import { EventEmitter } from 'events';

class HAClient extends EventEmitter {
  constructor() {
    super();
    this.ws = null;
    this.authToken = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 10;
    this.reconnectDelay = 1000;
    this.connectionId = 1;
    this.states = new Map();
    this.subscribed = false;
    this.loadAuthToken();
    this.connect();
  }

  loadAuthToken() {
    try {
      const token = fs.readFileSync('/etc/nestshift/ha-token', 'utf8').trim();
      if (token && !token.startsWith('#')) {
        this.authToken = token;
      }
    } catch (err) {
      console.warn('HA token not found or invalid');
    }
  }

  connect() {
    if (this.ws) {
      this.ws.close();
    }

    this.ws = new WebSocket('ws://localhost:8123/api/websocket');

    this.ws.onopen = () => {
      this.reconnectAttempts = 0;
      this.emit('connected');
    };

    this.ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        this.handleMessage(msg);
      } catch (err) {
        console.error('HA WebSocket message parse error:', err);
      }
    };

    this.ws.onclose = () => {
      this.emit('disconnected');
      if (this.reconnectAttempts < this.maxReconnectAttempts) {
        setTimeout(() => {
          this.reconnectAttempts++;
          this.reconnectDelay *= 1.5;
          this.connect();
        }, this.reconnectDelay);
      }
    };

    this.ws.onerror = (err) => {
      console.error('HA WebSocket error:', err);
      this.emit('error', err);
    };
  }

  handleMessage(msg) {
    if (msg.type === 'auth_required') {
      this.send({ type: 'auth', access_token: this.authToken });
    } else if (msg.type === 'auth_ok') {
      this.emit('authenticated');
      this.subscribeStates();
    } else if (msg.type === 'result' && msg.success) {
      this.emit('result', msg);
    } else if (msg.type === 'event' && msg.event.event_type === 'state_changed') {
      const entity = msg.event.data.new_state;
      this.states.set(entity.entity_id, entity);
      this.emit('state_changed', entity);
    }
  }

  send(msg) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      msg.id = this.connectionId++;
      this.ws.send(JSON.stringify(msg));
    }
  }

  subscribeStates() {
    if (!this.subscribed) {
      this.send({
        type: 'subscribe_events',
        event_type: 'state_changed'
      });
      this.subscribed = true;
    }
  }

  getStates() {
    return Array.from(this.states.values());
  }

  subscribeStates(callback) {
    this.on('state_changed', callback);
  }

  callService(domain, service, data = {}) {
    this.send({
      type: 'call_service',
      domain,
      service,
      service_data: data
    });
  }

  getHistory(entityId, hours = 24) {
    const endTime = new Date();
    const startTime = new Date(endTime - hours * 60 * 60 * 1000);
    
    return new Promise((resolve, reject) => {
      const id = this.connectionId;
      this.once('result', (msg) => {
        if (msg.id === id) {
          if (msg.success) {
            resolve(msg.result);
          } else {
            reject(new Error(msg.error.message));
          }
        }
      });
      
      this.send({
        id,
        type: 'get_history',
        entity_id: entityId,
        start_time: startTime.toISOString(),
        end_time: endTime.toISOString()
      });
    });
  }
}

export default new HAClient();