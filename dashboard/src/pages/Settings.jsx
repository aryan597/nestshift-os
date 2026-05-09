import React from 'react';
import { Glass } from '../design-system';
import { useNestShiftStore } from '../store/useNestShiftStore';

export default function Settings() {
  const { agentStatus } = useNestShiftStore();

  return (
    <div className="min-h-screen bg-gray-900 text-white p-4">
      <h1 className="text-2xl font-bold mb-6">Settings</h1>

      {/* Agent Toggle Cards */}
      <Glass className="p-4 mb-6">
        <h2 className="text-lg font-semibold mb-4">Agent Control</h2>
        <div className="space-y-4">
          {['energy', 'automation', 'system'].map((agent) => (
            <div key={agent} className="flex justify-between items-center p-4 bg-gray-800 rounded">
              <span className="capitalize">{agent} Agent</span>
              <button className="px-4 py-2 bg-green-500 rounded">Toggle</button>
            </div>
          ))}
        </div>
      </Glass>

      {/* System Health */}
      <Glass className="p-4 mb-6">
        <h2 className="text-lg font-semibold mb-4">System Health</h2>
        <div className="space-y-4">
          <div>
            <div className="flex justify-between mb-1">
              <span>CPU</span>
              <span>{agentStatus?.system?.cpu_pct || 0}%</span>
            </div>
            <div className="w-full bg-gray-700 rounded-full h-2">
              <div
                className="bg-blue-500 h-2 rounded-full"
                style={{ width: `${agentStatus?.system?.cpu_pct || 0}%` }}
              ></div>
            </div>
          </div>
          <div>
            <div className="flex justify-between mb-1">
              <span>RAM</span>
              <span>{agentStatus?.system?.ram_pct || 0}%</span>
            </div>
            <div className="w-full bg-gray-700 rounded-full h-2">
              <div
                className="bg-blue-500 h-2 rounded-full"
                style={{ width: `${agentStatus?.system?.ram_pct || 0}%` }}
              ></div>
            </div>
          </div>
          <div>
            <div className="flex justify-between mb-1">
              <span>Storage</span>
              <span>{agentStatus?.system?.disk_pct || 0}%</span>
            </div>
            <div className="w-full bg-gray-700 rounded-full h-2">
              <div
                className="bg-blue-500 h-2 rounded-full"
                style={{ width: `${agentStatus?.system?.disk_pct || 0}%` }}
              ></div>
            </div>
          </div>
        </div>
      </Glass>

      {/* About */}
      <Glass className="p-4">
        <h2 className="text-lg font-semibold mb-4">About</h2>
        <div className="space-y-2">
          <p>Version: 0.2.0</p>
          <p>Hardware: Raspberry Pi / Dev</p>
          <p>Uptime: {Math.floor((Date.now() / 1000) / 3600)} hours</p>
        </div>
      </Glass>
    </div>
  );
}