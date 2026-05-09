export const tokens = {
  colors: {
    bg: {
      base: '#0a0a0f',
      surface: '#12121a',
      elevated: '#1a1a28',
      overlay: 'rgba(255,255,255,0.04)',
    },
    accent: {
      primary: '#6366f1',    // indigo
      energy: '#10b981',     // green — cost savings / efficiency
      warning: '#f59e0b',    // amber — price spikes / alerts
      danger: '#ef4444',     // red — safety / errors
      ai: '#a78bfa',         // violet — AI decisions / agent activity
    },
    text: {
      primary: '#f1f5f9',
      secondary: '#94a3b8',
      muted: '#475569',
    },
    border: 'rgba(255,255,255,0.08)',
    glass: {
      bg: 'rgba(255,255,255,0.05)',
      border: 'rgba(255,255,255,0.10)',
      blur: '20px',
    }
  },
  radius: {
    sm: '8px',
    md: '12px',
    lg: '20px',
    xl: '28px',
  },
  shadow: {
    glow: {
      primary: '0 0 20px rgba(99,102,241,0.3)',
      energy: '0 0 20px rgba(16,185,129,0.3)',
      warning: '0 0 20px rgba(245,158,11,0.3)',
    }
  }
}