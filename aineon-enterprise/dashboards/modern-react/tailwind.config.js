/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'aineon-dark': '#0a0e27',
        'aineon-blue': '#3b82f6',
        'aineon-green': '#10b981',
        'aineon-red': '#ef4444',
        'aineon-purple': '#8b5cf6',
      },
      fontFamily: {
        'sans': ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
