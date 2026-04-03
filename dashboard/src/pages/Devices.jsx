import React from 'react';
import { useNestShiftStore } from '../store/useNestShiftStore';
import { Glass, tokens } from '../design-system';

export default function Devices() {
  const { devices, updateDeviceState } = useNestShiftStore();

  const toggleDevice = (device) => {
    // Optimistic UI update
    updateDeviceState(device.id, { state: device.state === 'on' ? 'off' : 'on' });
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Active Devices</h1>
          <p className="text-gray-400 mt-1">Manage Zigbee and GPIO connected hardware.</p>
        </div>
        <button className="px-4 py-2 bg-white/5 border border-white/10 rounded-lg hover:bg-white/10 transition-colors text-sm font-medium">
          + Add Device
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {devices.map((device) => {
          const isOn = device.state === 'on';
          return (
            <Glass key={device.id} className="p-6 relative group overflow-hidden transition-all duration-300 hover:border-white/20">
              {isOn && (
                <div 
                  className="absolute top-0 right-0 w-32 h-32 blur-3xl opacity-20 pointer-events-none rounded-full"
                  style={{ backgroundColor: tokens.colors.accent.primary }}
                ></div>
              )}
              
              <div className="flex justify-between items-start mb-6">
                <div className={`p-3 rounded-xl inline-flex items-center justify-center transition-colors ${isOn ? 'bg-cyan-500/20 text-cyan-500' : 'bg-white/5 text-gray-500'}`}>
                   <span className="text-2xl">{device.type === 'light' ? '💡' : '🔌'}</span>
                </div>
                
                {/* Custom Toggle Switch */}
                <button 
                  onClick={() => toggleDevice(device)}
                  className={`relative w-12 h-6 rounded-full transition-colors duration-300 focus:outline-none ${isOn ? 'bg-cyan-500' : 'bg-gray-700'}`}
                >
                  <span className={`absolute top-1 w-4 h-4 rounded-full bg-white transition-transform duration-300 ${isOn ? 'left-7 font-bold text-center' : 'left-1'}`}></span>
                </button>
              </div>

              <div>
                <h3 className="text-lg font-medium text-white mb-1">{device.name}</h3>
                <div className="flex space-x-3 text-xs">
                   <span className={`font-mono px-2 py-0.5 rounded border ${isOn ? 'border-cyan-500/30 text-cyan-400 bg-cyan-500/10' : 'border-gray-600 text-gray-500 bg-black/40'}`}>
                     {device.state.toUpperCase()}
                   </span>
                   <span className="text-gray-500 uppercase tracking-wider">{device.connection_type}</span>
                </div>
              </div>
            </Glass>
          );
        })}
      </div>
    </div>
  );
}