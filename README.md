<<<<<<< HEAD
@ -1,62 +1,61 @@
=======
>>>>>>> parent of ed9af44 (V1 release)
# 🧠 NestShift OS: Neural Autonomous Residential Engine (NARE)

## 🎯 The Vision: An Autonomous "Pre-Frontal Cortex" for the Home

**NestShift OS** is a highly premium, local-first **Edge AI Operating System** that transforms a standard house into a learning, adaptive environment. Unlike traditional "Smart Home" systems (Home Assistant, Alexa) that rely on brittle "If/Then" rules, NestShift utilizes **Synthetic Neural Logic** to grow its own understanding of your life.

### ✨ Key Neural Features
- **🧠 NARE Core (Neural Autonomous Residential Engine)** - A Spiking Neural Network (LIF model) that learns usage patterns through synaptic plasticity.
- **⚡ Hebbian Learning** - "Neurons that fire together, wire together." The house learns your habits by observing manual overrides and sensor correlations.
- **🛡️ Πsafe (Safety First) Architecture** - An immutable inhibitory layer that prevents autonomous actions from violating physical safety or grid constraints.
- **🗣️ Explainable AI (XAI)** - Every action taken by the brain includes a "Neural Trace" explaining the logic and confidence level in plain English.
- **📺 Kiosk-Mode Interface** - A native, hardware-optimized UI that boots directly on the Hub's display for a premium "appliance" feel.
- **🔐 Local Sovereignty** - 100% of the cognitive processing happens on-device. Your life stays private.

## 🏗️ System Architecture: The Neural Stack

```
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│  Premium UI     │      │   Neural Brain  │      │   Πsafe Filter  │
│  (React Kiosk)  │◄────►│   (NARE / LIF)  │◄────►│   (Immutable)   │
└─────────────────┘      └─────────────────┘      └─────────────────┘
         ▲                        ▲                        ▲
         │                        │                        │
         ▼                        ▼                        ▼
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│   MQTT Broker   │◄────►│  Energy Agent   │◄────►│  System Agent   │
│   (Nervous Sys) │      │  (Agile Sync)   │      │  (Drift Detect) │
└─────────────────┘      └─────────────────┘      └─────────────────┘
```

## 🚀 Building the Production OS Image

NestShift is built as a custom Linux distribution using the industrial `pi-gen` toolchain.

### 1. Prerequisites
- A Linux environment (Ubuntu 24.04 recommended) with `qemu-user-static` and `binfmt-support`.
- At least 50GB of free space.

### 2. Build Commands
```bash
# 1. Setup the builder
git clone --depth 1 https://github.com/RPi-Distro/pi-gen.git
cd pi-gen && git checkout arm64

# 2. Link the NestShift Stage
ln -s ~/os-image/os/stage-nestshift stage-nestshift

# 3. Start the build
sudo CLEAN=1 ./build.sh
```

### 3. Output
The build produces a `nestshift-os.img` in the `deploy/` directory. This image is flashable to an SD card for Raspberry Pi 4/5 or bootable in QEMU for PC-based verification.

## 🔒 The Πsafe Safety Mandate
No command reaches the hardware without passing through the **Inhibitory Layer**.
- **Sensor Coherence:** Ignores "impossible" sensor spikes (e.g., >5°C temp jump in 1 min).
- **Critical Inhibition:** High-risk appliances (Ovens, Power Tools) are physically blocked from AI activation.
- **Grid Protection:** Prevents simultaneous activation of >3 high-power devices to protect local wiring.

## 🚀 How to Run NestShift OS

