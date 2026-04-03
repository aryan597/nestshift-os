# NestShift OS: Project Status & Hand-Off Summary

## 🎯 The Business Goal
NestShift is building a highly premium, local-first **Edge OS and Smart Home Hub hardware** for residential installation. 
Instead of generic cloud apps, the NestShift business model involves:
1. Conducting a house visit to determine layout and automation requirements.
2. Providing a quotation for the physical Hub and requisite smart hardware (relays, zigbee sensors).
3. Physically installing the hardware.
4. **Booting the OS.** The UI on the screen natively guides the user to connect to Wi-Fi, scan a QR code from the NestShift mobile app to pair their account, and maps physical GPIO pins to software routines.
The OS then autonomously utilizes Python edge models to run devices while prioritizing cost-savings (Energy Agent) and comfort (Automations).

---

## 💻 Current Development State (What We Did)
We have fully built the **Graphical User Interface** for the physical Hub's touchscreen using React + Vite + TailwindCSS. It was designed from scratch referencing a high-end "OrbitAI" aesthetic using absolute deep blacks, `Inter` typography, glassmorphism, and thin neon (`#00f0ff` Cyan / `#00e676` Green) glowing borders.

### Developed Components:
1. **The Installation OS Setup Wizard (`Onboarding.jsx`)**: A phone-like 5-step installer routing the user through Wi-Fi, Login, QR Pairing, and Hardware Mapping. 
2. **The Dashboard Grid (`Home.jsx`)**: A 3-column UI featuring Comfort sliders, an interactive glowing Focus Cost dial, and Live Energy Rhythm charts.
3. **The AI Router (`SmartSchedule.jsx`)**: A unique timeline view split between Energy Savings tasks and Daily Routines that visually proves to the user what the AI is automating in the background.
4. **Sub-screens (`Devices`, `Energy`, `Settings`)**: fully themed out with premium elements.

### The Mock Architecture:
Because the Python backend was turned off during our UI sprints, we rigged a complete **Demo Data System**:
- The dashboard is powered by `store/useNestShiftStore.js`.
- It attempts to fetch from `services/api.js`.
- In `api.js`, I placed a hardcoded toggle: `const USE_MOCK = true;`. This forces all requests to resolve through `services/mockApi.js`, which injects fake device states, simulated cost charts, and faux latency so the dashboard visually "works" independently of your database.

---

## ⚙️ How to Setup & Run
When you return tomorrow, you just need to do this:

**1. Start the UI Server:**
```bash
cd dashboard
npm install
npm run dev
```

**2. Previewing the Demo:**
Open `http://localhost:5173`. You will instantly be thrown into the OS Onboarding Wizard. Walk through the steps, hit the "Simulate App Scan Success" on the QR code, map your hardware, and wait 5 seconds. The mock data will explode into life across the dash.

---

## 📥 What Needs to Happen Next
When you are ready to transition from UI-design back into full-stack integrations:
1. **Turn off Mock Mode:** Go into `dashboard/src/services/api.js` and switch `const USE_MOCK = false;`.
2. **Start Backend Services:** Boot up your FastAPI (`services/api/main.py`), Mosquitto MQTT, and InfluxDB servers. Ensure your backend handles the `/devices` and `/energy/usage` routes seamlessly.
3. **Hardware Kiosk:** Move the `os-image` codebase onto a Raspberry Pi 5 / Jetson Nano. Flash the Debian OS and write a systemd script that launches Chromium in `--kiosk` mode pointing to `localhost:5173` on boot.
