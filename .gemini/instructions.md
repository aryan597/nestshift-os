# 🤖 AI Agent Context Initialization (NestShift OS)

**Project Identifier:** NestShift OS (Edge AI Smart Home Hub)
**Current Stage:** Frontend UI Built (React/Vite) & Fleshed out with mock data. Python Backend (FastAPI) disabled.

## Core Rules for Working in this Project
1. **No Destructive Architectural Changes:** The backend runs on a highly specific Pi-gen hardware stack (`os/BUILD.md`) targeting Raspberry Pi / Jetson Nano. Do not refactor core microservice boundaries (FastAPI -> MQTT -> InfluxDB) without extreme deliberation.
2. **Design Language:** All React UI components live in `dashboard/src/`. They must adhere globally to the `tokens.js` configuration (Deep Orbit dark `#080b12`, Neon Cyan `#00f0ff`, Neon Green `#00e676`, and `Inter` font). Do not introduce basic layouts like Material UI.
3. **Mock State Toggle:** When editing the frontend, check `dashboard/src/services/api.js`. `USE_MOCK = true` is currently set, meaning data is resolving through `mockApi.js`. If you need to debug live InfluxDB endpoints, flip this to `false`.
4. **Onboarding Context:** We are an OS. The main app (`App.jsx`) is guarded by an `isOnboarded` boolean in the Zustand store. If `false`, the app locks the screen to the `Onboarding.jsx` wizard. 

*When resuming an AI conversation, read `NESTSHIFT_PROJECT_SUMMARY.md` first.*
