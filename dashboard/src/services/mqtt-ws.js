import mqtt from 'mqtt';

export function createMqttClient() {
  const client = mqtt.connect('ws://localhost:9001');

  const subscriptions = new Map();
  let connectionCallback = null;

  client.on('connect', () => {
    console.log('MQTT connected');
    if (connectionCallback) connectionCallback(true);
    
    // Subscribe to topics
    client.subscribe('nestshift/devices/+/state');
    client.subscribe('nestshift/sensors/+/reading');
    client.subscribe('nestshift/agents/energy/forecast');
    client.subscribe('nestshift/tariff/current');
    client.subscribe('nestshift/agents/system/health');
  });

  client.on('disconnect', () => {
    console.log('MQTT disconnected');
    if (connectionCallback) connectionCallback(false);
  });

  client.on('message', (topic, message) => {
    try {
      const payload = JSON.parse(message.toString());
      const callback = subscriptions.get(topic);
      if (callback) callback(payload);
    } catch (error) {
      console.error('Failed to parse MQTT message:', error);
    }
  });

  return {
    subscribe(topic, callback) {
      subscriptions.set(topic, callback);
    },
    publish(topic, payload) {
      client.publish(topic, JSON.stringify(payload));
    },
    disconnect() {
      client.end();
    },
    onConnectionChange(callback) {
      connectionCallback = callback;
    }
  };
}