import { create } from 'zustand';

/**
 * NestShift Store - manages all dashboard state
 * Includes brain data, sensors, energy, devices, safety, MQTT status
 */
export const useNestShiftStore = create((set, get) => ({
  // ============ Connection Status ============
  apiConnected: false,
  mqttConnected: false,
  mockMode: true, // Start in mock mode until connected
  simulationMode: false,

  // ============ Brain / NARE State ============
  brainStatus: {
    active_neurons: 0,
    strong_synapses: 0,
    autonomous_actions_today: 0,
    uptime_seconds: 0,
  },
  neuralTrace: [],
  synapses: [],

  // ============ Sensors ============
  sensors: {},

  // ============ Energy ============
  energy: {
    tariff: { price_per_kwh: 0, is_peak: false },
    schedule: [],
    savings_today: 0,
    readings: [],
  },

  // ============ Devices ============
  devices: [],
  deviceStates: {}, // { deviceId: { state, wattage, etc } }

  // ============ Safety ============
  safety: {
    hvac_current: 21,
    high_power_count: 0,
    inhibited_devices: [],
    recent_violations: [],
    overall_status: 'OFFLINE',
  },

  // ============ System ============
  startTime: Date.now(),
  lastUpdate: null,

  // ============ Actions - Connection ============
  setApiConnected: (connected) => set({ apiConnected: connected, mockMode: !connected }),
  setMqttConnected: (connected) => set({ mqttConnected: connected }),
  setSimulationMode: (mode) => set({ simulationMode: mode }),

  // ============ Actions - Brain ============
  setBrainStatus: (status) => set({ brainStatus: status, lastUpdate: Date.now() }),
  setNeuralTrace: (trace) => set({ neuralTrace: trace.slice(-20) }),
  setSynapses: (synapses) => set({ synapses: synapses.sort((a, b) => b.weight - a.weight) }),

  // ============ Actions - Sensors ============
  setSensors: (sensors) => set({ sensors, lastUpdate: Date.now() }),
  updateSensor: (topic, data) => set((state) => ({
    sensors: { ...state.sensors, [topic]: { ...data, lastUpdate: Date.now() } }
  })),

  // ============ Actions - Energy ============
  setEnergy: (energy) => set({ energy, lastUpdate: Date.now() }),
  updateTariff: (tariff) => set((state) => ({
    energy: { ...state.energy, tariff }
  })),

  // ============ Actions - Devices ============
  setDevices: (devices) => set({ devices, lastUpdate: Date.now() }),
  updateDeviceState: (name, state) => set((state) => ({
    deviceStates: { ...state.deviceStates, [name]: { ...state.deviceStates[name], ...state } }
  })),
  setDeviceState: (name, deviceState) => set((state) => ({
    deviceStates: { ...state.deviceStates, [name]: deviceState }
  })),

  // ============ Actions - Safety ============
  setSafety: (safety) => set({ safety, lastUpdate: Date.now() }),
  addViolation: (violation) => set((state) => ({
    safety: {
      ...state.safety,
      recent_violations: [violation, ...state.safety.recent_violations].slice(0, 10)
    }
  })),

  // ============ Helpers ============
  getUptime: () => {
    const { startTime } = get();
    return Math.floor((Date.now() - startTime) / 1000);
  },

  getStrongSynapses: () => {
    const { synapses } = get();
    return synapses.filter(s => s.weight >= 0.65);
  },

  getAutonomousDevices: () => {
    const { synapses, devices } = get();
    const autonomousTopics = synapses.filter(s => s.weight >= 0.65).map(s => s.post_topic);
    return devices.filter(d => autonomousTopics.some(t => t.includes(d.id) || t.includes(d.name)));
  },

  // ============ Bulk Update ============
  updateFromMQTT: (topic, data) => {
    const { updateSensor, setBrainStatus, setNeuralTrace, updateTariff } = get();
    
    if (topic.startsWith('nestshift/brain/status')) {
      setBrainStatus(data);
    } else if (topic.startsWith('nestshift/brain/trace')) {
      setNeuralTrace([data]);
    } else if (topic.startsWith('nestshift/sensors/')) {
      updateSensor(topic, data);
    } else if (topic.startsWith('nestshift/agents/energy/')) {
      updateTariff(data);
    }
  },
}));