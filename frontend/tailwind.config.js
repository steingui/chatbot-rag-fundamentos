/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Plus Jakarta Sans', '-apple-system', 'BlinkMacSystemFont', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      colors: {
        surface: {
          bg: '#F4F4F6',
          card: '#FFFFFF',
        },
        lime: {
          500: '#52C443',
          600: '#45B037',
        }
      }
    },
  },
  plugins: [],
}
