# 🧠 NestShift OS: Neural Autonomous Residential Engine (NARE)

## 🎯 Current Vision
NestShift has evolved into a **Synthetic Neural Core** for the modern home. We have successfully implemented the "Pre-Frontal Cortex" using spiking neural logic (LIF neurons) that learns organically through Hebbian mechanisms (STDP), moving away from rigid, manually programmed automation.

## 🛠️ Roadmap & Progress

### 1. Safety & Integrity (Πsafe) - **[COMPLETED]**
- [x] Immutable hardware safety constraints (HVAC 16-26°C).
- [x] Sensor coherence validation (Temperature jump protection).
- [x] Inhibitory feedback loops (Brain cannot trigger high-risk heating appliances).
- [x] Grid overload prevention (Simultaneous high-power device limits).

### 2. The Neural Brain (NARE) - **[COMPLETED]**
- [x] Leaky Integrate-and-Fire (LIF) neuron models for sensors and devices.
- [x] Hebbian Learning mechanism ("Neurons that fire together, wire together").
- [x] Synapse weighting for device-to-device correlations via MQTT.
- [x] Persistent neural state storage for long-term learning.

### 3. Edge Intelligence (Agents) - **[COMPLETED]**
- [x] **Energy Agent**: LightGBM-powered demand forecasting + Octopus Agile integration.
- [x] **Automation Agent**: Probabilistic behavior pattern recognition.
- [x] **System Agent**: Real-time resource monitoring and AI model drift detection.

### 4. Premium OS Experience - **[COMPLETED]**
- [x] **OrbitAI Dashboard**: High-end glassmorphism UI with neon aesthetics.
- [x] **Onboarding Wizard**: 5-step hardware mapping and pairing flow.
- [x] **OS Build Pipeline**: Custom `pi-gen` stage for Raspberry Pi deployment.

### 5. Future Frontiers - **[TODO]**
- [ ] **Home Assistant (HA) Discovery**: Sniff MQTT config messages to auto-map devices.
- [ ] **Advanced Neuroplasticity**: Dynamic synapse pruning and homeostatic scaling.
- [ ] **Local LLM Integration**: Voice-based "Neural Trace" explanations for AI decisions.

## 📜 Architectural Rules
1. **Safety First:** No AI command reaches the MQTT broker without passing through the Πsafe filter.
2. **Local Sovereignty:** 100% of the Brain and Agents run on-device. Zero cloud dependency for core logic.
3. **Neural Traceability:** Every autonomous action is logged with a "Neural Trace" explaining the synapse strength and sensor trigger.
4. **Premium Aesthetic:** UI must maintain the "OrbitAI" glassmorphism theme (`tokens.js`).

## 🚀 Execution Commands
- **Start UI:** `cd dashboard && npm run dev`
- **Start All Services:** `docker-compose -f dev/docker-compose.dev.yml up`
- **Run Simulator:** `python scripts/simulate_house.py` (Planned)
- **Run Tests:** `pytest tests/`
