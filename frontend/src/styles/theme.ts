/**
 * NextBelt Design System — Clean Enterprise
 * Neutral whites · cool grays · teal accent
 * Inspired by SMMS Enterprise
 */

export const theme = {
  colors: {
    // Primary — Teal
    primary: '#0F6F6F',
    primaryLight: '#1A8A8A',
    primaryDark: '#0A4E4E',
    primaryGlow: 'rgba(15, 111, 111, 0.08)',
    
    // Accent — Copper (secondary CTA)
    accent: '#C0603F',
    accentLight: '#D4714F',
    accentDark: '#9A4A2E',
    accentGlow: 'rgba(192, 96, 63, 0.08)',
    
    // Surfaces — pure white + neutral gray
    bgBase: '#FAFAFA',
    bgRaised: '#FFFFFF',
    bgCard: '#FFFFFF',
    bgCardHover: '#F5F5F5',
    bgSurface: '#F0F0F0',
    bgInput: '#FFFFFF',
    
    // Text — neutral dark
    text: '#333333',
    textSecondary: '#666666',
    textMuted: '#999999',
    textHeading: '#1A1A1A',
    
    // Borders — cool gray
    border: '#E5E5E5',
    borderHover: '#D0D0D0',
    borderActive: 'rgba(15, 111, 111, 0.5)',
    
    // Status colors
    success: '#0D8A5E',
    successBg: 'rgba(13, 138, 94, 0.06)',
    warning: '#B8860B',
    warningBg: 'rgba(184, 134, 11, 0.06)',
    error: '#C53030',
    errorBg: 'rgba(197, 48, 48, 0.05)',
    
    // Glass
    glassBg: 'rgba(255, 255, 255, 0.92)',
    glassBorder: '#E5E5E5',
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
      mono: "'IBM Plex Mono', monospace",
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
    sm: '4px',
    md: '8px',
    lg: '12px',
    xl: '16px',
  },
  
  shadows: {
    sm: '0 1px 2px rgba(0, 0, 0, 0.05)',
    md: '0 2px 8px rgba(0, 0, 0, 0.06)',
    lg: '0 4px 16px rgba(0, 0, 0, 0.08)',
    glow: '0 0 20px rgba(15, 111, 111, 0.05)',
    glowAccent: '0 0 20px rgba(192, 96, 63, 0.05)',
  },
  
  transition: '0.2s ease',
};

export type Theme = typeof theme;
