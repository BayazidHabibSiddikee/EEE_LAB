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
        'scanline': 'scanline 8s linear infinite',
        'float': 'float 6s ease-in-out infinite',
        'pulse-slow': 'pulse 4s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'glitch': 'glitch 3s infinite',
        'radar': 'radar 10s linear infinite',
        'typing': 'typing 3.5s steps(40, end), blink .75s step-end infinite',
        'boot': 'boot 1s ease-out forwards',
      },
      keyframes: {
        scanline: {
          '0%': { transform: 'translateY(-100%)' },
          '100%': { transform: 'translateY(100%)' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0px) rotate(0deg)' },
          '50%': { transform: 'translateY(-20px) rotate(2deg)' },
        },
        glitch: {
          '0%, 90%, 100%': { transform: 'translateX(0)' },
          '92%': { transform: 'translateX(-2px)' },
          '94%': { transform: 'translateX(2px)' },
          '96%': { transform: 'translateX(-1px)' },
          '98%': { transform: 'translateX(1px)' },
        },
        radar: {
          '0%': { transform: 'rotate(0deg)' },
          '100%': { transform: 'rotate(360deg)' },
        },
        typing: {
          'from': { width: '0' },
          'to': { width: '100%' },
        },
        blink: {
          '50%': { borderColor: 'transparent' },
        },
        boot: {
          '0%': { opacity: '0', transform: 'translateY(20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
      boxShadow: {
        'glow': '0 0 20px rgba(0, 255, 200, 0.3), 0 0 40px rgba(0, 255, 200, 0.1)',
        'glow-secondary': '0 0 20px rgba(255, 0, 110, 0.3), 0 0 40px rgba(255, 0, 110, 0.1)',
        'inner-glow': 'inset 0 0 20px rgba(0, 255, 200, 0.1)',
      },
      backgroundImage: {
        'grid-pattern': 'linear-gradient(rgba(0, 255, 200, 0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(0, 255, 200, 0.03) 1px, transparent 1px)',
        'radial-glow': 'radial-gradient(ellipse at center, rgba(0, 255, 200, 0.1) 0%, transparent 70%)',
      },
    },
  },
  plugins: [],
}