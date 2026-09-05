import { useMQTT } from '../hooks/useMQTT'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts'

export default function Energy() {
  const { data } = useMQTT()
  const { energy } = data

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-orbit-cyan">Energy</h1>
      
      {/* Current Usage */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-orbit-card border border-orbit-border rounded-xl p-5">
          <div className="text-gray-400 text-sm">Current Usage</div>
          <div className="text-3xl font-bold text-orbit-cyan mt-1">{energy.currentUsage}</div>
          <div className="text-gray-500 text-sm">watts</div>
        </div>
        <div className="bg-orbit-card border border-orbit-border rounded-xl p-5">
          <div className="text-gray-400 text-sm">Today</div>
          <div className="text-3xl font-bold mt-1">£{energy.todayCost}</div>
        </div>
        <div className="bg-orbit-card border border-orbit-border rounded-xl p-5">
          <div className="text-gray-400 text-sm">This Week</div>
          <div className="text-3xl font-bold mt-1">£{energy.weekCost}</div>
        </div>
        <div className="bg-orbit-card border border-orbit-border rounded-xl p-5">
          <div className="text-gray-400 text-sm">This Month</div>
          <div className="text-3xl font-bold mt-1">£{energy.monthCost}</div>
        </div>
      </div>

      {/* Tariff */}
      <div className="bg-orbit-card border border-orbit-border rounded-xl p-5">
        <div className="flex items-center justify-between mb-4">
          <div>
            <div className="text-gray-400 text-sm">Current Tariff</div>
            <div className="text-2xl font-bold text-orbit-cyan uppercase">{energy.tariff}</div>
          </div>
        </div>
        <div className="text-gray-400 text-sm mb-4">24h Usage & Cost</div>
        <ResponsiveContainer width="100%" height={250}>
          <AreaChart data={energy.usageHistory}>
            <XAxis dataKey="hour" stroke="#666" fontSize={12} />
            <YAxis yAxisId="left" stroke="#666" fontSize={12} />
            <YAxis yAxisId="right" orientation="right" stroke="#666" fontSize={12} />
            <Tooltip
              contentStyle={{ background: '#12121a', border: '1px solid #1e1e2e', borderRadius: 8 }}
              labelStyle={{ color: '#00f5d4' }}
            />
            <Area yAxisId="left" type="monotone" dataKey="usage" stroke="#00f5d4" fill="#00f5d420" strokeWidth={2} name="Usage (W)" />
            <Area yAxisId="right" type="monotone" dataKey="cost" stroke="#ffd93d" fill="#ffd93d20" strokeWidth={2} name="Cost (£)" />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Savings */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-orbit-card border border-orbit-border rounded-xl p-5">
          <div className="text-gray-400 text-sm mb-2">Estimated Savings (vs Flat)</div>
          <div className="text-3xl font-bold text-orbit-green">£4.23</div>
          <div className="text-gray-500 text-sm mt-1">This week</div>
        </div>
        <div className="bg-orbit-card border border-orbit-border rounded-xl p-5">
          <div className="text-gray-400 text-sm mb-2">Optimisation Score</div>
          <div className="text-3xl font-bold text-orbit-cyan">78%</div>
          <div className="text-gray-500 text-sm mt-1">Based on tariff flexibility</div>
        </div>
      </div>
    </div>
  )
}