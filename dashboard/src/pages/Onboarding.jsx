import React, { useState, useEffect } from 'react';
import { useNestShiftStore } from '../store/useNestShiftStore';
import { tokens, Glass } from '../design-system';

export default function Onboarding() {
  const [step, setStep] = useState(1);
  const setIsOnboarded = useNestShiftStore((state) => state.setIsOnboarded);
  const [mockLoading, setMockLoading] = useState(false);

  const handleNext = () => setStep(step + 1);

  // Step 1: Wi-Fi setup
  const renderWifiSetup = () => (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="text-center space-y-2 mb-8">
        <h2 className="text-3xl font-bold tracking-tight">Connect to Wi-Fi</h2>
        <p className="text-gray-400">Your Hub needs an internet connection to sync with the cloud.</p>
      </div>
      <div className="space-y-3">
        {['Home_Network_5G', 'Home_Network_2G', 'Guest_Wifi'].map((net, i) => (
          <button 
            key={net}
            onClick={handleNext}
            className="w-full flex justify-between items-center p-4 rounded-xl border border-white/10 hover:border-cyan-500 hover:bg-white/5 transition-all"
          >
            <div className="flex items-center space-x-3">
              <span className="text-xl">📶</span>
              <span className="font-medium text-lg">{net}</span>
            </div>
            <span className="text-cyan-500 font-medium opacity-0 hover:opacity-100">Connect</span>
          </button>
        ))}
      </div>
    </div>
  );

  // Step 2: Login
  const renderLogin = () => (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="text-center space-y-2 mb-8">
        <h2 className="text-3xl font-bold tracking-tight">NestShift Account</h2>
        <p className="text-gray-400">Sign in to your pre-configured NestShift profile.</p>
      </div>
      <div className="space-y-4 max-w-sm mx-auto">
        <input 
          type="email" 
          placeholder="Email address" 
          className="w-full bg-black/40 border border-white/10 rounded-xl py-3 px-4 text-white focus:outline-none focus:border-cyan-500 transition-colors"
          defaultValue="admin@nestshift.com"
        />
        <input 
          type="password" 
          placeholder="Password" 
          className="w-full bg-black/40 border border-white/10 rounded-xl py-3 px-4 text-white focus:outline-none focus:border-cyan-500 transition-colors"
          defaultValue="********"
        />
        <button 
          onClick={handleNext}
          className="w-full bg-gradient-to-r from-cyan-500 to-blue-500 text-white font-semibold py-3 rounded-xl shadow-[0_0_15px_rgba(0,240,255,0.3)] hover:opacity-90 transition-opacity"
        >
          Sign In
        </button>
      </div>
    </div>
  );

  // Step 3: App Pair
  const renderPairing = () => (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500 text-center">
      <div className="space-y-2 mb-4">
        <h2 className="text-3xl font-bold tracking-tight">Pair Mobile App</h2>
        <p className="text-gray-400">Scan this QR code with the NestShift mobile app to securely link your device.</p>
      </div>
      
      <div className="inline-block p-4 bg-white rounded-2xl mx-auto shadow-[0_0_40px_rgba(255,255,255,0.1)]">
        {/* Placeholder for actual QR */}
        <div className="w-48 h-48 bg-gray-200 grid grid-cols-4 grid-rows-4 gap-1 p-2 rounded-lg">
          {Array(16).fill(0).map((_, i) => (
            <div key={i} className={`bg-black rounded-sm ${Math.random() > 0.5 ? 'opacity-100' : 'opacity-0'}`}></div>
          ))}
        </div>
      </div>
      
      <div className="pt-8">
        <button 
          onClick={handleNext}
          className="px-6 py-2 rounded-full border border-gray-600 hover:border-white text-gray-400 hover:text-white transition-colors text-sm"
        >
          [DEV] Simulate App Scan Success
        </button>
      </div>
    </div>
  );

  // Step 4: Hardware Config
  const renderHardware = () => (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500 w-full max-w-2xl mx-auto">
      <div className="text-center space-y-2 mb-8">
        <h2 className="text-3xl font-bold tracking-tight">Hardware Configuration</h2>
        <p className="text-gray-400">Verify discovered Zigbee devices and map physical GPIO relays.</p>
      </div>
      
      <div className="bg-black/30 border border-white/5 rounded-2xl overflow-hidden text-sm">
        <table className="w-full text-left">
          <thead className="bg-[#0f131a] border-b border-white/5">
            <tr>
              <th className="px-4 py-3 text-gray-400 font-medium">Device Name</th>
              <th className="px-4 py-3 text-gray-400 font-medium">Protocol</th>
              <th className="px-4 py-3 text-gray-400 font-medium">Pin / Address</th>
              <th className="px-4 py-3 text-gray-400 font-medium">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5">
            <tr className="hover:bg-white/5">
              <td className="px-4 py-3 font-medium">Living Room Bulb</td>
              <td className="px-4 py-3 text-cyan-500">Zigbee</td>
              <td className="px-4 py-3 text-gray-500">0x00158D...</td>
              <td className="px-4 py-3 text-green-500">Paired</td>
            </tr>
            <tr className="hover:bg-white/5">
              <td className="px-4 py-3 font-medium">Main HVAC Relay</td>
              <td className="px-4 py-3 text-purple-400">GPIO</td>
              <td className="px-4 py-3">
                <select className="bg-transparent border border-white/20 rounded px-2 py-1 outline-none text-white focus:border-cyan-500">
                  <option>Pin 17</option>
                  <option>Pin 27</option>
                  <option>Pin 22</option>
                </select>
              </td>
              <td className="px-4 py-3 text-green-500">Active</td>
            </tr>
            <tr className="hover:bg-white/5">
              <td className="px-4 py-3 font-medium">Water Heater Base</td>
              <td className="px-4 py-3 text-purple-400">GPIO</td>
              <td className="px-4 py-3">
                <select className="bg-transparent border border-white/20 rounded px-2 py-1 outline-none text-white focus:border-cyan-500">
                  <option>Pin 27</option>
                  <option>Pin 17</option>
                  <option>Pin 22</option>
                </select>
              </td>
              <td className="px-4 py-3 text-green-500">Active</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div className="flex justify-end pt-4">
        <button 
          onClick={handleNext}
          className="px-8 py-3 bg-white text-black font-semibold rounded-xl hover:bg-gray-200 transition-colors"
        >
          Confirm Connections
        </button>
      </div>
    </div>
  );

  // Step 5: Loading / Finish
  const renderLoading = () => {
    if (!mockLoading) {
      setMockLoading(true);
      setTimeout(() => {
        setIsOnboarded(true); // Triggers App to render main dashboard
      }, 5000); // 5 seconds dev mode load
    }

    return (
      <div className="flex flex-col items-center justify-center space-y-8 animate-in fade-in duration-1000 h-64">
        <div className="relative w-24 h-24">
          <div className="absolute inset-0 border-4 border-white/10 rounded-full"></div>
          <div className="absolute inset-0 border-4 border-cyan-500 rounded-full border-t-transparent animate-spin"></div>
        </div>
        <div className="text-center space-y-2">
          <h2 className="text-2xl font-bold tracking-tight text-white mb-2">Setting up your NestShift OS...</h2>
          <p className="text-cyan-500 animate-pulse font-medium text-sm">Compiling AI Models</p>
          <p className="text-gray-500 text-xs">This normally takes 5 minutes, accelerated for dev mode.</p>
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-[#080b12] text-slate-100 font-sans flex items-center justify-center relative overflow-hidden" style={{ backgroundImage: 'radial-gradient(circle at 50% 0%, #151a28 0%, #080b12 50%)' }}>
      
      {/* Decorative Background Elements */}
      <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] rounded-full bg-cyan-500/10 blur-[120px] pointer-events-none"></div>
      <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] rounded-full bg-purple-500/10 blur-[120px] pointer-events-none"></div>

      {/* Main Glass Panel */}
      <Glass className="w-full max-w-4xl min-h-[500px] p-12 flex flex-col items-center justify-center relative z-10 shadow-2xl">
        {step === 1 && renderWifiSetup()}
        {step === 2 && renderLogin()}
        {step === 3 && renderPairing()}
        {step === 4 && renderHardware()}
        {step === 5 && renderLoading()}
      </Glass>
    </div>
  );
}
