import React, { useState, useEffect } from 'react';
import useSystemReady from '../hooks/useSystemReady';

const BootScreen = ({ onReady }) => {
  const { nestshiftReady, haReady, allReady } = useSystemReady();
  const [minTimePassed, setMinTimePassed] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => setMinTimePassed(true), 2000);
    return () => clearTimeout(timer);
  }, []);

  useEffect(() => {
    if (allReady && minTimePassed) {
      setTimeout(onReady, 500); // Smooth fade
    }
  }, [allReady, minTimePassed, onReady]);

  const getStatusIcon = (ready) => ready ? '✓' : '●';

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      width: '100vw',
      height: '100vh',
      backgroundColor: 'black',
      display: 'flex',
      flexDirection: 'column',
      justifyContent: 'center',
      alignItems: 'center',
      fontFamily: 'system-ui, sans-serif',
      color: 'white',
      zIndex: 1000,
    }}>
      <h1 style={{
        fontSize: '4rem',
        fontWeight: 'bold',
        marginBottom: '2rem',
        letterSpacing: '0.1em',
      }}>
        NESTSHIFT
      </h1>
      
      <div style={{
        fontSize: '1.5rem',
        lineHeight: '2.5',
        textAlign: 'center',
      }}>
        <div>
          {getStatusIcon(nestshiftReady)} Energy Brain
        </div>
        <div>
          {getStatusIcon(haReady)} Device Hub
        </div>
        <div>
          {getStatusIcon(nestshiftReady)} Automation Engine
        </div>
        {!allReady && (
          <div style={{
            animation: 'pulse 1.5s infinite',
            marginTop: '1rem',
            opacity: 0.7,
          }}>
            ● Connecting...
          </div>
        )}
      </div>
      
      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 0.7; }
          50% { opacity: 1; }
        }
      `}</style>
    </div>
  );
};

export default BootScreen;