import { useMQTT } from '../hooks/useMQTT'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'

function formatUptime(seconds) {
  const days = Math.floor(seconds / 86400)
  const hours = Math.floor((seconds % 86400) / 3600)
  const mins = Math.floor((seconds % 3600) / 60)
  return `${days}d ${hours}h ${mins}m`
}

export default function Overview() {
  const { data } = useMQTT()
  const { overview } = data

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-orbit-cyan">System Overview</h1>
      
      {/* Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-orbit-card border border-orbit-border rounded-xl p-5">
          <div className="text-gray-400 text-sm">System Status</div>
          <div className="text-2xl font-bold text-orbit-green mt-1">{overview.systemStatus}</div>
        </div>
        <div className="bg-orbit-card border border-orbit-border rounded-xl p-5">
          <div className="text-gray-400 text-sm">Uptime</div>
          <div className="text-2xl font-bold mt-1">{formatUptime(overview.uptime)}</div>
        </div>
        <div className="bg-orbit-card border border-orbit-border rounded-xl p-5">
          <div className="text-gray-400 text-sm">CPU Usage</div>
          <div className="text-2xl font-bold mt-1">{overview.cpuUsage}%</div>
        </div>
        <div className="bg-orbit-card border border-orbit-border rounded-xl p-5">
          <div className="text-gray-400 text-sm">Memory</div>
          <div className="text-2xl font-bold mt-1">{overview.memoryUsage}MB</div>
        </div>
      </div>

      {/* Devices & MQTT */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-orbit-card border border-orbit-border rounded-xl p-5">
          <div className="text-gray-400 text-sm mb-3">Devices</div>
          <div className="flex items-center gap-4">
            <div className="text-4xl font-bold text-orbit-cyan">{overview.activeDevices}</div>
            <div className="text-gray-400">/ {overview.totalDevices} active</div>
          </div>
          <div className="mt-3 h-2 bg-orbit-border rounded-full overflow-hidden">
            <div
              className="h-full bg-orbit-cyan transition-all"
              style={{ width: `${(overview.activeDevices / overview.totalDevices) * 100}%` }}
            />
          </div>
        </div>
        <div className="bg-orbit-card border border-orbit-border rounded-xl p-5">
          <div className="text-gray-400 text-sm mb-3">MQTT Messages</div>
          <div className="flex items-center gap-4">
            <div className="text-4xl font-bold text-orbit-cyan">{overview.mqttMessagesPerMin}</div>
            <div className="text-gray-400">/ min</div>
          </div>
        </div>
      </div>

      {/* Activity Chart */}
      <div className="bg-orbit-card border border-orbit-border rounded-xl p-5">
        <div className="text-gray-400 text-sm mb-4">24h Activity</div>
        <ResponsiveContainer width="100%" height={200}>
          <LineChart data={data.energy.usageHistory}>
            <XAxis dataKey="hour" stroke="#666" fontSize={12} />
            <YAxis stroke="#666" fontSize={12} />
            <Tooltip
              contentStyle={{ background: '#12121a', border: '1px solid #1e1e2e', borderRadius: 8 }}
              labelStyle={{ color: '#00f5d4' }}
            />
            <Line type="monotone" dataKey="usage" stroke="#00f5d4" strokeWidth={2} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}