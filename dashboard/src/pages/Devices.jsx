import React, { useState } from 'react';
import { Glass } from '../design-system';
import { useNestShiftStore } from '../store/useNestShiftStore';

export default function Devices() {
  const { devices } = useNestShiftStore();
  const [searchTerm, setSearchTerm] = useState('');

  const filteredDevices = devices.filter(device =>
    device.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="min-h-screen bg-gray-900 text-white p-4">
      <h1 className="text-2xl font-bold mb-6">Devices</h1>

      {/* Search Bar */}
      <Glass className="p-4 mb-6">
        <input
          type="text"
          placeholder="Search devices..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-full p-2 bg-transparent border rounded"
        />
      </Glass>

      {/* Device Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredDevices.map((device) => (
          <Glass key={device.id} className="p-4">
            <div className="text-3xl mb-2">{device.type === 'light' ? '💡' : '🔌'}</div>
            <h3 className="text-lg font-semibold">{device.name}</h3>
            <p className="text-sm mb-2">State: {device.state}</p>
            <pre className="text-xs bg-gray-800 p-2 rounded overflow-x-auto">
              {JSON.stringify(device, null, 2)}
            </pre>
            <button className="mt-2 px-4 py-2 bg-blue-500 rounded">Toggle</button>
          </Glass>
        ))}
      </div>

      <button className="mt-6 px-4 py-2 bg-green-500 rounded">Add Device (Coming Soon)</button>
    </div>
  );
}