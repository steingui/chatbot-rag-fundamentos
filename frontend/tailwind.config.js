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
        canvas: 'var(--color-canvas)',
        surface: 'var(--color-surface)',
        card: 'var(--color-card)',
        border: 'var(--color-border)',
        'border-strong': 'var(--color-border-strong)',
        ink: 'var(--color-ink)',
        'ink-muted': 'var(--color-ink-muted)',
        accent: 'var(--color-accent)',
        'accent-strong': 'var(--color-accent-strong)',
        'accent-ink': 'var(--color-accent-ink)',
        warning: 'var(--color-warning)',
        danger: 'var(--color-danger)',
        'danger-strong': 'var(--color-danger-strong)',
      },
      borderRadius: {
        sm: 'var(--radius-sm)',
        md: 'var(--radius-md)',
        lg: 'var(--radius-lg)',
        xl: 'var(--radius-xl)',
      },
      transitionTimingFunction: {
        spring: 'var(--ease-spring)',
      },
    },
  },
  plugins: [],
}
