/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#3498db',
          dark: '#2980b9',
        },
        secondary: {
          DEFAULT: '#2c3e50',
          dark: '#34495e',
        },
        success: '#27ae60',
        'success-dark': '#229954',
        danger: '#dc3545',
        warning: '#fbbf24',
        purple: {
          DEFAULT: '#9b59b6',
          dark: '#8e44ad',
        },
      },
      fontFamily: {
        sans: ['-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'sans-serif'],
        mono: ['Monaco', 'Menlo', 'Ubuntu Mono', 'Courier New', 'monospace'],
      },
    },
  },
  plugins: [],
}
