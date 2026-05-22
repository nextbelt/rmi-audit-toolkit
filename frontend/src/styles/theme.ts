/**
 * RMI Audit Toolkit — Design Tokens
 * Cream surfaces · Pine accent · Serif headlines
 */

export const theme = {
  colors: {
    // Primary — Pine / teal
    primary: '#0E6E62',
    primaryLight: '#15877a',
    primaryDark: '#124d45',
    primaryGlow: 'rgba(14, 110, 98, 0.12)',

    // Accent — Clay (secondary)
    accent: '#C2533C',
    accentLight: '#D4714F',
    accentDark: '#9A3D2A',
    accentGlow: 'rgba(194, 83, 60, 0.10)',

    // Surfaces — cream + white
    bgBase: '#F6F4EF',
    bgRaised: '#FFFFFF',
    bgCard: '#FFFFFF',
    bgCardHover: '#FAF8F3',
    bgSurface: '#FAF8F3',
    bgInput: '#FFFFFF',

    // Text — ink scale
    text: '#1B1F1D',
    textSecondary: '#3C423F',
    textMuted: '#7A807D',
    textMutedSoft: '#9AA09D',
    textHeading: '#1B1F1D',

    // Borders — warm cream
    border: '#E6E2D8',
    borderSoft: '#ECE8DE',
    borderHover: '#9AA09D',
    borderActive: 'rgba(14, 110, 98, 0.5)',

    // Status
    success: '#2F8A6B',
    successBg: 'rgba(47, 138, 107, 0.10)',
    warning: '#C08A2E',
    warningBg: 'rgba(192, 138, 46, 0.10)',
    error: '#C2533C',
    errorBg: 'rgba(194, 83, 60, 0.08)',

    // Glass
    glassBg: 'rgba(255, 255, 255, 0.92)',
    glassBorder: '#E6E2D8',
  },

  spacing: {
    xs: '4px',
    sm: '8px',
    md: '16px',
    lg: '24px',
    xl: '40px',
    '2xl': '64px',
    '3xl': '100px',
  },

  typography: {
    fontFamily: {
      primary: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
      serif: "'Instrument Serif', serif",
      mono: "'JetBrains Mono', monospace",
    },
    fontSize: {
      xs: '0.75rem',
      sm: '0.875rem',
      base: '1rem',
      lg: '1.125rem',
      xl: '1.25rem',
      '2xl': '1.5rem',
      '3xl': '2rem',
      '4xl': '2.5rem',
      '5xl': '3.5rem',
    },
    fontWeight: {
      light: 300,
      normal: 400,
      medium: 500,
      semibold: 600,
      bold: 700,
    },
  },

  radius: {
    sm: '8px',
    md: '12px',
    lg: '16px',
    xl: '20px',
  },

  shadows: {
    sm: '0 1px 2px rgba(27, 31, 29, 0.04)',
    md: '0 2px 8px rgba(27, 31, 29, 0.06)',
    lg: '0 8px 30px rgba(27, 31, 29, 0.10)',
    glow: '0 0 20px rgba(14, 110, 98, 0.08)',
    glowAccent: '0 0 20px rgba(194, 83, 60, 0.08)',
  },

  transition: '0.15s ease',
};

export type Theme = typeof theme;
