const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

export async function mockGetHealth() {
  await delay(200);
  return { status: "ok", timestamp: new Date().toISOString(), services: { api: "mock", mqtt: "mock", influxdb: "mock" } };
}

export async function mockGetDevices() {
  await delay(300);
  return [
    { id: "dev_001", name: "Living Room Main", type: "light", state: "on", connection_type: "zigbee" },
    { id: "dev_002", name: "Kitchen Spots", type: "light", state: "off", connection_type: "zigbee" },
    { id: "dev_003", name: "HVAC Relay", type: "relay", state: "on", connection_type: "gpio", pin: 17 },
    { id: "dev_004", name: "Water Heater", type: "relay", state: "off", connection_type: "gpio", pin: 27 },
    { id: "dev_005", name: "Smart Lock", type: "sensor", state: "closed", connection_type: "wifi" },
    { id: "dev_006", name: "Exterior Lights", type: "light", state: "off", connection_type: "zigbee" },
  ];
}

export async function mockControlDevice(deviceId, action, params = {}) {
  await delay(150);
  return { status: "success", deviceId, action };
}

export async function mockGetEnergyUsage(period = '24h') {
  await delay(400);
  const readings = [];
  let kwh = 0.5;
  for (let i = 0; i < 24; i++) {
    kwh = Math.max(0.1, kwh + (Math.random() * 0.4 - 0.2));
    readings.push({ time: `${i}:00`, kwh: Number(kwh.toFixed(2)) });
  }
  return { cost_gbp: 1.45, savings_gbp: 0.82, kwh_total: 8.4, readings };
}

export async function mockGetCurrentTariff() {
  await delay(100);
  return { price_per_kwh: 15.5, is_peak: false, provider: "Octopus Mock" };
}

export async function mockGetAgentStatus() {
  await delay(200);
  return {
    automation: { status: "active", confidence: 0.92, last_action: "Disabled Water Heater" },
    energy: { status: "active", confidence: 0.88, mode: "balanced" },
    system: { status: "active", confidence: 1.0, health: "optimal" }
  };
}

export async function mockGetAutomations() {
  await delay(300);
  return [
    { id: "auto_1", name: "Morning Routine", type: "routine", active: true },
    { id: "auto_2", name: "Peak Savings", type: "energy", active: true }
  ];
}
