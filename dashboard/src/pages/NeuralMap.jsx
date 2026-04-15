import React, { useMemo } from 'react';
import { motion } from 'framer-motion';
import { useNestShiftStore } from '../store/useNestShiftStore';
import Glass from '../design-system/Glass';

const NeuralMap = () => {
  const { devices, sensors, synapses } = useNestShiftStore();

  // Filter for devices and sensors that have active synapses
  const activeSynapses = useMemo(() => {
    // Mock synapses if none exist yet for visual demo
    return synapses?.length > 0 ? synapses : [
      { pre: 'hallway_motion', post: 'hallway_light', weight: 0.85 },
      { pre: 'kitchen_motion', post: 'kitchen_kettle', weight: 0.42 },
      { pre: 'front_door', post: 'foyer_light', weight: 0.98 },
    ];
  }, [synapses]);

  return (
    <div className="p-8 space-y-8 min-h-screen pb-24">
      <header>
        <h1 className="text-4xl font-bold text-white tracking-tight">Neural Map</h1>
        <p className="text-cyan-400/60 mt-2">Visualizing the synthetic synapses of your home.</p>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 relative">
        {/* Connection Lines (SVG Layer) */}
        <svg className="absolute inset-0 w-full h-full pointer-events-none z-0" style={{ minHeight: '600px' }}>
          {activeSynapses.map((synapse, i) => (
            <motion.line
              key={i}
              x1="20%"
              y1={`${20 + i * 25}%`}
              x2="80%"
              y2={`${20 + i * 25}%`}
              stroke="#00f0ff"
              strokeWidth={synapse.weight * 4}
              initial={{ pathLength: 0, opacity: 0 }}
              animate={{ pathLength: 1, opacity: synapse.weight * 0.8 }}
              transition={{ duration: 2, delay: i * 0.2 }}
              className="drop-shadow-[0_0_8px_rgba(0,240,255,0.5)]"
            />
          ))}
        </svg>

        {/* Sensory Cortex (Inputs) */}
        <div className="space-y-6 z-10">
          <h2 className="text-xs uppercase tracking-[0.2em] text-white/40 font-semibold mb-4">Sensory Cortex</h2>
          {['Hallway Motion', 'Kitchen Motion', 'Front Door'].map((sensor, i) => (
            <Glass key={i} className="p-4 flex items-center justify-between border-l-2 border-l-cyan-500">
              <span className="text-white font-medium">{sensor}</span>
              <div className="w-2 h-2 rounded-full bg-cyan-500 animate-pulse shadow-[0_0_10px_#00f0ff]" />
            </Glass>
          ))}
        </div>

        {/* The Thinking Gap */}
        <div className="flex flex-col items-center justify-center space-y-4">
            <div className="text-center">
                <motion.div 
                    animate={{ scale: [1, 1.1, 1], opacity: [0.3, 0.6, 0.3] }}
                    transition={{ duration: 4, repeat: Infinity }}
                    className="w-32 h-32 rounded-full border-2 border-dashed border-cyan-500/30 flex items-center justify-center"
                >
                    <span className="text-[10px] uppercase tracking-widest text-cyan-400/50">Neural Core</span>
                </motion.div>
            </div>
        </div>

        {/* Motor Cortex (Outputs) */}
        <div className="space-y-6 z-10">
          <h2 className="text-xs uppercase tracking-[0.2em] text-white/40 font-semibold mb-4 text-right">Motor Cortex</h2>
          {['Hallway Light', 'Kettle', 'Foyer Light'].map((device, i) => (
            <Glass key={i} className="p-4 flex items-center justify-between border-r-2 border-r-green-500">
              <div className="w-2 h-2 rounded-full bg-green-500/20" />
              <span className="text-white font-medium">{device}</span>
            </Glass>
          ))}
        </div>
      </div>

      {/* Explainer / Trace */}
      <Glass className="p-6 mt-12 bg-cyan-500/5 border-cyan-500/20">
        <h3 className="text-sm font-bold text-cyan-400 uppercase tracking-widest mb-4">Latest Neural Trace</h3>
        <div className="space-y-3 font-mono text-xs text-white/70">
          <p className="flex justify-between">
            <span className="text-white/40">[21:42:04]</span>
            <span>Synapse (Front Door → Foyer Light) spiked. Weight: 0.98.</span>
          </p>
          <p className="flex justify-between">
            <span className="text-white/40">[21:42:04]</span>
            <span className="text-green-400">Action: Foyer Light ON. Confidence: High.</span>
          </p>
          <p className="flex justify-between">
            <span className="text-white/40">[21:42:08]</span>
            <span>Threshold not met for (Kitchen Motion → Kettle). Weight: 0.42. Ignored.</span>
          </p>
        </div>
      </Glass>
    </div>
  );
};

export default NeuralMap;
