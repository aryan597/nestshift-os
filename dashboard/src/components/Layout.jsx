import { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { useMQTT } from './hooks/useMQTT'

const navItems = [
  { path: '/', label: 'Overview', icon: '◉' },
  { path: '/brain', label: 'Brain', icon: '◈' },
  { path: '/energy', label: 'Energy', icon: '⚡' },
  { path: '/devices', label: 'Devices', icon: '▦' },
  { path: '/safety', label: 'Safety', icon: '◈' },
]

export default function Layout({ children }) {
  const location = useLocation()
  const { status } = useMQTT()
  const [sidebarOpen, setSidebarOpen] = useState(true)

  return (
    <div className="flex min-h-screen">
      {/* Sidebar */}
      <aside className={`${sidebarOpen ? 'w-56' : 'w-16'} bg-orbit-card border-r border-orbit-border transition-all duration-300 flex flex-col`}>
        {/* Logo */}
        <div className="p-4 border-b border-orbit-border">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded bg-orbit-cyan flex items-center justify-center text-orbit-bg font-bold">N</div>
            {sidebarOpen && <span className="text-orbit-cyan font-semibold">NestShift</span>}
          </div>
        </div>

        {/* Nav */}
        <nav className="flex-1 p-2">
          {navItems.map(item => (
            <Link
              key={item.path}
              to={item.path}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg mb-1 transition-colors ${
                location.pathname === item.path
                  ? 'bg-orbit-cyan-dim text-orbit-cyan'
                  : 'text-gray-400 hover:bg-orbit-border hover:text-white'
              }`}
            >
              <span className="text-lg">{item.icon}</span>
              {sidebarOpen && <span>{item.label}</span>}
            </Link>
          ))}
        </nav>

        {/* MQTT Status */}
        <div className="p-4 border-t border-orbit-border">
          <div className="flex items-center gap-2">
            <span className={`w-2 h-2 rounded-full ${status === 'connected' ? 'bg-orbit-green animate-pulse' : 'bg-orbit-red'}`} />
            {sidebarOpen && <span className="text-xs text-gray-500">{status}</span>}
          </div>
        </div>
      </aside>

      {/* Main */}
      <main className="flex-1 p-6 overflow-auto">
        {children}
      </main>
    </div>
  )
}