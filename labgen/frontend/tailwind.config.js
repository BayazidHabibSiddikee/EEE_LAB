/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        cyber: {
          bg: '#0f172a',
          surface: '#1e293b',
          border: '#334155',
          primary: '#3b82f6',
          secondary: '#6366f1',
          accent: '#8b5cf6',
          warning: '#ef4444',
          text: '#f8fafc',
          textDim: '#94a3b8',
          scanline: 'rgba(59, 130, 246, 0.03)',
        },
      },
      fontFamily: {
        mono: ['JetBrains Mono', 'Fira Code', 'Consolas', 'monospace'],
        display: ['Orbitron', 'Rajdhani', 'sans-serif'],
        ui: ['Space Grotesk', 'Inter', 'sans-serif'],
      },
      animation: {
        'pulse-slow': 'pulse 4s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
      boxShadow: {
        'glow': '0 0 20px rgba(0, 255, 200, 0.3), 0 0 40px rgba(0, 255, 200, 0.1)',
        'glow-secondary': '0 0 20px rgba(255, 0, 110, 0.3), 0 0 40px rgba(255, 0, 110, 0.1)',
        'inner-glow': 'inset 0 0 20px rgba(0, 255, 200, 0.1)',
      },
    },
  },
  plugins: [],
}