import React, { CSSProperties, HTMLAttributes } from 'react';

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  hover?: boolean;
  border?: boolean;
  glow?: boolean;
}

export const Card: React.FC<CardProps> = ({
  children,
  hover = false,
  border = true,
  glow = false,
  style,
  ...props
}) => {
  const baseStyles: CSSProperties = {
    background: '#FFFFFF',
    border: border ? '1px solid #E5E5E5' : 'none',
    borderRadius: '8px',
    padding: '24px',
    transition: 'all 0.15s ease',
    position: 'relative',
    boxShadow: glow ? '0 1px 4px rgba(15, 111, 111, 0.06)' : '0 1px 2px rgba(0, 0, 0, 0.04)',
  };

  const combinedStyles = {
    ...baseStyles,
    ...style,
  };

  return (
    <div
      style={combinedStyles}
      {...props}
      onMouseEnter={(e) => {
        if (hover) {
          const target = e.currentTarget;
          target.style.borderColor = '#D0D0D0';
          target.style.background = '#FAFAFA';
          target.style.boxShadow = '0 2px 8px rgba(0, 0, 0, 0.06)';
          target.style.transform = 'translateY(-1px)';
        }
        props.onMouseEnter?.(e);
      }}
      onMouseLeave={(e) => {
        if (hover) {
          const target = e.currentTarget;
          target.style.borderColor = '#E5E5E5';
          target.style.background = '#FFFFFF';
          target.style.boxShadow = glow ? '0 1px 4px rgba(15, 111, 111, 0.06)' : '0 1px 2px rgba(0, 0, 0, 0.04)';
          target.style.transform = 'translateY(0)';
        }
        props.onMouseLeave?.(e);
      }}
    >
      {children}
    </div>
  );
};
