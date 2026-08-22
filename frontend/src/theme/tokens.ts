export const tokens = {
  colors: {
    bg: '#0d0d0d',
    surface: '#111111',
    surface2: '#1a1a1a',
    border: '#2a2a2a',
    borderHi: '#3a3a3a',
    text: '#e4e4e4',
    muted: '#666666',
    accent: '#00ff88',
    accentDim: 'rgba(0, 255, 136, 0.12)',
    accentGlow: 'rgba(0, 255, 136, 0.08)',
    red: '#ff5f57',
    yellow: '#ffbd2e',
    green: '#28ca41',
    userBg: '#1a1a2e',
    userBorder: '#2d2d4a',
  },
  typography: {
    fontFamily: "'JetBrains Mono', 'Fira Code', 'Cascadia Code', monospace",
    fontSizeBase: '20px',
    fontSizeSm: '0.75rem',
    fontSizeMd: '0.85rem',
    fontSizeLg: '1rem',
  },
  radii: {
    sm: '4px',
    md: '6px',
    lg: '8px',
    full: '9999px',
  },
  transitions: {
    fast: 'all 0.15s ease',
    normal: 'all 0.25s ease',
  }
} as const;

export type ThemeTokens = typeof tokens;
