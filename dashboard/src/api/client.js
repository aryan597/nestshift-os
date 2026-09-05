const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * NestShift API Client
 * All device commands go through Πsafe via the REST API
 */

// Generic request wrapper
async function request(endpoint, options = {}) {
  try {
    const response = await fetch(`${BASE_URL}${endpoint}`, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    });
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.message || `HTTP ${response.status}`);
    }
    
    return response.json();
  } catch (error) {
    console.error(`[API] ${options.method || 'GET'} ${endpoint} failed:`, error.message);
    throw error;
  }
}

// ============ Health ============
export async function getHealth() {
  return request('/health');
}

// ============ Brain / NARE ============
export async function getBrainStatus() {
  return request('/api/brain/status');
}

export async function getSynapses() {
  return request('/api/brain/synapses');
}

export async function getNeuralTrace(limit = 20) {
  return request(`/api/brain/trace?limit=${limit}`);
}

// ============ Devices ============
export async function getDevices() {
  return request('/api/devices');
}

export async function getDevice(name) {
  return request(`/api/devices/${name}`);
}

export async function setDevice(name, payload) {
  // Sends to nestshift/devices/{name}/set → goes through Πsafe
  return request(`/api/devices/${name}/set`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

// ============ Energy ============
export async function getEnergyTariff() {
  return request('/api/energy/tariff');
}

export async function getEnergySchedule() {
  return request('/api/energy/schedule');
}

export async function getEnergyUsage(period = '24h') {
  return request(`/api/energy/usage?period=${period}`);
}

// ============ Safety ============
export async function getSafetyStatus() {
  return request('/api/safety/status');
}

export async function getSafetyViolations(limit = 10) {
  return request(`/api/safety/violations?limit=${limit}`);
}

// ============ GPIO / Zigbee ============
export async function getGpioStatus() {
  return request('/api/gpio/status');
}

export async function getZigbeeStatus() {
  return request('/api/zigbee/status');
}

// ============ Fallback for demo ============
import { getMockData } from '../hooks/useMQTTClient';

export function createAPIClient() {
  let apiConnected = false;
  let mockMode = false;

  async function checkConnection() {
    try {
      await getHealth();
      apiConnected = true;
      mockMode = false;
      return true;
    } catch {
      apiConnected = false;
      mockMode = true;
      console.warn('[API] Backend unavailable, using mock data');
      return false;
    }
  }

  // Wrapped methods that fall back to mock
  async function getBrainData() {
    if (mockMode) return getMockData().brain;
    try {
      return await getBrainStatus();
    } catch {
      return getMockData().brain;
    }
  }

  async function getSensorData() {
    if (mockMode) return getMockData().sensors;
    try {
      return await getBrainStatus(); // Or dedicated sensor endpoint
    } catch {
      return getMockData().sensors;
    }
  }

  async function getDevicesData() {
    if (mockMode) return getMockData().devices;
    try {
      return await getDevices();
    } catch {
      return getMockData().devices;
    }
  }

  async function getEnergyData() {
    if (mockMode) return getMockData().energy;
    try {
      const [tariff, schedule, usage] = await Promise.all([
        getEnergyTariff(),
        getEnergySchedule(),
        getEnergyUsage(),
      ]);
      return { tariff, schedule, ...usage };
    } catch {
      return getMockData().energy;
    }
  }

  async function getSafetyData() {
    if (mockMode) return getMockData().safety;
    try {
      return await getSafetyStatus();
    } catch {
      return getMockData().safety;
    }
  }

  async function controlDevice(name, payload) {
    if (mockMode) {
      console.warn('[API] Mock mode: device control simulated');
      return { success: true, mock: true };
    }
    return setDevice(name, payload);
  }

  return {
    checkConnection,
    isConnected: () => apiConnected,
    isMockMode: () => mockMode,
    getBrainData,
    getSensorData,
    getDevicesData,
    getEnergyData,
    getSafetyData,
    controlDevice,
  };
}

// Export singleton
export const nestshiftApi = createAPIClient();