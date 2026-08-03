import type { Config } from 'tailwindcss';

const config: Config = {
  content: [
    './app/**/*.{js,ts,jsx,tsx}',
    './components/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        surface: '#161616',
        accent: '#FFB703',
        success: '#10B981',
        warning: '#F59E0B',
        danger: '#EF4444',
        border: '#262626',
      },
      boxShadow: {
        glow: '0 20px 60px rgba(255, 183, 3, 0.12)',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
};

export default config;
