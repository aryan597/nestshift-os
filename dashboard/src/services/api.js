import * as mockApi from './mockApi';

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const USE_MOCK = true; // Hardcoded to true for demo/onboarding sequence

// Health
export async function getHealth() {
  if (USE_MOCK) return mockApi.mockGetHealth();
  const response = await fetch(`${BASE_URL}/health`);
  if (!response.ok) throw new Error('Failed to get health');
  return response.json();
}

// Devices
export async function getDevices() {
  if (USE_MOCK) return mockApi.mockGetDevices();
  const response = await fetch(`${BASE_URL}/devices`);
  if (!response.ok) throw new Error('Failed to get devices');
  return response.json();
}

export async function controlDevice(deviceId, action, params = {}) {
  if (USE_MOCK) return mockApi.mockControlDevice(deviceId, action, params);
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
  if (USE_MOCK) return mockApi.mockGetEnergyUsage(period);
  const response = await fetch(`${BASE_URL}/energy/usage?period=${period}`);
  if (!response.ok) throw new Error('Failed to get energy usage');
  return response.json();
}

export async function getCurrentTariff() {
  if (USE_MOCK) return mockApi.mockGetCurrentTariff();
  const response = await fetch(`${BASE_URL}/energy/tariff/current`);
  if (!response.ok) throw new Error('Failed to get current tariff');
  return response.json();
}

// Agents
export async function getAgentStatus() {
  if (USE_MOCK) return mockApi.mockGetAgentStatus();
  const response = await fetch(`${BASE_URL}/agents/status`);
  if (!response.ok) throw new Error('Failed to get agent status');
  return response.json();
}

// Automations
export async function getAutomations() {
  if (USE_MOCK) return mockApi.mockGetAutomations();
  return [];
}

export async function toggleAutomation(id, enabled) {
  // Stub for now
}

// AI Command (existing brain endpoint)
export async function sendVoiceCommand(text) {
  if (USE_MOCK) return { response: "Mock voice command handled" };
  const response = await fetch(`${BASE_URL}/ai/command`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ command: text }),
  });
  if (!response.ok) throw new Error('Failed to send voice command');
  return response.json();
}