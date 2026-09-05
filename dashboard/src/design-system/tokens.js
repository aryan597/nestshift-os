export const tokens = {
  colors: {
    bg: {
      base: '#0a0a0f',
      surface: '#12121a',
      elevated: '#1a1a28',
      overlay: 'rgba(255,255,255,0.04)',
    },
    accent: {
      primary: '#00f5d4',    // neon cyan - OrbitAI primary
      secondary: '#7b2fff',  // electric purple - OrbitAI secondary
      energy: '#10b981',     // green — cost savings
      warning: '#ffb800',    // amber — price spikes / alerts
      danger: '#ff3d3d',     // red — safety / errors
      ai: '#a78bfa',         // violet — AI decisions
    },
    text: {
      primary: '#f1f5f9',
      secondary: '#94a3b8',
      muted: '#475569',
    },
    border: 'rgba(0,245,212,0.15)',
    glass: {
      bg: 'rgba(255,255,255,0.05)',
      border: 'rgba(0,245,212,0.15)',
      blur: '12px',
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
      primary: '0 0 20px rgba(0,245,212,0.3)',
      secondary: '0 0 20px rgba(123,47,255,0.3)',
      energy: '0 0 20px rgba(16,185,129,0.3)',
      warning: '0 0 20px rgba(255,184,0,0.3)',
    }
  }
};