import React, { CSSProperties, ButtonHTMLAttributes } from 'react';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'text' | 'accent';
  size?: 'sm' | 'md' | 'lg';
  fullWidth?: boolean;
  loading?: boolean;
}

export const Button: React.FC<ButtonProps> = ({
  children,
  variant = 'primary',
  size = 'md',
  fullWidth = false,
  loading = false,
  disabled,
  style,
  ...props
}) => {
  const baseStyles: CSSProperties = {
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '8px',
    fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
    fontWeight: 500,
    borderRadius: '4px',
    cursor: disabled || loading ? 'not-allowed' : 'pointer',
    transition: 'all 0.15s ease',
    border: '1px solid',
    textDecoration: 'none',
    opacity: disabled || loading ? 0.4 : 1,
    width: fullWidth ? '100%' : 'auto',
    letterSpacing: '0.01em',
  };

  const variantStyles: Record<string, CSSProperties> = {
    primary: {
      background: '#0F6F6F',
      color: '#FFFFFF',
      borderColor: '#0F6F6F',
      boxShadow: '0 1px 3px rgba(15, 111, 111, 0.2)',
    },
    accent: {
      background: '#C0603F',
      color: '#FFFFFF',
      borderColor: '#C0603F',
      boxShadow: '0 1px 3px rgba(192, 96, 63, 0.2)',
    },
    secondary: {
      background: 'rgba(15, 111, 111, 0.06)',
      color: '#0F6F6F',
      borderColor: '#D0D0D0',
    },
    outline: {
      background: 'transparent',
      color: '#333333',
      borderColor: '#D0D0D0',
    },
    text: {
      background: 'transparent',
      color: '#0F6F6F',
      border: 'none',
      borderBottom: '1px solid transparent',
    },
  };

  const sizeStyles: Record<string, CSSProperties> = {
    sm: {
      padding: '8px 16px',
      fontSize: '0.813rem',
    },
    md: {
      padding: '12px 24px',
      fontSize: '0.875rem',
    },
    lg: {
      padding: '16px 32px',
      fontSize: '1rem',
    },
  };

  const combinedStyles = {
    ...baseStyles,
    ...variantStyles[variant],
    ...sizeStyles[size],
    ...style,
  };

  return (
    <button
      style={combinedStyles}
      disabled={disabled || loading}
      {...props}
      onMouseEnter={(e) => {
        if (!disabled && !loading) {
          const target = e.currentTarget;
          if (variant === 'primary') {
            target.style.background = '#1A8A8A';
            target.style.borderColor = '#1A8A8A';
            target.style.boxShadow = '0 2px 6px rgba(15, 111, 111, 0.3)';
            target.style.transform = 'translateY(-1px)';
          } else if (variant === 'accent') {
            target.style.background = '#D4714F';
            target.style.borderColor = '#D4714F';
            target.style.boxShadow = '0 2px 6px rgba(192, 96, 63, 0.3)';
            target.style.transform = 'translateY(-1px)';
          } else if (variant === 'secondary') {
            target.style.background = 'rgba(15, 111, 111, 0.10)';
            target.style.borderColor = '#0F6F6F';
          } else if (variant === 'outline') {
            target.style.background = '#F5F5F5';
            target.style.borderColor = '#BBBBBB';
          } else if (variant === 'text') {
            target.style.borderBottomColor = '#0F6F6F';
          }
        }
        props.onMouseEnter?.(e);
      }}
      onMouseLeave={(e) => {
        const target = e.currentTarget;
        if (variant === 'primary') {
          target.style.background = '#0F6F6F';
          target.style.borderColor = '#0F6F6F';
          target.style.boxShadow = '0 1px 3px rgba(15, 111, 111, 0.2)';
          target.style.transform = 'translateY(0)';
        } else if (variant === 'accent') {
          target.style.background = '#C0603F';
          target.style.borderColor = '#C0603F';
          target.style.boxShadow = '0 1px 3px rgba(192, 96, 63, 0.2)';
          target.style.transform = 'translateY(0)';
        } else if (variant === 'secondary') {
          target.style.background = 'rgba(15, 111, 111, 0.06)';
          target.style.borderColor = '#D0D0D0';
        } else if (variant === 'outline') {
          target.style.background = 'transparent';
          target.style.borderColor = '#D0D0D0';
        } else if (variant === 'text') {
          target.style.borderBottomColor = 'transparent';
        }
        props.onMouseLeave?.(e);
      }}
    >
      {loading && <span className="spinner" style={{ width: '16px', height: '16px', borderWidth: '2px' }} />}
      {children}
    </button>
  );
};
