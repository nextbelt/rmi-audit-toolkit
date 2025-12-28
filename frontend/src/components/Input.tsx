import React, { InputHTMLAttributes, CSSProperties } from 'react';

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  fullWidth?: boolean;
}

export const Input: React.FC<InputProps> = ({
  label,
  error,
  fullWidth = true,
  style,
  ...props
}) => {
  const containerStyles: CSSProperties = {
    marginBottom: '24px',
    width: fullWidth ? '100%' : 'auto',
  };

  const labelStyles: CSSProperties = {
    display: 'block',
    marginBottom: '8px',
    fontWeight: 500,
    fontSize: '0.875rem',
    color: '#1A1A1A',
  };

  const inputStyles: CSSProperties = {
    width: '100%',
    padding: '16px',
    border: `1px solid ${error ? '#9B2C2C' : '#E5E4E0'}`,
    borderRadius: '4px',
    fontSize: '1rem',
    fontFamily: "'Space Grotesk', sans-serif",
    transition: 'all 0.2s ease',
    background: '#fff',
    color: '#1A1A1A',
    ...style,
  };

  const errorStyles: CSSProperties = {
    marginTop: '4px',
    fontSize: '0.75rem',
    color: '#9B2C2C',
  };

  return (
    <div style={containerStyles}>
      {label && <label style={labelStyles}>{label}</label>}
      <input
        style={inputStyles}
        {...props}
        onFocus={(e) => {
          e.currentTarget.style.borderColor = '#0D4F4F';
          e.currentTarget.style.outline = 'none';
          e.currentTarget.style.boxShadow = '0 0 0 3px rgba(13, 79, 79, 0.1)';
        }}
        onBlur={(e) => {
          e.currentTarget.style.borderColor = error ? '#9B2C2C' : '#E5E4E0';
          e.currentTarget.style.boxShadow = 'none';
        }}
      />
      {error && <div style={errorStyles}>{error}</div>}
    </div>
  );
};

interface TextAreaProps extends InputHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  error?: string;
  fullWidth?: boolean;
  rows?: number;
}

export const TextArea: React.FC<TextAreaProps> = ({
  label,
  error,
  fullWidth = true,
  rows = 4,
  style,
  ...props
}) => {
  const containerStyles: CSSProperties = {
    marginBottom: '24px',
    width: fullWidth ? '100%' : 'auto',
  };

  const labelStyles: CSSProperties = {
    display: 'block',
    marginBottom: '8px',
    fontWeight: 500,
    fontSize: '0.875rem',
    color: '#1A1A1A',
  };

  const textareaStyles: CSSProperties = {
    width: '100%',
    padding: '16px',
    border: `1px solid ${error ? '#9B2C2C' : '#E5E4E0'}`,
    borderRadius: '4px',
    fontSize: '1rem',
    fontFamily: "'Space Grotesk', sans-serif",
    transition: 'all 0.2s ease',
    background: '#fff',
    color: '#1A1A1A',
    resize: 'vertical',
    minHeight: `${rows * 24}px`,
    ...style,
  };

  const errorStyles: CSSProperties = {
    marginTop: '4px',
    fontSize: '0.75rem',
    color: '#9B2C2C',
  };

  return (
    <div style={containerStyles}>
      {label && <label style={labelStyles}>{label}</label>}
      <textarea
        style={textareaStyles}
        rows={rows}
        {...(props as any)}
        onFocus={(e) => {
          e.currentTarget.style.borderColor = '#0D4F4F';
          e.currentTarget.style.outline = 'none';
          e.currentTarget.style.boxShadow = '0 0 0 3px rgba(13, 79, 79, 0.1)';
        }}
        onBlur={(e) => {
          e.currentTarget.style.borderColor = error ? '#9B2C2C' : '#E5E4E0';
          e.currentTarget.style.boxShadow = 'none';
        }}
      />
      {error && <div style={errorStyles}>{error}</div>}
    </div>
  );
};
