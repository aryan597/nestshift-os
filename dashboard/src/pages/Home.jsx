import React, { useState, useEffect } from 'react';
import { tokens, Glass } from '../design-system';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import { useNestShiftStore } from '../store/useNestShiftStore';

export default function Home() {
  const [currentTime, setCurrentTime] = useState(new Date());
  const { apiConnected, mqttConnected, energyUsage, currentTariff, agentStatus, comfortCostBias, devices } = useNestShiftStore();

  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  const todaysCost = energyUsage?.cost_gbp || 0;
  const savings = energyUsage?.savings_gbp || 0;
  const confidence = agentStatus?.automation?.confidence || 0;

  const getSliderText = (value) => {
    if (value <= 0.3) return "Maximising savings — minor comfort adjustments may occur";
    if (value <= 0.7) return "Balanced — smart shifts around your routine";
    return "Comfort first — savings where they don't affect you";
  };

  const chartData = energyUsage?.readings?.map((reading, index) => ({
    time: `${index}:00`,
    actual: reading.kwh,
    forecast: reading.kwh * 0.9, // Mock forecast
  })) || [];

  return (
    <div className="min-h-screen bg-gray-900 text-white p-4 space-y-6">
      {/* Header Bar */}
      <Glass className="sticky top-0 z-10 p-4 flex justify-between items-center">
        <h1 className="text-xl font-bold">NestShift</h1>
        <div className="text-lg">{currentTime.toLocaleTimeString()}</div>
        <div className="flex space-x-2">
          <div className={`w-3 h-3 rounded-full ${apiConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
          <div className={`w-3 h-3 rounded-full ${mqttConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
        </div>
      </Glass>

      {/* Hero Energy Card */}
      <Glass className="p-6" style={{ background: savings > 0.2 ? tokens.shadow.glow.energy : todaysCost > 1 ? tokens.shadow.glow.warning : 'none' }}>
        <div className="flex justify-between items-center">
          <div>
            <div className="text-4xl font-bold">£{todaysCost.toFixed(2)}</div>
            <div style={{ color: tokens.colors.accent.energy }}>Saved £{savings.toFixed(2)} vs unoptimised</div>
          </div>
          <div className="text-right">
            <div>{currentTariff?.price_per_kwh || 0}p/kWh</div>
            <div className={currentTariff?.is_peak ? 'text-amber-500' : 'text-green-500'}>
              {currentTariff?.is_peak ? 'Peak' : 'Off-Peak'}
            </div>
          </div>
        </div>
      </Glass>

      {/* Agent IQ Bar */}
      <Glass className="p-4">
        <h2 className="text-lg font-semibold mb-4">System Intelligence</h2>
        <div className="flex justify-around mb-4">
          {['Energy Agent', 'Automation Agent', 'System Agent'].map((agent, index) => (
            <div key={agent} className="flex items-center space-x-2">
              <div className={`w-2 h-2 rounded-full ${
                index === 1 ? (confidence > 0.5 ? 'bg-green-500' : 'bg-amber-500') : 'bg-green-500'
              }`}></div>
              <span>{agent}</span>
            </div>
          ))}
        </div>
        <div className="w-full bg-gray-700 rounded-full h-2">
          <div
            className="h-2 rounded-full"
            style={{
              width: `${confidence * 100}%`,
              backgroundColor: tokens.colors.accent.ai,
              boxShadow: tokens.shadow.glow.primary
            }}
          ></div>
        </div>
        <div className="flex justify-between text-sm mt-1">
          <span>Learning</span>
          <span>Optimised</span>
        </div>
      </Glass>

      {/* Comfort vs Cost Slider */}
      <Glass className="p-4">
        <h2 className="text-lg font-semibold mb-4">Your Priority</h2>
        <input
          type="range"
          min="0"
          max="1"
          step="0.1"
          value={comfortCostBias}
          onChange={(e) => useNestShiftStore.getState().setComfortCostBias(parseFloat(e.target.value))}
          className="w-full"
        />
        <div className="flex justify-between text-sm mt-2">
          <span>Save More £</span>
          <span>Stay Comfortable</span>
        </div>
        <p className="text-sm mt-2">{getSliderText(comfortCostBias)}</p>
      </Glass>

      {/* Energy Chart */}
      <Glass className="p-4">
        <h2 className="text-lg font-semibold mb-4">Today's Usage</h2>
        <ResponsiveContainer width="100%" height={200}>
          <AreaChart data={chartData}>
            <XAxis dataKey="time" />
            <YAxis />
            <Tooltip />
            <Area type="monotone" dataKey="actual" stroke={tokens.colors.accent.primary} fill={tokens.colors.accent.primary} />
            <Area type="monotone" dataKey="forecast" stroke={tokens.colors.accent.ai} fill="none" strokeDasharray="5 5" />
          </AreaChart>
        </ResponsiveContainer>
      </Glass>

      {/* Device Grid */}
      <Glass className="p-4">
        <h2 className="text-lg font-semibold mb-4">Devices ({devices.length})</h2>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {devices.map((device) => (
            <div key={device.id} className="p-4 rounded-lg border" style={{ borderColor: device.state === 'on' ? tokens.colors.accent.primary : tokens.colors.border }}>
              <div className="text-2xl mb-2">{device.type === 'light' ? '💡' : '🔌'}</div>
              <div className="font-semibold">{device.name}</div>
              <div className="text-sm">{device.state}</div>
            </div>
          ))}
        </div>
      </Glass>

      {/* Recent Decisions */}
      <Glass className="p-4">
        <h2 className="text-lg font-semibold mb-4">Why the system did this</h2>
        <p className="text-sm">No automated actions yet — learning your home</p>
      </Glass>
    </div>
  );
}