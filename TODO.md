# NestShift OS - TODO / Feature Gap List

## Status Legend
- 🔴 Not Started (0%)
- ⚠️ Started / Partial (1-50%)
- 🟡 Mostly Working (50-90%)
- ✅ Complete (90-100%)

---

## 🔴 CRITICAL - Core Infrastructure

### 1. Brain / NARE (Neural Autonomous Residential Engine)
**Status:** 🔴 0%

**What's missing:**
- [ ] Implement LIFNeuron class (Leaky Integrate-and-Fire)
  - Membrane potential, threshold, refractory period
  - Spike generation on threshold breach
- [ ] Implement Synapse class with STDP (Hebbian Learning)
  - Spike-timing dependent plasticity
  - Weight adjustment based on pre/post synaptic spikes
- [ ] Implement NeuralNetwork class
  - Connect sensor neurons → hidden layer → device output neurons
  - Forward pass for inference
  - Backward pass for learning
- [ ] Add Neural Trace / Explainability
  - Track which sensors triggered which action
  - Expose via API for dashboard visualization
- [ ] Integrate with MQTT
  - Subscribe to sensor topics
  - Publish actions to device topics

**Location:** `services/brain/main.py`

---

### 2. GPIO Service
**Status:** 🔴 5%

**What's missing:**
- [ ] MQTT subscriber for device commands
- [ ] GPIO pin mapping from config
- [ ] Read sensor states (temperature, motion, etc.)
- [ ] Write device states (relay on/off, PWM)
- [ ] Error handling for hardware failures
- [ ] Debounce logic for button/switch inputs
- [ ] Publish state changes back to MQTT

**Location:** `services/gpio/main.py`

---

### 3. Zigbee Service
**Status:** 🔴 0%

**What's missing:**
- [ ] Zigbee2MQTT integration script
- [ ] Device discovery and pairing
- [ ] MQTT bridge for zigbee2mqtt
- [ ] Device template mapping (Aqara, Danfoss, etc.)
- [ ] Availability tracking (online/offline)

**Location:** `services/zigbee/`

---

### 4. Device Registry
**Status:** 🔴 0%

**What's missing:**
- [ ] SQLite database schema for devices
  - `devices` table: id, name, type, room, capabilities
  - `device_state` table: device_id, state_json, updated_at
  - `device_capabilities` table: device_id, capability, config
- [ ] CRUD API endpoints
  - GET/POST/PUT/DELETE /devices
  - GET /devices/{id}/state
  - POST /devices/{id}/command
- [ ] MQTT integration for state sync
- [ ] Device discovery service

**Location:** `services/api/main.py` (new endpoints)

---

### 5. Central Config Management
**Status:** 🔴 0%

**What's missing:**
- [ ] Create `config/nestshift.yaml` schema
  - MQTT broker settings
  - InfluxDB connection
  - Device pin mappings
  - Agent enable/disable flags
  - Safety rule overrides
- [ ] Config loader service
- [ ] Hot reload capability
- [ ] Environment variable overrides
- [ ] Validation on startup

**Location:** New file `services/config/`

---

## 🟡 IMPORTANT - Functionality

### 6. Voice / Whisper Integration
**Status:** 🔴 0%

**What's missing:**
- [ ] Audio input capture (USB microphone)
- [ ] Whisper small model integration
- [ ] Intent extraction from transcript
- [ ] Text-to-speech for responses
- [ ] Hotword detection ("Hey NestShift")
- [ ] Audio buffer management

**Location:** New service `services/voice/`

---

### 7. Dashboard (OrbitAI)
**Status:** ⚠️ 20%

**What's missing:**
- [ ] Main dashboard page with energy charts
- [ ] Device control page
- [ ] Room/group management
- [ ] Automation rules UI
- [ ] Settings page (WiFi, users, agents)
- [ ] Onboarding wizard
- [ ] Real-time WebSocket updates
- [ ] Dark glassmorphism theme implementation

**Location:** `dashboard/src/`

