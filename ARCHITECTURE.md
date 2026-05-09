# NestShift OS — Technical Architecture

This document describes the end-to-end AI architecture of NestShift OS from an ML systems engineering perspective. The design philosophy mirrors enterprise-grade MLOps patterns — observable, bounded, drift-aware — applied to the unique constraints of edge home automation.

---

## 1. End-to-End Data Flow

The system implements a streaming pipeline from physical sensors to actuator commands, with each stage decoupled via MQTT message bus.

### 1.1 Data Ingestion

```
[Sensors] → MQTT → [InfluxDB] → [Feature Engineering]
```

- **Sources**: Zigbee devices (TRVs, relays, motion sensors), CT clamp NILM, Shelly 1PM power readings
- **Protocol**: MQTT 3.1.1 over TCP (port 1883, TLS on 8883 for production)
- **Topic Schema**:
  - Device state: `nestshift/devices/{device_id}/state`
  - Sensor readings: `nestshift/sensors/{sensor_id}/reading`
  - Agent actions: `nestshift/agents/{agent}/action`

**Feature Engineering Layer**: Every 60 seconds, raw sensor readings are aggregated into feature vectors:

| Feature | Source | Aggregation |
|---------|--------|-------------|
| `hour_of_day` | Timestamp | Direct |
| `day_of_week` | Timestamp | Direct |
| `temperature_avg_1h` | TRV sensors | Rolling mean |
| `occupancy_count` | Motion sensors | Sum (active in last 30 min) |
| `kwh_consumption_1h` | CT clamp | Delta sum |
| `tariff_price_current` | Octopus API | Lookup |

### 1.2 Decision Pipeline

```
[Feature Vector] → [RL Agent] → [Rule Engine] → [Safety Filter] → [Device Command]
```

1. **BehaviourModel** (automation-agent): Predicts next action based on learned patterns
2. **RuleEngine**: Enforces domain-specific constraints (e.g., "don't disable security devices when occupied")
3. **SafetyFilter (Πsafe)**: Immutable hardware bounds — no AI can override

### 1.3 Actuation

Device commands are published to MQTT topics consumed by:
- Zigbee2MQTT for Zigbee devices
- Shelly HTTP API for Shelly relays
- GPIO service for direct Raspberry Pi hardware

---

## 2. Local Inference Pipeline

All AI inference executes on-device. No data leaves the Raspberry Pi 5.

### 2.1 Constraints

| Constraint | Implication |
|------------|-------------|
| 4GB RAM | Models must be < 500MB; batch inference not viable |
| ARM64 CPU | ONNX runtime with NEON optimization; no CUDA |
| Power budget | Inference < 5W sustained |
| Latency requirement | < 2s end-to-end from sensor to action |

### 2.2 Model Serving Architecture

```
┌─────────────────────────────────────────────┐
│              asyncio event loop              │
├─────────────────────────────────────────────┤
│  aiomqtt (async consumer)  →  Feature prep  │
│                                          ↓  │
│  BehaviourModel.predict() →  Action candidate│
│                                          ↓  │
│  RuleEngine.validate()   →  Rule-checked    │
│                                          ↓  │
│  SafetyFilter.validate() →  Safety-bound    │
│                                          ↓  │
│  Publish to MQTT → Device actuation          │
└─────────────────────────────────────────────┘
```

**Model Formats**:
- BehaviourModel: In-memory Python object (numpy dict), not a serialized model
- DemandForecaster: LightGBM `.pkl` file, loaded on-demand (~50MB)

### 2.3 Why Not Cloud?

1. **Latency**: Round-trip to cloud API adds 200-500ms minimum; local inference is < 50ms
2. **Availability**: Home network may be down; local operation must persist
3. **Privacy**: No sensor data in third-party data centers — regulatory alignment with GDPR Article 44
4. **Cost**: Eliminates per-request API fees; fixed hardware cost amortized over device lifetime

---

## 3. RL Agent Design

The automation-agent implements a simplified reinforcement learning agent that learns household patterns without the overhead of full RL frameworks.

### 3.1 Behaviour Model Architecture

```python
class BehaviourModel:
    # State: patterns[hour][device_id][action] -> count
    # Learned from: device state changes and user actions
    
    def predict_next_action(current_hour, device_states):
        if confidence < 0.3:  # Insufficient training data
            return None  # Defer to rules
        
        # Greedy selection: highest probability action > 75%
        for device_id, actions in patterns[current_hour].items():
            for action, count in actions.items():
                prob = count / total_actions
                if prob > 0.75:
                    return { device_id, action, confidence: prob }
```

### 3.2 Learning Mechanism

- **Observations**: Every device state change is recorded as `(timestamp, device_id, action)`
- **Feature extraction**: Actions aggregated by hour-of-day — captures circadian rhythms
- **Learning rate**: `alpha = confidence * 0.8` when confidence >= 0.3, else 0 (no learning)
- **Convergence**: Requires ~2000 events (~3 weeks of typical household activity)

