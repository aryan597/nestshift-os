import React from 'react';
import { useNestShiftStore } from '../store/useNestShiftStore';
import { Glass, tokens } from '../design-system';

export default function Energy() {
  const { energyUsage, currentTariff, comfortCostBias } = useNestShiftStore();

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Energy Hub</h1>
          <p className="text-gray-400 mt-1">Deep dive into your consumption and tariffs.</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Glass className="p-8 md:col-span-2 relative overflow-hidden">
           <h3 className="text-lg font-medium mb-6">Current Cycle Breakdown</h3>
           
           <div className="grid grid-cols-3 gap-8 mb-8">
             <div>
               <div className="text-sm text-gray-400 mb-1">Total Consumption</div>
               <div className="text-3xl font-bold text-white">{energyUsage?.kwh_total || '0.0'} <span className="text-lg text-gray-500">kWh</span></div>
             </div>
             <div>
               <div className="text-sm text-gray-400 mb-1">Generated (Solar)</div>
               <div className="text-3xl font-bold text-[#00e676]">0.0 <span className="text-lg text-[#00e676]/60">kWh</span></div>
             </div>
             <div>
               <div className="text-sm text-gray-400 mb-1">Total Cost</div>
               <div className="text-3xl font-bold text-white">£{energyUsage?.cost_gbp || '0.00'}</div>
             </div>
           </div>

           <div className="w-full bg-white/5 h-4 rounded-full overflow-hidden flex">
             <div className="bg-[#00f0ff] h-full" style={{ width: '60%' }} title="HVAC"></div>
             <div className="bg-[#8b5cf6] h-full" style={{ width: '25%' }} title="Water Heater"></div>
             <div className="bg-white/20 h-full" style={{ width: '15%' }} title="Other"></div>
           </div>
           <div className="flex space-x-6 mt-4 text-xs font-medium text-gray-400">
             <div className="flex items-center space-x-2"><div className="w-2 h-2 rounded-full bg-[#00f0ff]"></div><span>HVAC (60%)</span></div>
             <div className="flex items-center space-x-2"><div className="w-2 h-2 rounded-full bg-[#8b5cf6]"></div><span>Water Heater (25%)</span></div>
             <div className="flex items-center space-x-2"><div className="w-2 h-2 rounded-full bg-white/20"></div><span>Base Load (15%)</span></div>
           </div>
        </Glass>

        <Glass className="p-8">
           <h3 className="text-lg font-medium mb-6">Live Tariff</h3>
           <div className="flex items-center justify-center p-8 bg-black/40 rounded-full w-48 h-48 mx-auto border" style={{ borderColor: currentTariff?.is_peak ? tokens.colors.accent.warning : tokens.colors.border }}>
             <div className="text-center">
               <div className="text-4xl font-bold text-white mb-2">{currentTariff?.price_per_kwh || 0}<span className="text-lg text-gray-500">p</span></div>
               <div className={`text-sm font-medium ${currentTariff?.is_peak ? 'text-[#f59e0b]' : 'text-[#00e676]'}`}>
                 {currentTariff?.is_peak ? 'PEAK RATE' : 'OFF PEAK'}
               </div>
             </div>
           </div>
           <div className="text-center mt-6 text-sm text-gray-400">
             Provided by <span className="text-white">{currentTariff?.provider || 'Unknown'}</span>
           </div>
        </Glass>
      </div>
    </div>
  );
}