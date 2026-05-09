import { create } from 'zustand';

export const useNestShiftStore = create((set, get) => ({
  // Connection
  apiConnected: false,
  mqttConnected: false,

  // Devices
  devices: [],

  // Energy
  energyUsage: null,
  currentTariff: null,

  // Agents
  agentStatus: null,

  // Preferences
  comfortCostBias: 0.5,

  // Actions
  setDevices: (devices) => set({ devices }),
  updateDeviceState: (deviceId, state) => set((prev) => ({
    devices: prev.devices.map(d => d.id === deviceId ? { ...d, ...state } : d)
  })),
  setEnergyUsage: (energyUsage) => set({ energyUsage }),
  setCurrentTariff: (currentTariff) => set({ currentTariff }),
  setAgentStatus: (agentStatus) => set({ agentStatus }),
  setComfortCostBias: (comfortCostBias) => set({ comfortCostBias }),
  setApiConnected: (apiConnected) => set({ apiConnected }),
  setMqttConnected: (mqttConnected) => set({ mqttConnected }),
}));