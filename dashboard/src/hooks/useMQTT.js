import { useState, useEffect, useCallback, useRef } from 'react';
import mqtt from 'mqtt';

/**
 * useMQTT - WebSocket MQTT hook for NestShift OS
 * Connects to ws://localhost:9001 and subscribes to:
 * - nestshift/brain/status (heartbeat every 5s)
 * - nestshift/brain/trace (neural trace events)
 * - nestshift/sensors/# (all sensor readings)
 * - nestshift/gpio/status (GPIO heartbeat)
 * - nestshift/agents/energy/status (energy agent status)
 */
export function useMQTT() {
  const [connected, setConnected] = useState(false);
  const [messages, setMessages] = useState({});
  const [latestByTopic, setLatestByTopic] = useState({});
  const [reconnecting, setReconnecting] = useState(false);
  const clientRef = useRef(null);
  const retryTimeoutRef = useRef(null);

  const NESTSHIFT_TOPICS = [
    'nestshift/brain/status',
    'nestshift/brain/trace',
    'nestshift/sensors/#',
    'nestshift/gpio/status',
    'nestshift/agents/energy/status',
  ];

  const connect = useCallback(() => {
    if (clientRef.current?.connected) return;
    
    try {
      const client = mqtt.connect('ws://localhost:9001', {
        clientId: `nestshift-dashboard-${Math.random().toString(16).slice(2, 10)}`,
        reconnectPeriod: 3000,
        connectTimeout: 10000,
      });

      client.on('connect', () => {
        console.log('[MQTT] Connected to ws://localhost:9001');
        setConnected(true);
        setReconnecting(false);
        
        // Subscribe to NestShift topics
        NESTSHIFT_TOPICS.forEach(topic => {
          client.subscribe(topic, { qos: 1 }, (err) => {
            if (err) console.error(`[MQTT] Failed to subscribe to ${topic}:`, err);
            else console.log(`[MQTT] Subscribed to ${topic}`);
          });
        });
      });

      client.on('message', (topic, payload) => {
        try {
          const data = JSON.parse(payload.toString());
          const timestamp = Date.now();
          
          // Update latest by topic
          setLatestByTopic(prev => ({
            ...prev,
            [topic]: { data, timestamp }
          }));
          
          // Add to message buffer (keep last 200 per topic pattern)
          setMessages(prev => {
            const topicPattern = topic.replace(/\/[^/]+$/, '/+'); // e.g., sensors/motion/+
            const key = topicPattern || topic;
            const topicMessages = prev[key] || [];
            const newMessages = [...topicMessages, { topic, data, timestamp }].slice(-200);
            return { ...prev, [key]: newMessages };
          });
        } catch (e) {
          console.warn('[MQTT] Failed to parse message:', topic, e);
        }
      });

      client.on('disconnect', () => {
        console.log('[MQTT] Disconnected');
        setConnected(false);
      });

      client.on('reconnect', () => {
        console.log('[MQTT] Reconnecting...');
        setReconnecting(true);
      });

      client.on('error', (err) => {
        console.error('[MQTT] Error:', err.message);
      });

      clientRef.current = client;
    } catch (err) {
      console.error('[MQTT] Connection error:', err);
      setReconnecting(true);
      // Retry after 3s
      retryTimeoutRef.current = setTimeout(connect, 3000);
    }
  }, []);

  const disconnect = useCallback(() => {
    if (retryTimeoutRef.current) {
      clearTimeout(retryTimeoutRef.current);
    }
    if (clientRef.current) {
      clientRef.current.end(true);
      clientRef.current = null;
    }
    setConnected(false);
  }, []);

  const subscribe = useCallback((topic, callback) => {
    if (clientRef.current?.connected) {
      clientRef.current.subscribe(topic, { qos: 1 }, (err) => {
        if (err) console.error(`[MQTT] Subscribe error:`, err);
      });
    }
  }, []);

  const publish = useCallback((topic, payload) => {
    if (clientRef.current?.connected) {
      clientRef.current.publish(topic, JSON.stringify(payload), { qos: 1 });
    }
  }, []);

  useEffect(() => {
    connect();
    return () => disconnect();
  }, [connect, disconnect]);

  return {
    connected,
    reconnecting,
    messages,
    latestByTopic,
    subscribe,
    publish,
    connect,
    disconnect,
  };
}

/**
 * Mock MQTT data for demo mode when backend unavailable
 */
