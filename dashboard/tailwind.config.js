/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        orbit: {
          bg: '#0a0a0f',
          card: '#12121a',
          border: '#1e1e2e',
          cyan: '#00f5d4',
          'cyan-dim': '#00f5d440',
          red: '#ff6b6b',
          yellow: '#ffd93d',
          green: '#00f5d4'
        }
      }
    },
  },
  plugins: [],
}