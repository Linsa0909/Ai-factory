/** @type {import('tailwindcss').Config} */
module.exports = {
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter var', 'Inter', 'Geist', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      colors: {
        linear: {
          bg: '#000000',
          card: 'rgba(24, 24, 27, 0.5)',
          border: '#27272a',
          'border-hover': '#3f3f46',
          fg: '#fafafa',
          muted: '#71717a',
          accent: '#6366f1',
          danger: '#ef4444',
          success: '#22c55e',
          warning: '#f59e0b',
        },
      },
      borderRadius: {
        xl: '16px',
        '2xl': '20px',
      },
      boxShadow: {
        glow: '0 0 20px -5px rgba(99, 102, 241, 0.1)',
        'glow-lg': '0 0 40px -10px rgba(99, 102, 241, 0.15)',
      },
      backgroundImage: {
        'micro-dots': 'radial-gradient(#27272a 1px, transparent 1px)',
      },
      backgroundSize: {
        'micro-dots': '16px 16px',
      },
      animation: {
        'fade-in': 'fadeIn 0.2s ease-out',
        'slide-up': 'slideUp 0.3s ease-out',
        'scale-in': 'scaleIn 0.2s ease-out',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(8px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        scaleIn: {
          '0%': { opacity: '0', transform: 'scale(0.97)' },
          '100%': { opacity: '1', transform: 'scale(1)' },
        },
      },
    },
  },
  plugins: [],
};
