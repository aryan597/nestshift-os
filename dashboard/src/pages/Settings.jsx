import React from 'react';
import { useNestShiftStore } from '../store/useNestShiftStore';
import { Glass, tokens } from '../design-system';

export default function Settings() {
  const { apiConnected, mqttConnected } = useNestShiftStore();

  return (
    <div className="space-y-8 animate-in fade-in duration-500 max-w-4xl">
      <div className="flex justify-between items-center bg-black/30 p-8 rounded-3xl border border-white/5 relative overflow-hidden">
        <div className="absolute top-0 right-0 w-64 h-64 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none"></div>
        <div className="flex items-center space-x-6 relative z-10">
          <div className="w-24 h-24 rounded-full border-2 border-white/10 bg-gray-800 flex items-center justify-center text-4xl shadow-2xl">👤</div>
          <div>
            <h1 className="text-3xl font-bold tracking-tight text-white mb-1">NestShift Admin</h1>
            <p className="text-cyan-500">admin@nestshift.com</p>
          </div>
        </div>
        <div className="relative z-10 text-right space-y-2">
          <div className="flex items-center space-x-3 justify-end">
            <span className="text-sm text-gray-400">System Hub ID:</span>
            <span className="font-mono text-sm bg-white/10 px-2 py-1 rounded">NSH-88A92</span>
          </div>
          <button className="text-sm text-red-500 hover:text-red-400 bg-red-500/10 px-4 py-2 rounded-lg transition-colors">
            Sign Out
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Glass className="p-8">
           <h3 className="text-xl font-bold mb-6 flex items-center"><span className="mr-3 text-cyan-400">🔌</span> Hardware Configuration</h3>
           <p className="text-gray-400 text-sm mb-6">Manage internal GPIO pins and Zigbee adapter settings mapping.</p>
           
           <div className="space-y-4">
             <button className="w-full text-left p-4 rounded-xl bg-black/40 border border-white/5 hover:border-cyan-500/50 transition-colors flex justify-between items-center group">
               <span className="font-medium group-hover:text-cyan-400">GPIO Pin Mappings</span>
               <span className="text-gray-500">→</span>
             </button>
             <button className="w-full text-left p-4 rounded-xl bg-black/40 border border-white/5 hover:border-cyan-500/50 transition-colors flex justify-between items-center group">
               <span className="font-medium group-hover:text-cyan-400">Zigbee 2 MQTT Coordinator</span>
               <span className="text-gray-500">→</span>
             </button>
             <button className="w-full text-left p-4 rounded-xl bg-black/40 border border-white/5 hover:border-cyan-500/50 transition-colors flex justify-between items-center group">
               <span className="font-medium group-hover:text-cyan-400">Wi-Fi & Network</span>
               <span className="text-gray-500">→</span>
             </button>
           </div>
        </Glass>

        <Glass className="p-8">
           <h3 className="text-xl font-bold mb-6 flex items-center"><span className="mr-3 text-purple-400">🧠</span> AI Engine Settings</h3>
           <p className="text-gray-400 text-sm mb-6">Customize the behavior of the autonomous background agents.</p>
           
           <div className="space-y-6">
             <div className="flex items-center justify-between">
                <div>
                  <div className="font-medium text-white">Aggressive Savings</div>
                  <div className="text-xs text-gray-500">AI will prioritize cost over comfort unconditionally.</div>
                </div>
                <div className="w-10 h-5 bg-gray-700 rounded-full relative"><div className="absolute left-1 top-1 w-3 h-3 bg-white rounded-full"></div></div>
             </div>
             <div className="flex items-center justify-between">
                <div>
                  <div className="font-medium text-white">Auto-discover Devices</div>
                  <div className="text-xs text-gray-500">Automatically map new smart devices to default routines.</div>
                </div>
                <div className="w-10 h-5 bg-cyan-500 rounded-full relative"><div className="absolute left-6 top-1 w-3 h-3 bg-white rounded-full"></div></div>
             </div>
             
             <div className="pt-4 border-t border-white/10">
               <div className="text-xs text-gray-400 mb-2">Microservice Diagnostics</div>
               <div className="flex space-x-4">
                 <div className="flex items-center space-x-2 text-xs font-mono"><div className={`w-2 h-2 rounded-full ${apiConnected ? 'bg-[#00e676]' : 'bg-red-500'}`}></div><span>FastAPI</span></div>
                 <div className="flex items-center space-x-2 text-xs font-mono"><div className={`w-2 h-2 rounded-full ${mqttConnected ? 'bg-[#00e676]' : 'bg-red-500'}`}></div><span>Mosquitto</span></div>
               </div>
             </div>
           </div>
        </Glass>
      </div>
    </div>
  );
}