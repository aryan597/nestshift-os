# NestShift OS

> A local-first, edge AI operating system for the home. Learns your patterns. Runs entirely offline. No cloud, no subscriptions, no surveillance.

<!-- TODO: Add hero screenshot here — 1200x600px, dark UI with neon accents -->
<!-- Place image at: docs/screenshots/dashboard-hero.png -->

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](./LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Node 18+](https://img.shields.io/badge/node-18+-green.svg)](https://nodejs.org/)

---

## What is it?

**NestShift OS** turns a Raspberry Pi into a truly autonomous home brain. Unlike smart home hubs that rely on rigid "if-this-then-that" rules, NestShift uses a neural core that learns from your behavior and anticipates what you need — all without sending a single byte to the cloud.

It runs every AI model locally: voice recognition, energy forecasting, behavioral learning, and safety filtering. Your data stays in your house. Period.

---

## Features

| Feature | What it does |
|---|---|
| 🧠 **Neural Brain (NARE)** | Spiking neural network with Hebbian learning that forms synapses between your sensors and devices. The more you use it, the smarter it gets. |
| ⚡ **Energy Optimisation** | LightGBM forecasts your demand and shifts high-power loads to the cheapest tariff windows — 9–13% savings demonstrated. |
| 🔒 **Pi-safe Hardware Filter** | Immutable safety constraints. No AI, voice command, or bug can override hard limits on temperature, wattage, or high-power concurrency. |
| 🎙️ **Local Voice Control** | Whisper Small runs on-device. Speak naturally. No cloud ASR, no wake-word phoning home. |
| 🖥️ **OrbitAI Dashboard** | Glassmorphism React UI with real-time telemetry, neural traces, and energy rhythm charts. Deep blacks, neon cyan accents, zero clutter. |
| 📊 **Drift-aware MLOps** | SystemAgent monitors prediction quality and triggers automatic retraining when your habits change. |

<!-- TODO: Add 3–4 screenshot thumbnails here -->
<!-- docs/screenshots/brain-panel.png — NARE neuron activity -->
<!-- docs/screenshots/energy-panel.png — Live cost & savings chart -->
<!-- docs/screenshots/safety-panel.png — Pi-safe constraint monitor -->

---

## Quick Start

### Preview the Dashboard (mock mode)

```bash
git clone https://github.com/aryan597/nestshift-os.git
cd nestshift-os/dashboard
npm install
npm run dev
# Open http://localhost:5173
```

### Run a single service locally

```bash
cd services/brain
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

### Full install on Raspberry Pi 4/5

```bash
curl -sSL https://raw.githubusercontent.com/aryan597/nestshift-os/main/scripts/install.sh | bash
```

> **Note:** Full stack deployment requires Mosquitto MQTT, InfluxDB, and Zigbee2MQTT. See [ARCHITECTURE.md](./ARCHITECTURE.md) for detailed service topology.

---

## System Architecture

```
┌─────────────────┐      ┌──────────────┐      ┌─────────────────┐
│  OrbitAI Dashboard │◄────►│  FastAPI      │◄────►│  Mosquitto MQTT │
│   (React + Vite)   │      │   Gateway     │      │    (TLS)        │
└─────────────────┘      └──────────────┘      └─────────────────┘
                                                        │
       ┌──────────────┬──────────────┬─────────────────┼─────────────────┐
       ▼              ▼              ▼                 ▼                 ▼
┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐
│   Brain    │ │  Energy    │ │ Automation │ │   System   │ │   Zigbee   │
│  (NARE)    │ │   Agent    │ │   Agent    │ │   Agent    │ │  / GPIO    │
└────────────┘ └────────────┘ └────────────┘ └────────────┘ └────────────┘
```

- **NARE Brain** — LIF spiking neurons + STDP learning
- **Energy Agent** — LightGBM demand forecasting + Octopus Agile tariff arbitrage
- **Automation Agent** — Hourly behavior pattern mining with confidence scoring
- **System Agent** — Drift detection, model freshness, hardware health
- **Pi-safe** — Immutable safety filter between all agents and physical hardware

Read the full architecture: [ARCHITECTURE.md](./ARCHITECTURE.md)

---

## Hardware Stack

| Component | Purpose |
|---|---|
| **Raspberry Pi 5** (4GB+) | Primary compute |
| **Shelly 1PM** | WiFi relays + power monitoring |
| **Danfoss Ally TRV** | Zigbee radiator valves |
| **Aqara Sensors** | Temp, humidity, motion, door/window |
| **CT Clamp** | Whole-home energy monitoring (NILM) |

---

## Project Structure

```
nestshift-os/
├── dashboard/          # React + Vite OrbitAI UI
├── services/           # Microservices (FastAPI + asyncio)
│   ├── api/            # REST gateway & auth
│   ├── brain/          # NARE neural core
│   ├── energy-agent/   # Demand forecasting & tariff logic
│   ├── automation-agent/  # Behavioral pattern learning
│   ├── system-agent/   # Drift detection & monitoring
│   ├── gpio/           # Raspberry Pi hardware interface
│   └── zigbee/         # Zigbee2MQTT bridge
├── board/              # Buildroot OS overlay
├── config/             # Hardware & neural config
├── scripts/            # Installation & flashing helpers
├── simulation/         # Digital twin evaluation framework
├── tests/              # Safety & logic test suite
└── systemd/            # Production service units
```

---

## Security & Privacy

- **Local-first**: 100% of inference and data stays on your Pi. No cloud APIs, no telemetry, no outbound analytics.
- **Encrypted transport**: All MQTT traffic uses TLS. JWT auth on REST endpoints.
- **Immutable safety**: Pi-safe constraints are hardcoded. No prompt injection, voice spoof, or model drift can disable them.
- **Camera-free**: Optional WiFi CSI sensing (RuView) for through-wall occupancy without cameras or wearables.

---

## Research

NestShift OS is the product of active research in edge AI and residential energy optimisation.

- **Energy optimisation**: 9–13% cost reduction across dynamic tariffs (see [RESEARCH.md](./RESEARCH.md))
- **Solar self-consumption**: 12–38% savings for solar-equipped households
- **Digital twin**: Reproducible Monte Carlo simulation framework included in `simulation/`

Read the full research background: [RESEARCH.md](./RESEARCH.md)

---

## Contributing

NestShift sits at the intersection of neuroscience, embedded systems, and home automation. We're actively looking for contributors in:

- Spiking neural networks (snnTorch / Norse)
- Embedded ML & ONNX Runtime on ARM64
- Zigbee / Matter device integrations
- Safety-critical systems verification

Open an issue or draft PR. All contributions are reviewed through the Pi-safe lens: *safety first, features second.*

---

*Built by NestShift Ltd for a sustainable, intelligent future.*
