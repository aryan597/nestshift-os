import { useMQTT } from '../hooks/useMQTT'

export default function Safety() {
  const { data } = useMQTT()
  const { safety } = data

  const statusColors = {
    clear: 'text-orbit-green bg-orbit-green',
    warning: 'text-orbit-yellow bg-orbit-yellow',
    violation: 'text-orbit-red bg-orbit-red'
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-orbit-cyan">Safety Monitor</h1>
      
      {/* 5 Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {/* HVAC Range */}
        <div className="bg-orbit-card border border-orbit-border rounded-xl p-5">
          <div className="text-gray-400 text-sm mb-2">HVAC Range (16-26°C)</div>
          <div className="flex items-center gap-4">
            <div className="text-4xl font-bold text-orbit-cyan">{safety.hvacSetpoint}°</div>
            <div className="flex-1">
              <div className="h-3 bg-orbit-border rounded-full overflow-hidden">
                <div 
                  className="h-full bg-orbit-cyan transition-all"
                  style={{ width: `${((safety.hvacSetpoint - 16) / 10) * 100}%` }}
                />
              </div>
              <div className="flex justify-between text-xs text-gray-500 mt-1">
                <span>16°</span>
                <span>26°</span>
              </div>
            </div>
          </div>
        </div>

        {/* High-Power Devices */}
        <div className="bg-orbit-card border border-orbit-border rounded-xl p-5">
          <div className="text-gray-400 text-sm mb-2">High-Power Devices</div>
          <div className="flex items-center gap-4">
            <div className={`text-4xl font-bold ${safety.highPowerDevices >= safety.maxHighPower ? 'text-orbit-red' : 'text-orbit-cyan'}`}>
              {safety.highPowerDevices}
            </div>
            <div className="text-gray-400">/ {safety.maxHighPower}</div>
          </div>
          <div className="mt-3 h-3 bg-orbit-border rounded-full overflow-hidden">
            <div 
              className={`h-full transition-all ${safety.highPowerDevices >= safety.maxHighPower ? 'bg-orbit-red' : 'bg-orbit-cyan'}`}
              style={{ width: `${(safety.highPowerDevices / safety.maxHighPower) * 100}%` }}
            />
          </div>
        </div>

        {/* Sensor Coherence */}
        <div className="bg-orbit-card border border-orbit-border rounded-xl p-5">
          <div className="text-gray-400 text-sm mb-2">Sensor Coherence</div>
          {safety.sensorAnomalies.length === 0 ? (
            <div className="flex items-center gap-2">
              <span className="text-orbit-green text-2xl">✓</span>
              <span className="text-orbit-green font-bold">All Clear</span>
            </div>
          ) : (
            <div className="space-y-2">
              {safety.sensorAnomalies.map((a, i) => (
                <div key={i} className="p-2 bg-orbit-red/20 border border-orbit-red/30 rounded text-orbit-red text-sm">
                  {a.sensor}: {a.issue}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Inhibitory Control */}
        <div className="bg-orbit-card border border-orbit-border rounded-xl p-5">
          <div className="text-gray-400 text-sm mb-2">Inhibitory Control</div>
          <div className="space-y-2">
            {safety.inhibitoryDevices.map((device, i) => (
              <div key={i} className="flex items-center gap-2">
                <span className="text-orbit-red">⛔</span>
                <span className="text-gray-300">{device}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Overall Status */}
        <div className="bg-orbit-card border border-orbit-border rounded-xl p-5 md:col-span-2">
          <div className="text-gray-400 text-sm mb-2">Overall Safety Status</div>
          <div className="flex items-center gap-4">
            <div className={`w-6 h-6 rounded-full ${statusColors[safety.status]}`} />
            <span className={`text-3xl font-bold ${
              safety.status === 'clear' ? 'text-orbit-green' : 
              safety.status === 'warning' ? 'text-orbit-yellow' : 'text-orbit-red'
            }`}>
              {safety.status.toUpperCase()}
            </span>
          </div>
        </div>
      </div>

      {/* Violation Log */}
      <div className="bg-orbit-card border border-orbit-border rounded-xl p-5">
        <h2 className="text-lg font-semibold mb-4">🚫 Violation Log</h2>
        <div className="space-y-2">
          {safety.violations.map(violation => (
            <div key={violation.id} className="flex items-center justify-between p-3 bg-orbit-bg rounded-lg">
              <div className="flex items-center gap-3">
                <span className="text-orbit-red">⛔</span>
                <div>
                  <div className="font-mono text-sm text-gray-300">{violation.action}</div>
                  <div className="text-gray-500 text-xs">{violation.time}</div>
                </div>
              </div>
              <div className="text-right">
                <div className="px-2 py-1 bg-orbit-red/20 border border-orbit-red/30 rounded text-orbit-red text-xs">
                  {violation.reason}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}