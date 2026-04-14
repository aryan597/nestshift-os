# 🧠 NestShift OS: Neural Autonomous Residential Engine (NARE)

## 🎯 Current Vision
NestShift is evolving from a standard smart home hub into a **Synthetic Neural Core**. We are building a "Pre-Frontal Cortex" for the home that learns organically through spiking neural logic rather than manual programming.

## 🛠️ Roadmap & Progress

### 1. Safety & Integrity (Πsafe) - **[IN PROGRESS]**
- [ ] Immutable hardware safety constraints.
- [ ] Sensor coherence validation (ignore "impossible" jumps).
- [ ] Inhibitory feedback loops to "punish" unsafe neural paths.

### 2. The Neural Brain (NARE) - **[TODO]**
- [ ] Implement Leaky Integrate-and-Fire (LIF) neuron models.
- [ ] Hebbian Learning mechanism ("Neurons that fire together, wire together").
- [ ] Synapse weighting for device-to-device correlations.

### 3. Home Assistant (HA) Integration - **[TODO]**
- [ ] HA Discovery Bridge (Sniff MQTT config messages).
- [ ] "Neural Extension" mode for existing HA users.

### 4. OS & Hardware Optimization - **[IN PROGRESS]**
- [ ] Local Kiosk Mode (HDMI display auto-boot).
- [ ] InfluxDB data retention & SD card protection.
- [ ] Read-only root filesystem for power-loss resilience.

## 📜 Architectural Rules
1. **Safety First:** No AI command reaches the MQTT broker without passing through the Πsafe filter.
2. **Local Sovereignty:** 100% of the Brain runs on-device. No cloud dependencies for core logic.
3. **Explainability:** Every autonomous action must have a "Neural Trace" explaining *why* it happened.
4. **Premium Aesthetic:** UI must maintain the "OrbitAI" glassmorphism theme (`tokens.js`).

## 🚀 Execution Commands
- **Start UI:** `cd dashboard && npm run dev`
- **Start Backend:** `services/api/venv/bin/python services/api/main.py`
- **Run Simulator:** `python scripts/simulate_house.py` (Planned)
