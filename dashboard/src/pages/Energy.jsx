import React, { useState } from 'react';
import { Glass } from '../design-system';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import { useNestShiftStore } from '../store/useNestShiftStore';

export default function Energy() {
  const [period, setPeriod] = useState('Today');
  const { energyUsage } = useNestShiftStore();

  const periods = ['Today', '7 Days', '30 Days'];

  const chartData = energyUsage?.readings?.map((reading, index) => ({
    day: `Day ${index + 1}`,
    cost: reading.kwh * 0.28, // Mock cost calculation
  })) || [];

  return (
    <div className="min-h-screen bg-gray-900 text-white p-4">
      <h1 className="text-2xl font-bold mb-6">Energy Analytics</h1>

      {/* Period Selector */}
      <Glass className="p-4 mb-6">
        <div className="flex space-x-4">
          {periods.map((p) => (
            <button
              key={p}
              onClick={() => setPeriod(p)}
              className={`px-4 py-2 rounded ${period === p ? 'bg-blue-500' : 'bg-gray-700'}`}
            >
              {p}
            </button>
          ))}
        </div>
      </Glass>

      {/* Summary Row */}
      <Glass className="p-4 mb-6">
        <div className="grid grid-cols-4 gap-4 text-center">
          <div>
            <div className="text-2xl font-bold">{energyUsage?.total_kwh || 0} kWh</div>
            <div className="text-sm">Total Usage</div>
          </div>
          <div>
            <div className="text-2xl font-bold">£{(energyUsage?.cost_gbp || 0).toFixed(2)}</div>
            <div className="text-sm">Total Cost</div>
          </div>
          <div>
            <div className="text-2xl font-bold">£{(energyUsage?.savings_gbp || 0).toFixed(2)}</div>
            <div className="text-sm">Saved</div>
          </div>
          <div>
            <div className="text-2xl font-bold">28p/kWh</div>
            <div className="text-sm">Avg Price</div>
          </div>
        </div>
      </Glass>

      {/* Bar Chart */}
      <Glass className="p-4 mb-6">
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={chartData}>
            <XAxis dataKey="day" />
            <YAxis />
            <Tooltip />
            <Bar dataKey="cost" fill="#6366f1" />
          </BarChart>
        </ResponsiveContainer>
      </Glass>

      {/* Tariff Calendar */}
      <Glass className="p-4">
        <h2 className="text-lg font-semibold mb-4">Tariff Calendar</h2>
        <div className="grid grid-cols-24 gap-1">
          {Array.from({ length: 24 }, (_, i) => (
            <div
              key={i}
              className={`h-8 rounded ${
                i >= 7 && i <= 10 ? 'bg-amber-500' : i >= 17 && i <= 20 ? 'bg-red-500' : 'bg-green-500'
              }`}
              title={`${i}:00 - ${i + 1}:00`}
            ></div>
          ))}
        </div>
      </Glass>

      <button className="mt-6 px-4 py-2 bg-blue-500 rounded">Export Data</button>
    </div>
  );
}