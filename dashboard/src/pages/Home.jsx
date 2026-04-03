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
    <div className="space-y-6">
      {/* Top Search / Status Bar */}
      <div className="flex justify-between items-center bg-[#0f131a]/80 backdrop-blur-md border border-white/5 p-4 rounded-2xl">
        <div className="flex-1 max-w-xl relative">
          <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
            <span className="text-gray-500">🔍</span>
          </div>
          <input 
            type="text" 
            placeholder="Search agents, prompts, devices, anything..." 
            className="w-full bg-black/40 border border-white/10 rounded-xl py-2.5 pl-12 pr-4 text-sm text-white focus:outline-none focus:border-cyan-500 transition-colors"
          />
        </div>
        <div className="flex items-center space-x-4">
          <div className="flex space-x-3 bg-black/40 p-2 rounded-xl border border-white/5">
            <div className={`w-3 h-3 rounded-full shadow-[0_0_8px_currentColor] ${apiConnected ? 'text-green-400 bg-green-400' : 'text-red-500 bg-red-500'}`} title="API Status"></div>
            <div className={`w-3 h-3 rounded-full shadow-[0_0_8px_currentColor] ${mqttConnected ? 'text-green-400 bg-green-400' : 'text-red-500 bg-red-500'}`} title="MQTT Status"></div>
          </div>
          <div className="text-sm font-medium text-gray-300 bg-black/40 px-4 py-2 rounded-xl border border-white/5">
            {currentTime.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* LEFT COLUMN: Controls & Smart Schedule */}
        <div className="lg:col-span-4 space-y-6">
          <div className="flex items-center space-x-3 mb-2">
            <span className="text-[#00f0ff] text-xl">⚡</span>
            <h2 className="text-xl font-medium tracking-wide">Energy Flow</h2>
          </div>
          
          <Glass className="p-6">
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-sm text-gray-400 font-medium">Optimization Priority</h3>
              <span className="px-3 py-1 rounded-full text-xs bg-[#00e676]/10 text-[#00e676] border border-[#00e676]/20">Auto adjusted</span>
            </div>
            
            <div className="space-y-4">
              <div className="space-y-2">
                <div className="flex justify-between text-xs text-gray-400 font-medium">
                  <span>Savings</span>
                  <span>Comfort</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.1"
                  value={comfortCostBias}
                  onChange={(e) => useNestShiftStore.getState().setComfortCostBias(parseFloat(e.target.value))}
                  className="w-full h-2 bg-black/50 rounded-full appearance-none cursor-pointer accent-[#00f0ff]"
                  style={{
                    background: `linear-gradient(to right, ${tokens.colors.accent.energy} 0%, ${tokens.colors.accent.primary} 100%)`
                  }}
                />
                <p className="text-xs text-gray-400 pt-2">{getSliderText(comfortCostBias)}</p>
              </div>
            </div>
          </Glass>

          {/* Connected Devices */}
          <Glass className="p-6">
            <h3 className="text-sm text-gray-400 font-medium mb-4">Active Devices ({devices.length})</h3>
            <div className="space-y-3">
              {devices.slice(0, 4).map((device) => (
                <div key={device.id} className="flex justify-between items-center p-3 rounded-xl bg-black/30 border border-white/5 hover:border-white/10 transition-colors">
                  <div className="flex items-center space-x-3">
                    <span className="text-lg opacity-70">{device.type === 'light' ? '💡' : '🔌'}</span>
                    <span className="text-sm font-medium">{device.name}</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className="text-xs text-gray-500 capitalize">{device.state}</span>
                    <div className={`w-2 h-2 rounded-full ${device.state === 'on' ? 'bg-[#00f0ff] shadow-[0_0_8px_#00f0ff]' : 'bg-gray-600'}`}></div>
                  </div>
                </div>
              ))}
            </div>
          </Glass>
        </div>

        {/* CENTER COLUMN: Focus Mode / Main Dial */}
        <div className="lg:col-span-4 space-y-6">
          <div className="flex items-center space-x-3 mb-2">
            <span className="text-[#00f0ff] text-xl">🎯</span>
            <h2 className="text-xl font-medium tracking-wide">System Focus</h2>
          </div>

          <Glass className="p-6 flex flex-col items-center justify-center min-h-[400px]">
            {/* Massive Circular Dial */}
            <div className="relative w-64 h-64 rounded-full flex items-center justify-center mb-8"
                 style={{
                   background: 'radial-gradient(circle, rgba(15,19,26,1) 0%, rgba(0,0,0,1) 100%)',
                   boxShadow: `0 0 40px ${todaysCost > 1 ? 'rgba(245,158,11,0.1)' : 'rgba(0,240,255,0.15)'}, inset 0 0 20px rgba(255,255,255,0.02)`,
                   border: `1px solid ${tokens.colors.border}`
                 }}>
              
              {/* Outer Glowing Indicator Line */}
              <svg className="absolute inset-0 w-full h-full -rotate-90">
                <circle cx="128" cy="128" r="126" stroke={tokens.colors.border} strokeWidth="2" fill="none" />
                <circle 
                  cx="128" cy="128" r="126" 
                  stroke={tokens.colors.accent.primary} 
                  strokeWidth="4" 
                  fill="none" 
                  strokeDasharray="791" 
                  strokeDashoffset="200"
                  strokeLinecap="round"
                  style={{ filter: 'drop-shadow(0 0 8px rgba(0, 240, 255, 0.5))' }}
                />
              </svg>

              <div className="text-center z-10 w-full px-4">
                <div className="text-gray-400 text-sm mb-1 font-medium tracking-wider uppercase">Today's Cost</div>
                <div className="text-5xl font-bold text-white mb-2 tracking-tight">£{todaysCost.toFixed(2)}</div>
                <div className="inline-block px-3 py-1 rounded-full text-xs font-medium border"
                  style={{
                    backgroundColor: `${tokens.colors.accent.energy}15`,
                    color: tokens.colors.accent.energy,
                    borderColor: `${tokens.colors.accent.energy}30`
                  }}>
                  Saved £{savings.toFixed(2)}
                </div>
              </div>
            </div>

            {/* Current Tariff Info Plate */}
            <div className="w-full flex justify-between items-center p-4 rounded-xl border border-white/5 bg-black/40">
               <div className="flex items-center space-x-3">
                 <div className={`p-2 rounded-lg ${currentTariff?.is_peak ? 'bg-[#f59e0b]/20 text-[#f59e0b]' : 'bg-[#00f0ff]/20 text-[#00f0ff]'}`}>
                    {currentTariff?.is_peak ? '⚠️' : '⚡'}
                 </div>
                 <div>
                   <div className="text-xs text-gray-400">Current Tariff</div>
                   <div className="text-sm font-semibold">{currentTariff?.price_per_kwh || 0}p/kWh</div>
                 </div>
               </div>
               <div className={`text-sm font-medium ${currentTariff?.is_peak ? 'text-[#f59e0b]' : 'text-[#00f0ff]'}`}>
                 {currentTariff?.is_peak ? 'Peak Rate' : 'Off-Peak'}
               </div>
            </div>
          </Glass>
        </div>

        {/* RIGHT COLUMN: Insights & Charts */}
        <div className="lg:col-span-4 space-y-6">
          <div className="flex items-center space-x-3 mb-2">
            <span className="text-[#00e676] text-xl">📊</span>
            <h2 className="text-xl font-medium tracking-wide">Insights</h2>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <Glass className="p-4">
              <div className="text-xs font-medium text-gray-400 mb-2 whitespace-nowrap">Agent Confidence</div>
              <div className="flex items-end space-x-1">
                <span className="text-3xl font-bold text-white">{Math.round(confidence * 100)}</span>
                <span className="text-sm text-[#00e676] mb-1">/100</span>
              </div>
            </Glass>
            <Glass className="p-4">
              <div className="text-xs font-medium text-gray-400 mb-2">System AI Tasks</div>
              <div className="flex items-end space-x-1">
                <span className="text-3xl font-bold text-white">14</span>
              </div>
            </Glass>
          </div>

          {/* AI Agents Health */}
          <Glass className="p-6 relative overflow-hidden">
             {/* Decorative glow */}
             <div className="absolute -top-10 -right-10 w-32 h-32 bg-[#8b5cf6]/20 blur-3xl rounded-full"></div>
             
             <h3 className="text-sm text-gray-400 font-medium mb-5">AI Agents Status</h3>
             <div className="space-y-4">
                {['Energy Agent', 'Automation Agent', 'System Agent'].map((agent, index) => (
                  <div key={agent} className="relative">
                    <div className="flex justify-between text-xs mb-1">
                      <span className="font-medium text-gray-200">{agent}</span>
                      <span className={index === 1 && confidence < 0.5 ? 'text-[#f59e0b]' : 'text-[#00e676]'}>Active</span>
                    </div>
                    <div className="w-full bg-white/5 rounded-full h-1.5 border border-white/5">
                      <div className="h-1.5 rounded-full" style={{
                        width: '100%',
                        backgroundColor: index === 1 && confidence < 0.5 ? tokens.colors.accent.warning : tokens.colors.accent.energy,
                        boxShadow: `0 0 10px ${index === 1 && confidence < 0.5 ? tokens.colors.accent.warning : tokens.colors.accent.energy}`
                      }}></div>
                    </div>
                  </div>
                ))}
             </div>
          </Glass>

          {/* Usage Chart */}
          <Glass className="p-6">
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-sm text-gray-400 font-medium">Usage Rhythm</h3>
              <div className="w-8 h-8 rounded-full bg-white/5 border border-white/10 flex items-center justify-center">
                 📈
              </div>
            </div>
            
            <div className="h-[150px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={chartData} margin={{ top: 5, right: 0, left: -20, bottom: 0 }}>
                  <XAxis dataKey="time" stroke="#475569" fontSize={10} tickLine={false} axisLine={false} />
                  <YAxis stroke="#475569" fontSize={10} tickLine={false} axisLine={false} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#0f131a', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px' }}
                    itemStyle={{ color: '#00f0ff' }}
                  />
                  <Area 
                    type="monotone" 
                    dataKey="actual" 
                    stroke={tokens.colors.accent.primary} 
                    strokeWidth={2}
                    fillOpacity={1} 
                    fill="url(#colorActual)" 
                  />
                  <defs>
                    <linearGradient id="colorActual" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor={tokens.colors.accent.primary} stopOpacity={0.3}/>
                      <stop offset="95%" stopColor={tokens.colors.accent.primary} stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </Glass>
        </div>
      </div>
    </div>
  );
}