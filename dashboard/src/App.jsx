import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import { tokens } from './design-system';
import { useNestShiftStore } from './store/useNestShiftStore';
import { getHealth, getDevices, getEnergyUsage, getCurrentTariff, getAgentStatus } from './services/api';
import { createMqttClient } from './services/mqtt-ws';
import Home from './pages/Home';
import SmartSchedule from './pages/SmartSchedule';
import Devices from './pages/Devices';
import Energy from './pages/Energy';
import Settings from './pages/Settings';
import Onboarding from './pages/Onboarding';

function AppContent() {
  const location = useLocation();
  const { setApiConnected, setMqttConnected, setDevices, setEnergyUsage, setCurrentTariff, setAgentStatus, isOnboarded } = useNestShiftStore();

  useEffect(() => {
    // Only load data if onboarded (simulates OS booting up after setup)
    if (!isOnboarded) return;

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
  }, [isOnboarded]);

  const navItems = [
    { path: '/', icon: '🏠', label: 'Home' },
    { path: '/schedule', icon: '⏱️', label: 'Schedule' },
    { path: '/devices', icon: '💡', label: 'Devices' },
    { path: '/energy', icon: '⚡', label: 'Energy' },
    { path: '/settings', icon: '⚙️', label: 'Settings' },
  ];

  if (!isOnboarded) {
    return <Onboarding />;
  }

  return (
    <div className="flex min-h-screen text-slate-100 font-sans selection:bg-cyan-500/30">
      {/* Fixed Left Sidebar */}
      <aside 
        className="w-64 fixed top-0 bottom-0 left-0 border-r z-50 flex flex-col" 
        style={{ 
          borderColor: tokens.colors.border, 
          backgroundColor: tokens.colors.glass.bg, 
          backdropFilter: `blur(${tokens.colors.glass.blur})` 
        }}
      >
        <div className="p-6 pb-2">
          {/* Logo / Brand Header */}
          <div className="flex items-center space-x-3 mb-10">
            <div 
              className="w-8 h-8 rounded-full shadow-lg" 
              style={{ 
                background: `linear-gradient(135deg, ${tokens.colors.accent.primary}, ${tokens.colors.accent.ai})`,
                boxShadow: tokens.shadow.glow.primary
              }}
            ></div>
            <div>
              <h1 className="text-lg font-bold tracking-tight text-white leading-tight">NestShift</h1>
              <p className="text-xs" style={{ color: tokens.colors.text.secondary }}>Personal AI Hub</p>
            </div>
          </div>

          {/* Navigation Menu */}
          <nav className="space-y-1">
            {navItems.map((item) => {
              const active = location.pathname === item.path;
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className="flex items-center space-x-3 px-4 py-3 rounded-lg transition-all duration-300 relative overflow-hidden group"
                  style={{
                    backgroundColor: active ? 'rgba(255,255,255,0.03)' : 'transparent',
                    color: active ? '#ffffff' : tokens.colors.text.secondary
                  }}
                >
                  {/* Left glowing active state indicator */}
                  {active && (
                    <div 
                      className="absolute left-0 top-0 bottom-0 w-1"
                      style={{ 
                        backgroundColor: tokens.colors.accent.energy,
                        boxShadow: `0 0 10px ${tokens.colors.accent.energy}`
                      }}
                    ></div>
                  )}
                  {/* Hover background for non-active */}
                  {!active && (
                    <div className="absolute inset-0 bg-white/5 opacity-0 group-hover:opacity-100 transition-opacity"></div>
                  )}
                  
                  <span className="text-xl relative z-10">{item.icon}</span>
                  <span className={`font-medium text-sm relative z-10 ${active ? 'tracking-wide' : ''}`}>{item.label}</span>
                </Link>
              );
            })}
          </nav>
        </div>
        
        {/* Bottom Profile / Settings shortcut in sidebar */}
        <div className="mt-auto p-6 border-t" style={{ borderColor: tokens.colors.border }}>
          <div className="flex items-center space-x-3">
             <div className="w-8 h-8 flex items-center justify-center rounded-full border border-gray-600 bg-gray-800">
               👤
             </div>
             <div>
               <div className="text-sm font-semibold text-white">NestShift Admin</div>
               <div className="text-xs" style={{ color: tokens.colors.accent.primary }}>System Active</div>
             </div>
          </div>
        </div>
      </aside>

      {/* Main Content Container (shifted right by sidebar width) */}
      <main className="flex-1 ml-64 p-8 relative z-10 min-h-screen">
        <div className="max-w-7xl mx-auto">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/schedule" element={<SmartSchedule />} />
            <Route path="/devices" element={<Devices />} />
            <Route path="/energy" element={<Energy />} />
            <Route path="/settings" element={<Settings />} />
          </Routes>
        </div>
      </main>
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