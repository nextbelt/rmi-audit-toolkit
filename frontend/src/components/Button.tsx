import React, { ButtonHTMLAttributes } from 'react';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'text' | 'accent' | 'ghost' | 'danger';
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
  className,
  style,
  ...props
}) => {
  const variantCls: Record<string, string> = {
    primary: 'btn primary',
    accent: 'btn primary',
    secondary: 'btn',
    outline: 'btn outline',
    ghost: 'btn ghost',
    text: 'btn ghost',
    danger: 'btn danger',
  };

  const sizeCls: Record<string, string> = {
    sm: 'sm',
    md: '',
    lg: 'lg',
  };

  const classes = [
    variantCls[variant] || 'btn',
    sizeCls[size] || '',
    fullWidth ? 'block' : '',
    className || '',
  ]
    .filter(Boolean)
    .join(' ');

  return (
    <button
      className={classes}
      disabled={disabled || loading}
      style={style}
      {...props}
    >
      {loading && (
        <span
          className="spinner"
          style={{ width: 14, height: 14, borderWidth: 2 }}
        />
      )}
      {children}
    </button>
  );
};