export function getMockData() {
  const now = Date.now();
  
  return {
    brain: {
      status: {
        active_neurons: 8,
        strong_synapses: 6,
        autonomous_actions_today: 23,
        uptime_seconds: 86400,
        timestamp: now,
      },
      trace: [
        { timestamp: now - 5000, pre_topic: 'sensors/motion/living_room', post_topic: 'devices/light/living_room', weight: 0.72, trigger: 'autonomous', delta_t_ms: 15 },
        { timestamp: now - 12000, pre_topic: 'sensors/temperature/bedroom', post_topic: 'devices/hvac', weight: 0.45, trigger: 'manual_override', delta_t_ms: 30 },
        { timestamp: now - 25000, pre_topic: 'sensors/door/front', post_topic: 'devices/light/hallway', weight: 0.38, trigger: 'teaching', delta_t_ms: 20 },
        { timestamp: now - 40000, pre_topic: 'sensors/motion/kitchen', post_topic: 'devices/switch/kettle', weight: 0.68, trigger: 'autonomous', delta_t_ms: 45 },
        { timestamp: now - 60000, pre_topic: 'sensors/light/living_room', post_topic: 'devices/hvac', weight: 0.51, trigger: 'manual_override', delta_t_ms: 25 },
      ],
      synapses: [
        { id: 1, pre_topic: 'sensors/motion/living_room', post_topic: 'devices/light/living_room', weight: 0.72, spike_count: 45, status: 'AUTONOMOUS' },
        { id: 2, pre_topic: 'sensors/motion/kitchen', post_topic: 'devices/switch/kettle', weight: 0.68, spike_count: 38, status: 'AUTONOMOUS' },
        { id: 3, pre_topic: 'sensors/temperature/bedroom', post_topic: 'devices/hvac', weight: 0.45, spike_count: 22, status: 'LEARNING' },
        { id: 4, pre_topic: 'sensors/door/front', post_topic: 'devices/light/hallway', weight: 0.38, spike_count: 15, status: 'LEARNING' },
        { id: 5, pre_topic: 'sensors/light/living_room', post_topic: 'devices/hvac', weight: 0.51, spike_count: 28, status: 'LEARNING' },
        { id: 6, pre_topic: 'sensors/power/aggregate', post_topic: 'devices/hvac', weight: 0.82, spike_count: 67, status: 'AUTONOMOUS' },
      ],
    },
    sensors: {
      'nestshift/sensors/motion/living_room': { state: true, last_change: now - 30000 },
      'nestshift/sensors/motion/bedroom': { state: false, last_change: now - 120000 },
      'nestshift/sensors/temperature/living_room': { value: 21.5, unit: 'C', last_change: now - 60000 },
      'nestshift/sensors/temperature/bedroom': { value: 19.2, unit: 'C', last_change: now - 90000 },
      'nestshift/sensors/door/front': { state: 'closed', last_change: now - 3600000 },
      'nestshift/sensors/power/aggregate': { watts: 1240.5, last_change: now - 5000 },
      'nestshift/sensors/light/living_room': { lux: 450, last_change: now - 10000 },
    },
    energy: {
      tariff: {
        price_per_kwh: 28.5,
        is_peak: true,
        period: 'peak',
        until: now + 3600000,
      },
      schedule: [
        { device: 'dishwasher', window: '22:00-23:00', energy_wh: 1200, cost_p: 34, status: 'scheduled' },
        { device: 'washing_machine', window: '23:00-00:00', energy_wh: 2000, cost_p: 28, status: 'scheduled' },
        { device: 'ev_charger', window: '00:00-05:00', energy_wh: 25000, cost_p: 75, status: 'scheduled' },
        { device: 'kettle', window: '06:30-06:45', energy_wh: 500, cost_p: 14, status: 'deferred' },
      ],
      savings_today: 0.43,
      readings: Array.from({ length: 24 }, (_, i) => ({
        time: `${i}:00`,
        watts: 800 + Math.random() * 600 + (i >= 18 && i <= 21 ? 400 : 0),
      })),
    },
    devices: [
      { id: 'light_living_room', name: 'Living Room Light', type: 'light', state: 'on', wattage: 60, room: 'living_room' },
      { id: 'light_bedroom', name: 'Bedroom Light', type: 'light', state: 'off', wattage: 40, room: 'bedroom' },
      { id: 'switch_kettle', name: 'Kettle', type: 'switch', state: 'off', wattage: 2000, room: 'kitchen' },
      { id: 'hvac', name: 'HVAC', type: 'hvac', state: 'on', wattage: 1500, room: 'home', setpoint: 21 },
      { id: 'lock_front', name: 'Front Door Lock', type: 'lock', state: 'locked', room: 'entrance' },
    ],
    safety: {
      hvac_current: 21,
      hvac_min: 16,
      hvac_max: 26,
      high_power_count: 2,
      high_power_max: 3,
      inhibited_devices: [],
      recent_violations: [],
      overall_status: 'ALL CLEAR',
    },
  };
}