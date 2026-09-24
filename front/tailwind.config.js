/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        apple: {
          bg: '#F5F5F7',
          card: '#FFFFFF',
          border: 'rgba(0, 0, 0, 0.08)',
          textPrimary: '#1D1D1F',
          textSecondary: '#86868B',
          accent: '#0071E3',
          accentHover: '#0077ED'
        }
      },
      borderRadius: {
        'apple': '12px',
        'apple-lg': '18px'
      },
      backdropBlur: {
        'apple': '20px'
      }
    },
  },
  plugins: [],
}
