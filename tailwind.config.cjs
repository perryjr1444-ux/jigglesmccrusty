/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        backdrop: '#090b1a',
        surface: '#11152b',
        surfaceMuted: '#1a1f3f',
        accent: {
          DEFAULT: '#7b6eff',
          subtle: '#3d3dff',
          soft: '#a58bff'
        }
      },
      boxShadow: {
        glow: '0 0 20px rgba(123, 110, 255, 0.35)',
        card: '0 20px 45px rgba(0,0,0,0.45)'
      },
      fontFamily: {
        sans: ['"Inter"', 'system-ui', 'sans-serif']
      },
      backgroundImage: {
        mesh: 'radial-gradient(100% 100% at 0% 0%, rgba(123, 110, 255, 0.22) 0%, transparent 55%), radial-gradient(100% 130% at 100% 0%, rgba(0, 168, 255, 0.2) 0%, transparent 60%), radial-gradient(90% 100% at 50% 100%, rgba(255, 99, 132, 0.18) 0%, transparent 62%)'
      }
    }
  },
  plugins: []
};