### 3.3 Why Not Full RL?

| Aspect | Full RL (PPO/SAC) | NestShift Behaviour Model |
|--------|-------------------|----------------------------|
| Sample efficiency | 10⁵-10⁶ episodes | 2000 events |
| Computational cost | GPU recommended | CPU only |
| Explosion risk | Unbounded actions | Hourly bucketing |
| Interpretability | Black box | Explicit pattern counts |
| Safety verification | Difficult | Trivial (check patterns) |

The behaviour model captures the core insight of RL — learning from interaction — without the deployment complexity. For a bounded smart home environment, this pragmatic approach outperforms over-engineered alternatives.

### 3.4 Drift Detection

The system-agent monitors prediction error rates:

```python
class DriftDetector:
    # Records prediction error per agent
    # Triggers retraining when:
    #   - energy: mean_error > 0.15
    #   - automation: mean_error > 0.25
    
    def check_drift(agent):
        # Rolling window of last 100 predictions
        mean_error = sum(errors[-100:]) / 100
        return mean_error > threshold[agent]
```

When drift is detected, the energy-agent retrains its LightGBM demand forecaster on the last 7 days of InfluxDB history.

---

## 4. Voice Command Processing

Voice commands follow a structured extraction pipeline:

```
[Audio Input] → [Whisper Small] → [Intent Parser] → [Action Dispatch]
```

### 4.1 Whisper Small

- **Model**: `tiny` or `base` (39M / 74M parameters)
- **Runtime**: `whisper.cpp` on ARM64, ~500ms per command
- **Output**: Raw transcription text

### 4.2 Intent Extraction

Transcribed text is parsed against a schema:

| Command Template | Extracted Action |
|-----------------|------------------|
| "turn on the living room lights" | `{ device_id: "living_room_lights", action: "turn_on" }` |
| "set heating to 21 degrees" | `{ device_id: "hvac", action: "set_temperature", params: { temperature: 21 } }` |
| "turn off the kettle" | `{ device_id: "kettle", action: "turn_off" }` |

**Current Implementation**: Simple keyword matching. Future versions will use a small local LLM (e.g., TinyLlama 1.1B) for intent disambiguation.

### 4.3 Safety Filter

Before any voice command reaches device actuation:

```python
def validate_action(action, system_state):
    # HVAC bounds enforced
    if action.type == "set_temperature":
        clamp(action.params.temperature, 16, 26)
    
    # High-power device limit (3 concurrent max)
    if action.type == "turn_on":
        if active_high_power >= 3:
            raise SafetyViolation("max_simultaneous_high_power")
```

---

## 5. Observability and MLOps

The system implements enterprise MLOps practices adapted for edge deployment:

### 5.1 Metrics Pipeline

```
[Agent decisions] → InfluxDB → [Grafana dashboard]
       ↓
  MQTT health topics → API gateway → /agents/status
```

### 5.2 Model Lifecycle

| Stage | Trigger | Action |
|-------|---------|--------|
| Training | Drift detected or manual | Retrain LightGBM on InfluxDB history |
| Deployment | Model file updated | Atomic swap (`mv new.pkl old.pkl`) |
| Monitoring | Every 60s | SystemAgent checks model freshness |
| Retirement | Age > 30 days | Archive to cold storage, notify |

### 5.3 Alerting

- **Drift alert**: `/nestshift/agents/system/drift_alert` — triggers retraining
- **Health failure**: `/nestshift/agents/system/health` — missing > 120s = degraded
- **Safety violation**: Logged with `level: "warning"` — inspectable via InfluxDB

---

## 6. Security Considerations

### 6.1 Authentication

- JWT tokens with 24-hour expiry
- Passwords hashed with bcrypt (cost factor 12)
- API endpoints require `Authorization: Bearer <token>`

### 6.2 Safety Filter (Πsafe)

The safety filter is **immutable** — not configurable via API, not overridable by any AI agent. It enforces:

| Rule | Value |
|------|-------|
| HVAC temperature bounds | 16°C ≤ T ≤ 26°C |
| Max concurrent high-power devices | 3 |
| Max single device wattage | 3000W |
| High-power threshold | 1000W |

---

## 7. Future Work

- **Hebbian learning**: Implement spike-timing-dependent plasticity (STDP) for unsupervised sensor correlation
- **Neural network brain**: Replace behaviour model with a small spiking neural network (snnTorch on ARM64)
- **Local LLM**: TinyLlama 1.1B for complex intent parsing without cloud

---

*This architecture is designed for ML engineers evaluating edge AI systems. The same principles — observable pipelines, bounded models, drift awareness — apply whether you're deploying home automation or industrial predictive maintenance.*