/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'bio-dark': '#0f1419',
        'bio-darker': '#0a0e12',
        'bio-accent': '#00d4aa',
        'bio-accent-dark': '#009d7f',
        'bio-purple': '#8b5cf6',
        'bio-danger': '#ef4444',
      },
      animation: {
        'pulse-glow': 'pulse-glow 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
      keyframes: {
        'pulse-glow': {
          '0%, 100%': { opacity: '1', boxShadow: '0 0 0 0 rgba(0, 212, 170, 0.7)' },
          '50%': { opacity: '0.8', boxShadow: '0 0 0 10px rgba(0, 212, 170, 0)' },
        },
      },
    },
  },
  plugins: [],
}
