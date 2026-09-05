import { useState, useEffect, useCallback } from 'react'
import mqtt from 'mqtt'

const MQTT_BROKER = 'ws://localhost:9001'

// Mock data fallback
const MOCK_DATA = {
  overview: {
    systemStatus: 'operational',
    uptime: 1472580,
    cpuUsage: 23,
    memoryUsage: 412,
    activeDevices: 8,
    totalDevices: 12,
    mqttMessagesPerMin: 47
  },
  brain: {
    neuronsActive: 24,
    synapsesTotal: 156,
    spikesLastHour: 1847,
    avgLatency: 2.3,
    autonomousActions: 12,
    manualOverrides: 3,
    intentDistribution: [
      { topic: 'light/living_room', weight: 0.72, spikes: 234 },
      { topic: 'light/bedroom', weight: 0.58, spikes: 189 },
      { topic: 'hvac', weight: 0.45, spikes: 156 },
      { topic: 'lock/front', weight: 0.38, spikes: 98 }
    ]
  },
  energy: {
    currentUsage: 1240,
    todayCost: 2.34,
    weekCost: 14.67,
    monthCost: 45.23,
    tariff: 'agile',
    usageHistory: Array.from({ length: 24 }, (_, i) => ({
      hour: i,
      usage: 800 + Math.random() * 800,
      cost: (800 + Math.random() * 800) * 0.30 / 1000
    }))
  },
  devices: {
    total: 12,
    online: 8,
    offline: 4,
    deviceList: [
      { id: 'light_living', name: 'Living Room Light', type: 'light', state: 'on', room: 'living_room', watts: 60 },
      { id: 'light_bedroom', name: 'Bedroom Light', type: 'light', state: 'off', room: 'bedroom', watts: 40 },
      { id: 'motion_living', name: 'Living Room Motion', type: 'sensor', state: 'active', room: 'living_room' },
      { id: 'temp_bedroom', name: 'Bedroom Temp', type: 'sensor', state: 'active', room: 'bedroom', value: 19.5 },
      { id: 'hvac', name: 'HVAC', type: 'hvac', state: 'heat', setpoint: 21, room: 'living_room', watts: 1200 },
      { id: 'lock_front', name: 'Front Door Lock', type: 'lock', state: 'locked', location: 'front' },
      { id: 'plug_kettle', name: 'Kettle Plug', type: 'switch', state: 'off', watts: 2000 },
      { id: 'sensor_kitchen', name: 'Kitchen Motion', type: 'sensor', state: 'inactive', room: 'kitchen' },
      { id: 'temp_kitchen', name: 'Kitchen Temp', type: 'sensor', state: 'active', room: 'kitchen', value: 22.1 },
      { id: 'door_front', name: 'Front Door', type: 'sensor', state: 'closed', location: 'front' },
      { id: 'power_main', name: 'Power Aggregate', type: 'sensor', state: 'active', value: 1240 },
      { id: 'light_kitchen', name: 'Kitchen Light', type: 'light', state: 'off', room: 'kitchen', watts: 60 }
    ]
  },
  safety: {
    hvacSetpoint: 21,
    highPowerDevices: 2,
    maxHighPower: 3,
    sensorAnomalies: [],
    inhibitoryDevices: ['oven', 'stove'],
    status: 'clear',
    violations: [
      { id: 1, time: '2026-05-25T18:32:15', action: 'hvac:set_temperature(35)', reason: 'hvac_max_temp_c', blocked: true },
      { id: 2, time: '2026-05-25T14:15:42', action: 'oven:turn_on()', reason: 'max_device_watts', blocked: true },
      { id: 3, time: '2026-05-25T12:45:33', action: 'turn_on(dev4)', reason: 'max_simultaneous_high_power', blocked: true }
    ]
  }
}

export function useMQTT() {
  const [status, setStatus] = useState('disconnected')
  const [data, setData] = useState(MOCK_DATA)
  const [client, setClient] = useState(null)

  useEffect(() => {
    let mqttClient
    let mockInterval

    const connect = async () => {
      try {
        mqttClient = mqtt.connect(MQTT_BROKER, {
          clientId: 'nestshift-dashboard',
          reconnectPeriod: 5000,
          connectTimeout: 5000
        })

        mqttClient.on('connect', () => {
          setStatus('connected')
          console.log('MQTT connected')
          mqttClient.subscribe('nestshift/#', { qos: 1 })
        })

        mqttClient.on('message', (topic, message) => {
          try {
            const payload = JSON.parse(message.toString())
            handleMessage(topic, payload)
          } catch (e) {}
        })

        mqttClient.on('error', () => setStatus('error'))
        mqttClient.on('close', () => setStatus('disconnected'))

        setClient(mqttClient)
      } catch (e) {
        console.log('MQTT unavailable, using mock data')
        setStatus('mock')
        startMockData()
      }
    }

    const handleMessage = (topic, payload) => {
      const prefix = 'nestshift/'
      if (!topic.startsWith(prefix)) return
      
      const key = topic.slice(prefix.length).split('/')[0]
      
      setData(prev => {
        const updated = { ...prev }
        
        if (key === 'overview') updated.overview = { ...prev.overview, ...payload }
        else if (key === 'brain') updated.brain = { ...prev.brain, ...payload }
        else if (key === 'energy') updated.energy = { ...prev.energy, ...payload }
        else if (key === 'devices') updated.devices = { ...prev.devices, ...payload }
        else if (key === 'safety') updated.safety = { ...prev.safety, ...payload }
        
        return updated
      })
    }

    const startMockData = () => {
      mockInterval = setInterval(() => {
        setData(prev => ({
          ...prev,
          overview: {
            ...prev.overview,
            mqttMessagesPerMin: Math.floor(40 + Math.random() * 20),
            cpuUsage: Math.floor(15 + Math.random() * 25)
          },
          energy: {
            ...prev.energy,
            currentUsage: Math.floor(1000 + Math.random() * 500)
          }
        }))
      }, 5000)
    }

    connect()

    return () => {
      if (mqttClient) mqttClient.end()
      if (mockInterval) clearInterval(mockInterval)
    }
  }, [])

  const publish = useCallback((topic, payload) => {
    if (client && status === 'connected') {
      client.publish(topic, JSON.stringify(payload))
    }
  }, [client, status])

  return { status, data, publish }
}