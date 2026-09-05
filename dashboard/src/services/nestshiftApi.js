import { EventEmitter } from 'events';

class NestShiftAPI extends EventEmitter {
  constructor() {
    super();
    this.baseURL = 'http://localhost:3000';
    this.ws = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 10;
    this.reconnectDelay = 1000;
    this.connectWebSocket();
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const config = {
      headers: {
        'Content-Type': 'application/json',
      },
      ...options,
    };

    try {
      const response = await fetch(url, config);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      return await response.json();
    } catch (err) {
      console.error(`NestShift API request failed: ${endpoint}`, err);
      throw err;
    }
  }

  connectWebSocket() {
    if (this.ws) {
      this.ws.close();
    }

    this.ws = new WebSocket(`${this.baseURL.replace('http', 'ws')}/ws`);

    this.ws.onopen = () => {
      this.reconnectAttempts = 0;
      this.emit('connected');
    };

    this.ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        this.emit('message', msg);
      } catch (err) {
        console.error('NestShift WebSocket message parse error:', err);
      }
    };

    this.ws.onclose = () => {
      this.emit('disconnected');
      if (this.reconnectAttempts < this.maxReconnectAttempts) {
        setTimeout(() => {
          this.reconnectAttempts++;
          this.reconnectDelay *= 1.5;
          this.connectWebSocket();
        }, this.reconnectDelay);
      }
    };

    this.ws.onerror = (err) => {
      console.error('NestShift WebSocket error:', err);
      this.emit('error', err);
    };
  }

  async getHealth() {
    return this.request('/health');
  }

  async getEnergyData() {
    return this.request('/api/energy');
  }

  async getBrainInsights() {
    return this.request('/api/brain/insights');
  }

  async getAutomationRules() {
    return this.request('/api/automation/rules');
  }

  async updateRule(id, patch) {
    return this.request(`/api/automation/rules/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(patch),
    });
  }

  subscribeBrainUpdates(callback) {
    this.on('message', (msg) => {
      if (msg.type === 'brain_update') {
        callback(msg.data);
      }
    });
  }
}

export default new NestShiftAPI();