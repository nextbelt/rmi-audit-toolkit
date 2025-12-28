import React, { CSSProperties, ButtonHTMLAttributes } from 'react';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'text';
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
    fontFamily: "'Space Grotesk', sans-serif",
    fontWeight: 500,
    borderRadius: '4px',
    cursor: disabled || loading ? 'not-allowed' : 'pointer',
    transition: 'all 0.2s ease',
    border: '2px solid',
    textDecoration: 'none',
    opacity: disabled || loading ? 0.5 : 1,
    width: fullWidth ? '100%' : 'auto',
  };

  const variantStyles: Record<string, CSSProperties> = {
    primary: {
      background: '#0D4F4F',
      color: '#fff',
      borderColor: '#0D4F4F',
    },
    secondary: {
      background: 'transparent',
      color: '#0D4F4F',
      borderColor: '#D1D0CC',
    },
    outline: {
      background: 'transparent',
      color: '#1A1A1A',
      borderColor: '#D1D0CC',
    },
    text: {
      background: 'transparent',
      color: '#0D4F4F',
      border: 'none',
      borderBottom: '1px solid transparent',
    },
  };

  const sizeStyles: Record<string, CSSProperties> = {
    sm: {
      padding: '8px 16px',
      fontSize: '0.875rem',
    },
    md: {
      padding: '16px 24px',
      fontSize: '1rem',
    },
    lg: {
      padding: '20px 32px',
      fontSize: '1.125rem',
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
            target.style.background = '#083A3A';
            target.style.borderColor = '#083A3A';
            target.style.transform = 'translateY(-1px)';
          } else if (variant === 'secondary' || variant === 'outline') {
            target.style.background = '#F2F1EE';
            target.style.borderColor = '#0D4F4F';
          } else if (variant === 'text') {
            target.style.borderBottomColor = '#0D4F4F';
          }
        }
      }}
      onMouseLeave={(e) => {
        const target = e.currentTarget;
        if (variant === 'primary') {
          target.style.background = '#0D4F4F';
          target.style.borderColor = '#0D4F4F';
          target.style.transform = 'translateY(0)';
        } else if (variant === 'secondary' || variant === 'outline') {
          target.style.background = 'transparent';
          target.style.borderColor = '#D1D0CC';
        } else if (variant === 'text') {
          target.style.borderBottomColor = 'transparent';
        }
      }}
    >
      {loading && <span className="spinner" style={{ width: '16px', height: '16px', borderWidth: '2px' }} />}
      {children}
    </button>
  );
};
