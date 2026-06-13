import React, { HTMLAttributes } from 'react';

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
  className,
  style,
  ...props
}) => {
  const classes = [
    'card',
    hover ? 'hover' : '',
    !border ? 'no-border' : '',
    glow ? 'glow' : '',
    className || '',
  ]
    .filter(Boolean)
    .join(' ');

  return (
    <div
      className={classes}
      style={{
        ...(border ? null : { border: 'none' }),
        ...style,
      }}
      {...props}
    >
      {children}
    </div>
  );
};
