const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Health
export async function getHealth() {
  const response = await fetch(`${BASE_URL}/health`);
  if (!response.ok) throw new Error('Failed to get health');
  return response.json();
}

// Devices
export async function getDevices() {
  const response = await fetch(`${BASE_URL}/devices`);
  if (!response.ok) throw new Error('Failed to get devices');
  return response.json();
}

export async function controlDevice(deviceId, action, params = {}) {
  const response = await fetch(`${BASE_URL}/devices/${deviceId}/control`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ action, ...params }),
  });
  if (!response.ok) throw new Error('Failed to control device');
  return response.json();
}

// Energy
export async function getEnergyUsage(period = '24h') {
  const response = await fetch(`${BASE_URL}/energy/usage?period=${period}`);
  if (!response.ok) throw new Error('Failed to get energy usage');
  return response.json();
}

export async function getCurrentTariff() {
  const response = await fetch(`${BASE_URL}/energy/tariff/current`);
  if (!response.ok) throw new Error('Failed to get current tariff');
  return response.json();
}

// Agents
export async function getAgentStatus() {
  const response = await fetch(`${BASE_URL}/agents/status`);
  if (!response.ok) throw new Error('Failed to get agent status');
  return response.json();
}

// Automations
export async function getAutomations() {
  // Stub for now
  return [];
}

export async function toggleAutomation(id, enabled) {
  // Stub for now
}

// AI Command (existing brain endpoint)
export async function sendVoiceCommand(text) {
  const response = await fetch(`${BASE_URL}/ai/command`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ command: text }),
  });
  if (!response.ok) throw new Error('Failed to send voice command');
  return response.json();
}