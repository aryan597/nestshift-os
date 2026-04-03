import React from 'react';
import { tokens } from './tokens.js';

export const Glass = ({ children, className = '', onClick, ...props }) => {
  return (
    <div
      className={`backdrop-blur-xl saturate-150 ${className}`}
      style={{
        background: tokens.colors.glass.bg,
        border: `1px solid ${tokens.colors.glass.border}`,
        borderRadius: tokens.radius.lg,
      }}
      onClick={onClick}
      {...props}
    >
      {children}
    </div>
  );
};