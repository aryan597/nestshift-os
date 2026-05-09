import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import { tokens } from './design-system';
import { useNestShiftStore } from './store/useNestShiftStore';
import { getHealth, getDevices, getEnergyUsage, getCurrentTariff, getAgentStatus } from './services/api';
import { createMqttClient } from './services/mqtt-ws';
import Home from './pages/Home';
import Devices from './pages/Devices';
import Energy from './pages/Energy';
import Settings from './pages/Settings';

function AppContent() {
  const location = useLocation();
  const { setApiConnected, setMqttConnected, setDevices, setEnergyUsage, setCurrentTariff, setAgentStatus } = useNestShiftStore();

  useEffect(() => {
    // Initialize API connection
    getHealth().then(() => setApiConnected(true)).catch(() => setApiConnected(false));

    // Initialize MQTT
    const mqttClient = createMqttClient();
    mqttClient.onConnectionChange(setMqttConnected);

    // Load initial data
    Promise.all([
      getDevices().then(setDevices).catch(console.error),
      getEnergyUsage().then(setEnergyUsage).catch(console.error),
      getCurrentTariff().then(setCurrentTariff).catch(console.error),
      getAgentStatus().then(setAgentStatus).catch(console.error),
    ]);

    return () => mqttClient.disconnect();
  }, []);

  const navItems = [
    { path: '/', icon: '🏠', label: 'Home' },
    { path: '/devices', icon: '💡', label: 'Devices' },
    { path: '/energy', icon: '⚡', label: 'Energy' },
    { path: '/settings', icon: '⚙️', label: 'Settings' },
  ];

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/devices" element={<Devices />} />
        <Route path="/energy" element={<Energy />} />
        <Route path="/settings" element={<Settings />} />
      </Routes>

      {/* Bottom Navigation */}
      <nav className="fixed bottom-0 left-0 right-0 bg-gray-800 border-t" style={{ borderColor: tokens.colors.border }}>
        <div className="flex justify-around">
          {navItems.map((item) => (
            <Link
              key={item.path}
              to={item.path}
              className={`flex flex-col items-center py-2 px-4 ${
                location.pathname === item.path ? 'text-blue-500' : 'text-gray-400'
              }`}
            >
              <span className="text-2xl">{item.icon}</span>
              <span className="text-xs">{item.label}</span>
            </Link>
          ))}
        </div>
      </nav>
    </div>
  );
}

function App() {
  return (
    <Router>
      <AppContent />
    </Router>
  );
}

export default App;