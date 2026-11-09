/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        vnpt: {
          50: '#f0f7ff',
          100: '#e0effe',
          200: '#bae0fd',
          300: '#7cc5fb',
          400: '#38a5f8',
          500: '#0072bc', // VNPT Bright Blue
          600: '#0066cc', // VNPT Primary Blue
          700: '#0052a3', // VNPT Deep Blue
          800: '#004282',
          900: '#00386c',
        },
        brand: {
          50: '#f0f7ff',
          100: '#e0effe',
          500: '#0066cc',
          600: '#0056b3',
          700: '#004085',
        }
      },
      fontSize: {
        'readable-sm': '0.925rem',  // ~14.8px
        'readable-base': '1.05rem', // ~16.8px
        'readable-lg': '1.2rem',   // ~19.2px
      }
    },
  },
  plugins: [],
}