---

### 8. MQTT Persistence
**Status:** 🔴 0%

**What's missing:**
- [ ] Retain last-known states on broker restart
- [ ] Will testament for device online/offline
- [ ] Birth/discovery messages
- [ ] Clean session handling

**Location:** `services/mqtt/`

---

### 9. Security Hardening
**Status:** ⚠️ 50%

**What's missing:**
- [ ] Change default admin/nestshift credentials
- [ ] Add rate limiting to API
- [ ] Input validation on all endpoints
- [ ] CSRF protection
- [ ] Secure WebSocket (WSS)
- [ ] TLS for MQTT (implement properly)
- [ ] Audit logging

**Location:** `services/api/main.py`

---

### 10. Logging & Observability
**Status:** ⚠️ 30%

**What's missing:**
- [ ] Structured logging (JSON format)
- [ ] Log levels per service
- [ ] Centralized log aggregation
- [ ] Trace ID for request correlation
- [ ] Log rotation

**Location:** All services

---

## 🟢 NICE TO HAVE

### 11. OTA Updates
- [ ] Update server / endpoint
- [ ] Delta update capability
- [ ] Rollback mechanism
- [ ] Integrity verification

### 12. Multi-User
- [ ] Household member accounts
- [ ] Guest accounts with limited access
- [ ] Role-based permissions
- [ ] Activity logs per user

### 13. Mobile App
- [ ] React Native or TWA
- [ ] Push notifications
- [ ] Widgets

### 14. External Integrations
- [ ] IFTTT webhooks
- [ ] Home Assistant bridge
- [ ] Google Home / Alexa skill

### 15. Advanced Energy
- [ ] LSTM/Transformer forecasting
- [ ] Solar generation prediction
- [ ] Battery storage optimization
- [ ] Carbon intensity integration

### 16. Scene Management
- [ ] "Movie mode", "Away mode", "Sleep mode"
- [ ] One-tap scene activation
- [ ] Scene scheduling

### 17. Notifications
- [ ] Push to mobile (FCM/APNs)
- [ ] Email alerts
- [ ] Telegram bot integration

---

## ✅ COMPLETE

- Energy Agent (90%)
- Automation Agent (75%)
- System Agent (80%)
- API (70%)
- Safety Filter (100%)
- MQTT Broker setup
- InfluxDB setup
- Tests for safety/drift/behaviour (40%)

---

## Recommended Build Order

1. **Device Registry** - Foundation for everything
2. **GPIO Service** - Actually control hardware
3. **Brain/NARE** - The flagship neural feature
4. **Dashboard** - Make it usable
5. **Config Management** - Clean up hardcoding
6. Everything else...

---

## Architecture Notes

```
┌─────────────────────────────────────────────────────────────┐
│                     OrbitAI Dashboard                       │
│                      (React + Vite)                        │
└─────────────────────────┬───────────────────────────────────┘
                          │ REST + WebSocket
┌─────────────────────────▼───────────────────────────────────┐
│                      FastAPI Gateway                        │
│              (Auth, Device Registry, Safety)               │
└─────────────────────────┬───────────────────────────────────┘
                          │ MQTT
┌─────────────────────────┴───────────────────────────────────┐
│                     MQTT Broker (Mosquitto)                 │
└──────┬──────────┬──────────┬──────────┬──────────┬────────┘
       │          │          │          │          │
   ┌───▼──┐  ┌───▼──┐  ┌───▼──┐  ┌───▼──┐  ┌───▼──┐
   │Brain │  │Energy│  │Auto  │  │System│  │GPIO  │
   │ NARE │  │Agent │  │Agent │  │Agent │  │      │
   └──┬───┘  └──┬───┘  └──┬───┘  └──┬───┘  └──┬───┘
      │         │         │         │         │
   ┌──▼────┬────▼─────────▼─────────▼─────────▼────────┐
   │              InfluxDB (Time Series)                 │
   └─────────────────────────────────────────────────────┘
```
