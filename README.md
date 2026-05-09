# NestShift OS

A privacy-first, edge AI home automation and energy management platform. NestShift OS runs entirely locally on Raspberry Pi 5 with no cloud dependency — your home data never leaves your premises.

## Overview

NestShift OS combines real-time sensor data, reinforcement learning automation agents, and intelligent energy management into a unified edge AI system. The platform orchestrates Zigbee devices, MQTT-based sensors, and local AI services to provide comfortable, cost-optimized home automation.

### Core AI Stack

- **Python AI Services** — Asynchronous microservices using asyncio and aiomqtt
- **FastAPI REST API** — Local API gateway with JWT authentication and safety filtering
- **Whisper Small ASR** — On-device voice command processing
- **RL Automation Agent** — Behaviour model learning household patterns
- **Zigbee2MQTT** — Integration with Zigbee devices (TRVs, sensors, relays)
- **Mosquitto MQTT** — Message broker for all sensor and agent communication
- **Node-RED** — Visual flow-based programming for automation rules
- **Octopus Agile Tariff Integration** — Real-time energy pricing optimization

## AI Architecture

NestShift OS implements an LLM-orchestrated pipeline architecture — the same engineering principles used in enterprise AI systems (RAG pipelines, agentic systems, structured extraction), applied to home automation instead of document processing.

### Pipeline Stages

1. **Sensor Data Ingestion Layer**
   - MQTT subscription to all device topics (`nestshift/devices/#`, `nestshift/sensors/#`)
   - Real-time time-series storage in InfluxDB
   - Data normalization and feature engineering at 1-minute resolution

2. **Semantic Understanding and Intent Extraction**
   - Voice commands processed through Whisper Small for on-device ASR
   - Contextual intent extraction combining recent sensor state + user history
   - Safety filter validation before any action reaches the decision engine

3. **Local AI Decision Engine**
   - **RL Agent**: BehaviourModel learns household patterns by recording device actions per hour-of-day. Confidence threshold determines when to act autonomously.
   - **Rule Fusion**: Safety filter (`Πsafe`) provides immutable hardware constraints that no AI can bypass — HVAC temperature bounds, concurrent high-power device limits
   - Drift detection via SystemAgent monitors prediction error rates and triggers model retraining

4. **Structured Output Layer**
   - Device commands serialized as validated JSON
   - Action schemas: `{ device_id, action, params, rule_validated, safety_clamped }`
   - Published to MQTT for device execution

5. **Monitoring and Observability**
   - All agent decisions logged to InfluxDB for downstream analytics
   - Health topics published every 60 seconds per agent
   - SystemAgent aggregates drift status and model freshness

## Hardware Stack

- **Raspberry Pi 5** — Primary compute platform (4GB+ recommended)
- **Shelly 1PM** — WiFi relays with power monitoring
- **Danfoss Ally Zigbee TRVs** — Radiator temperature control
- **Aqara Sensors** — Temperature, humidity, motion, door/window
- **CT Clamp** — Non-invasive load monitoring for NILM (Non-Intrusive Load Monitoring)

## Services

| Service | Purpose |
|---------|---------|
| `api` | FastAPI REST gateway with auth, safety filter, energy/tariff endpoints |
| `automation-agent` | RL-based behaviour learning, pattern prediction, rule validation |
| `energy-agent` | Octopus Agile tariff fetching, demand forecasting (LightGBM), load scheduling |
| `system-agent` | Resource monitoring, drift detection, model lifecycle management |
| `brain` | MQTT subscriber for future neural network processing |
| `gpio` | Raspberry Pi GPIO operations |
| `zigbee` | Zigbee2MQTT configuration |
| `mqtt` | Mosquitto broker configuration |
| `influxdb` | Time-series database for sensor data and metrics |

## Setup

### Prerequisites

- Raspberry Pi 5 with Raspberry Pi OS (64-bit)
- Docker and Docker Compose
- MQTT broker (Mosquitto)
- InfluxDB for time-series storage

### Quick Start

```bash
# Clone the repository
git clone https://github.com/yourorg/nestshift-os.git
cd nestshift-os

# Copy environment template
cp .env.example .env
# Edit .env with your configuration

# Start all services
docker-compose up -d

# Check service health
curl http://localhost:8000/health
```

### Configuration

All configuration is managed via environment variables in `.env`. Key variables:

- `MQTT_HOST`, `MQTT_PORT` — MQTT broker connection
- `INFLUXDB_URL`, `INFLUXDB_TOKEN` — InfluxDB connection
- `JWT_SECRET` — API authentication secret
- `OCTOPUS_API_KEY` — For tariff fetching (optional)

## Project Structure

```
nestshift-github-ready/
├── services/
│   ├── api/              # FastAPI REST service
│   ├── automation-agent/ # RL behaviour learning agent
│   ├── energy-agent/     # Tariff and forecasting agent
│   ├── system-agent/     # Monitoring and drift detection
│   ├── brain/            # Future neural network processing
│   ├── gpio/             # Raspberry Pi GPIO service
│   ├── zigbee/           # Zigbee2MQTT config
│   ├── mqtt/             # Mosquitto broker config
│   └── influxdb/         # InfluxDB initialization
├── config/
│   ├── gpio/             # GPIO pin configuration
│   └── nodered/          # Node-RED settings
├── systemd/              # Systemd service units
├── tests/                # Pytest test suite
├── dashboard/            # React dashboard frontend
├── board/                # Buildroot overlay for custom OS image
└── scripts/              # Installation and setup scripts
```

## Contributing

Contributions are welcome. Please ensure:

- All Python code passes linting (`ruff check`)
- Tests pass before submitting PRs
- New AI/ML features include drift detection and observability hooks

## License

MIT License — See LICENSE file for details.

---

Built with privacy-first principles. All inference runs locally — your home, your data, your AI.