import React, { CSSProperties, HTMLAttributes } from 'react';

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  hover?: boolean;
  border?: boolean;
}

export const Card: React.FC<CardProps> = ({
  children,
  hover = false,
  border = true,
  style,
  ...props
}) => {
  const baseStyles: CSSProperties = {
    background: '#fff',
    border: border ? '1px solid #E5E4E0' : 'none',
    borderRadius: '8px',
    padding: '40px',
    transition: 'all 0.2s ease',
    position: 'relative',
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
          target.style.borderColor = '#D1D0CC';
          target.style.boxShadow = '0 4px 20px rgba(0,0,0,0.06)';
        }
      }}
      onMouseLeave={(e) => {
        if (hover) {
          const target = e.currentTarget;
          target.style.borderColor = '#E5E4E0';
          target.style.boxShadow = 'none';
        }
      }}
    >
      {children}
    </div>
  );
};
