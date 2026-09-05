import { useMQTT } from '../hooks/useMQTT'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts'

export default function Brain() {
  const { data } = useMQTT()
  const { brain } = data

  const spikeHistory = Array.from({ length: 60 }, (_, i) => ({
    minute: 59 - i,
    spikes: Math.floor(20 + Math.random() * 40)
  })).reverse()

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-orbit-cyan">NARE Brain</h1>
      
      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-orbit-card border border-orbit-border rounded-xl p-5">
          <div className="text-gray-400 text-sm">Active Neurons</div>
          <div className="text-3xl font-bold text-orbit-cyan mt-1">{brain.neuronsActive}</div>
        </div>
        <div className="bg-orbit-card border border-orbit-border rounded-xl p-5">
          <div className="text-gray-400 text-sm">Total Synapses</div>
          <div className="text-3xl font-bold mt-1">{brain.synapsesTotal}</div>
        </div>
        <div className="bg-orbit-card border border-orbit-border rounded-xl p-5">
          <div className="text-gray-400 text-sm">Spikes (1h)</div>
          <div className="text-3xl font-bold text-orbit-cyan mt-1">{brain.spikesLastHour}</div>
        </div>
        <div className="bg-orbit-card border border-orbit-border rounded-xl p-5">
          <div className="text-gray-400 text-sm">Avg Latency</div>
          <div className="text-3xl font-bold mt-1">{brain.avgLatency}ms</div>
        </div>
      </div>

      {/* Action Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-orbit-card border border-orbit-border rounded-xl p-5">
          <div className="text-gray-400 text-sm mb-3">Autonomous Actions</div>
          <div className="text-4xl font-bold text-orbit-green">{brain.autonomousActions}</div>
        </div>
        <div className="bg-orbit-card border border-orbit-border rounded-xl p-5">
          <div className="text-gray-400 text-sm mb-3">Manual Overrides</div>
          <div className="text-4xl font-bold text-orbit-yellow">{brain.manualOverrides}</div>
        </div>
      </div>

      {/* Spike Activity */}
      <div className="bg-orbit-card border border-orbit-border rounded-xl p-5">
        <div className="text-gray-400 text-sm mb-4">Spike Activity (60min)</div>
        <ResponsiveContainer width="100%" height={200}>
          <AreaChart data={spikeHistory}>
            <XAxis dataKey="minute" stroke="#666" fontSize={12} />
            <YAxis stroke="#666" fontSize={12} />
            <Tooltip
              contentStyle={{ background: '#12121a', border: '1px solid #1e1e2e', borderRadius: 8 }}
              labelStyle={{ color: '#00f5d4' }}
            />
            <Area type="monotone" dataKey="spikes" stroke="#00f5d4" fill="#00f5d420" strokeWidth={2} />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Intent Distribution */}
      <div className="bg-orbit-card border border-orbit-border rounded-xl p-5">
        <div className="text-gray-400 text-sm mb-4">Intent Distribution</div>
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={brain.intentDistribution} layout="vertical">
            <XAxis type="number" domain={[0, 1]} stroke="#666" fontSize={12} />
            <YAxis dataKey="topic" type="category" stroke="#666" fontSize={12} width={120} />
            <Tooltip
              contentStyle={{ background: '#12121a', border: '1px solid #1e1e2e', borderRadius: 8 }}
              labelStyle={{ color: '#00f5d4' }}
            />
            <Bar dataKey="weight" fill="#00f5d4" radius={[0, 4, 4, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Top Synapses */}
      <div className="bg-orbit-card border border-orbit-border rounded-xl p-5">
        <div className="text-gray-400 text-sm mb-4">Top Synapses</div>
        <div className="space-y-3">
          {brain.intentDistribution.map((synapse, i) => (
            <div key={i} className="flex items-center justify-between p-3 bg-orbit-bg rounded-lg">
              <span className="text-sm">{synapse.topic}</span>
              <div className="flex items-center gap-4">
                <span className="text-orbit-cyan">{synapse.spikes} spikes</span>
                <span className="px-2 py-1 bg-orbit-cyan-dim text-orbit-cyan text-xs rounded">
                  w: {synapse.weight.toFixed(2)}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}