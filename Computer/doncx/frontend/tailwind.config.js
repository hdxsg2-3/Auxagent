/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: '#7C3AED',
        'primary-hover': '#6D28D9',
        'primary-light': '#F5F3FF',
        'primary-glow': 'rgba(124, 58, 237, 0.3)',
        secondary: '#8B5CF6',
        accent: '#A78BFA',
        'accent-light': '#C4B5FD',
        'bg-sidebar': '#0A0615',
        'bg-content': '#FDFBFF',
        'card-bg': 'rgba(255, 255, 255, 0.92)',
        border: '#EDE9FE',
        'text-primary': '#1A1525',
        'text-secondary': '#5C5470',
        'text-muted': '#9B95A5',
      },
      boxShadow: {
        'sm': '0 1px 3px rgba(124, 58, 237, 0.04)',
        'md': '0 4px 16px rgba(124, 58, 237, 0.08)',
        'lg': '0 8px 32px rgba(124, 58, 237, 0.12)',
        'xl': '0 16px 48px rgba(124, 58, 237, 0.16)',
      },
      borderRadius: {
        'sm': '8px',
        'md': '12px',
        'lg': '16px',
        'xl': '24px',
      },
      fontFamily: {
        sans: ['Inter', 'Noto Sans SC', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
