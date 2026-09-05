import React, { useState } from 'react';
import { Glass, tokens } from '../design-system';

export default function SmartSchedule() {
  const [filter, setFilter] = useState('Energy'); // 'Energy' or 'Routine'

  const energyEvents = [
    { time: '08:00', title: 'Off-Peak Pre-cooling', desc: 'HVAC cooled living area to 20°C using cheap rate.', current: false },
    { time: '11:30', title: 'Water Heater Disabled', desc: 'Peak grid pricing started. Shifted load.', current: false },
    { time: '14:00', title: 'Target Optimization', desc: 'Maintaining baseline comfort. 45% savings active.', current: true },
    { time: '17:00', title: 'Solar Excess Utilized', desc: 'Washing machine triggered via Zigbee relay.', current: false },
    { time: '21:00', title: 'Night Routine Prep', desc: 'Gradually cooling bedrooms down.', current: false }
  ];

  const routineEvents = [
    { time: '07:30', title: 'Good Morning Routine', desc: 'Blinds opened, Kitchen Spots On.', current: false },
    { time: '08:45', title: 'Away Mode Engaged', desc: 'Motion ceased. Armed perimeter sensors.', current: false },
    { time: '18:15', title: 'Welcome Home', desc: 'Front Door unlocked, Living Room Lights On.', current: true },
    { time: '22:30', title: 'Sleep Routine', desc: 'All media devices powered down, lights off.', current: false }
  ];

  const activeEvents = filter === 'Energy' ? energyEvents : routineEvents;

  return (
    <div className="space-y-8 animate-in fade-in duration-500 max-w-4xl">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">AI Schedule</h1>
          <p className="text-gray-400 mt-1">Autonomous actions determined by NestShift AI.</p>
        </div>
        
        {/* Sleek Toggle Switch */}
        <div className="flex bg-[#121622] p-1 rounded-xl border border-white/5">
          <button
            onClick={() => setFilter('Energy')}
            className={`px-6 py-2 rounded-lg text-sm font-medium transition-all ${
              filter === 'Energy' 
                ? 'bg-black/50 text-[#00e676] shadow-sm border border-white/10' 
                : 'text-gray-500 hover:text-gray-300'
            }`}
          >
            Energy Savings
          </button>
          <button
            onClick={() => setFilter('Routine')}
            className={`px-6 py-2 rounded-lg text-sm font-medium transition-all ${
              filter === 'Routine' 
                ? 'bg-black/50 text-[#00f0ff] shadow-sm border border-white/10' 
                : 'text-gray-500 hover:text-gray-300'
            }`}
          >
            Daily Routines
          </button>
        </div>
      </div>

      <Glass className="p-8">
        <div className="relative border-l-2 border-white/10 ml-4 space-y-10 py-4">
          {activeEvents.map((event, i) => (
            <div key={i} className="relative pl-8 group">
              {/* Timeline dot */}
              <div 
                className={`absolute left-[-9px] top-1.5 w-4 h-4 rounded-full border-2 border-[#121622] transition-colors ${
                  event.current 
                    ? filter === 'Energy' ? 'bg-[#00e676] shadow-[0_0_15px_rgba(0,230,118,0.5)]' : 'bg-[#00f0ff] shadow-[0_0_15px_rgba(0,240,255,0.5)]'
                    : 'bg-white/20 group-hover:bg-white/40'
                }`}
              ></div>
              
              <div className={`transition-all ${event.current ? 'opacity-100' : 'opacity-60 group-hover:opacity-100'}`}>
                <div className="flex items-center space-x-3 mb-1">
                  <span className={`font-mono text-xs px-2 py-1 rounded bg-white/5 ${
                    event.current 
                      ? filter === 'Energy' ? 'text-[#00e676]' : 'text-[#00f0ff]'
                      : 'text-gray-400'
                  }`}>
                    {event.time}
                  </span>
                  <h3 className="text-lg font-medium text-white">{event.title}</h3>
                </div>
                <p className="text-gray-400 text-sm">{event.desc}</p>
                
                {event.current && (
                  <div className="mt-4 p-3 bg-black/30 rounded-lg border border-white/5 inline-block">
                    <span className="text-xs font-medium text-purple-400">Agent Note:</span>
                    <span className="text-xs text-gray-300 ml-2">High confidence execution based on previous 7 days of pattern data.</span>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </Glass>
    </div>
  );
}
