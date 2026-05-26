import { useMQTT } from '../hooks/useMQTT'

const typeIcons = {
  light: '💡',
  sensor: '📡',
  hvac: '🌡️',
  lock: '🔒',
  switch: '🔌'
}

const typeColors = {
  light: 'text-yellow-400',
  sensor: 'text-blue-400',
  hvac: 'text-orange-400',
  lock: 'text-purple-400',
  switch: 'text-red-400'
}

export default function Devices() {
  const { data } = useMQTT()
  const { devices } = data

  const lights = devices.deviceList.filter(d => d.type === 'light')
  const sensors = devices.deviceList.filter(d => d.type === 'sensor')
  const hvac = devices.deviceList.filter(d => d.type === 'hvac')
  const switches = devices.deviceList.filter(d => d.type === 'switch' || d.type === 'lock')

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-orbit-cyan">Devices</h1>
      
      {/* Summary */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-orbit-card border border-orbit-border rounded-xl p-5">
          <div className="text-gray-400 text-sm">Total</div>
          <div className="text-3xl font-bold mt-1">{devices.total}</div>
        </div>
        <div className="bg-orbit-card border border-orbit-border rounded-xl p-5">
          <div className="text-gray-400 text-sm">Online</div>
          <div className="text-3xl font-bold text-orbit-green mt-1">{devices.online}</div>
        </div>
        <div className="bg-orbit-card border border-orbit-border rounded-xl p-5">
          <div className="text-gray-400 text-sm">Offline</div>
          <div className="text-3xl font-bold text-orbit-red mt-1">{devices.offline}</div>
        </div>
      </div>

      {/* Lighting */}
      <div className="bg-orbit-card border border-orbit-border rounded-xl p-5">
        <h2 className="text-lg font-semibold mb-4">💡 Lighting</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {lights.map(device => (
            <div key={device.id} className="p-4 bg-orbit-bg rounded-lg flex items-center justify-between">
              <div>
                <div className="font-medium">{device.name}</div>
                <div className="text-gray-500 text-sm">{device.room}</div>
              </div>
              <div className="text-right">
                <div className={`text-lg font-bold ${device.state === 'on' ? 'text-orbit-cyan' : 'text-gray-500'}`}>
                  {device.state.toUpperCase()}
                </div>
                {device.watts && <div className="text-gray-500 text-xs">{device.watts}W</div>}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* HVAC */}
      <div className="bg-orbit-card border border-orbit-border rounded-xl p-5">
        <h2 className="text-lg font-semibold mb-4">🌡️ HVAC</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {hvac.map(device => (
            <div key={device.id} className="p-4 bg-orbit-bg rounded-lg flex items-center justify-between">
              <div>
                <div className="font-medium">{device.name}</div>
                <div className="text-gray-500 text-sm">{device.room}</div>
              </div>
              <div className="text-right">
                <div className="text-orbit-cyan text-lg font-bold">{device.setpoint}°C</div>
                <div className="text-gray-500 text-xs">{device.state.toUpperCase()} • {device.watts}W</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Sensors */}
      <div className="bg-orbit-card border border-orbit-border rounded-xl p-5">
        <h2 className="text-lg font-semibold mb-4">📡 Sensors</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {sensors.map(device => (
            <div key={device.id} className="p-4 bg-orbit-bg rounded-lg flex items-center justify-between">
              <div>
                <div className="font-medium">{device.name}</div>
                <div className="text-gray-500 text-sm">{device.room || device.location}</div>
              </div>
              <div className="text-right">
                {device.value !== undefined ? (
                  <div className="text-orbit-cyan text-lg font-bold">
                    {device.value}{device.id.includes('temp') ? '°C' : ''}
                  </div>
                ) : (
                  <div className={`text-lg font-bold ${device.state === 'active' ? 'text-orbit-green' : 'text-gray-500'}`}>
                    {device.state.toUpperCase()}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Locks & Switches */}
      <div className="bg-orbit-card border border-orbit-border rounded-xl p-5">
        <h2 className="text-lg font-semibold mb-4">🔌 Locks & Switches</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {switches.map(device => (
            <div key={device.id} className="p-4 bg-orbit-bg rounded-lg flex items-center justify-between">
              <div>
                <div className="font-medium">{device.name}</div>
                <div className="text-gray-500 text-sm">{device.location || device.room}</div>
              </div>
              <div className="text-right">
                <div className={`text-lg font-bold ${device.state === 'on' || device.state === 'locked' ? 'text-orbit-cyan' : 'text-gray-500'}`}>
                  {device.state.toUpperCase()}
                </div>
                {device.watts && <div className="text-gray-500 text-xs">{device.watts}W</div>}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}