/**
 * NextBelt Design System - Extracted from styles-new.css
 * Industrial aesthetic with teal + copper palette
 */

export const theme = {
  colors: {
    // Primary - Deep industrial teal
    primary: '#0D4F4F',
    primaryLight: '#1A6B6B',
    primaryDark: '#083A3A',
    
    // Accent - Warm copper/orange
    accent: '#C65D3B',
    accentLight: '#E07A5A',
    accentDark: '#A04A2E',
    
    // Neutrals - Warm grays
    text: '#1A1A1A',
    textSecondary: '#5C5C5C',
    textMuted: '#8A8A8A',
    bg: '#FAFAF8',
    bgAlt: '#F2F1EE',
    bgDark: '#1A1A1A',
    border: '#E5E4E0',
    borderDark: '#D1D0CC',
    
    // Status colors
    success: '#2D6A4F',
    warning: '#B5830B',
    error: '#9B2C2C',
    
    // Whites
    white: '#FFFFFF',
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
      primary: "'Space Grotesk', -apple-system, BlinkMacSystemFont, sans-serif",
      mono: "'IBM Plex Mono', monospace",
    },
    fontSize: {
      xs: '0.75rem',    // 12px
      sm: '0.875rem',   // 14px
      base: '1rem',     // 16px
      lg: '1.125rem',   // 18px
      xl: '1.25rem',    // 20px
      '2xl': '1.5rem',  // 24px
      '3xl': '2rem',    // 32px
      '4xl': '2.5rem',  // 40px
      '5xl': '3.5rem',  // 56px
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
    sm: '4px',
    md: '8px',
    lg: '12px',
  },
  
  shadows: {
    sm: '0 1px 3px rgba(0,0,0,0.06)',
    md: '0 4px 20px rgba(0,0,0,0.06)',
    lg: '0 8px 30px rgba(0,0,0,0.12)',
    xl: '0 8px 30px rgba(13, 79, 79, 0.08)',
  },
  
  transition: '0.2s ease',
};

export type Theme = typeof theme;
