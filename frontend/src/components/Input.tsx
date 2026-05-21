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
    marginBottom: '20px',
    width: fullWidth ? '100%' : 'auto',
  };

  const labelStyles: CSSProperties = {
    display: 'block',
    marginBottom: '6px',
    fontWeight: 500,
    fontSize: '0.813rem',
    color: '#666666',
    textTransform: 'uppercase',
    letterSpacing: '0.05em',
  };

  const inputStyles: CSSProperties = {
    width: '100%',
    padding: '10px 14px',
    border: `1px solid ${error ? 'rgba(197, 48, 48, 0.4)' : '#D0D0D0'}`,
    borderRadius: '4px',
    fontSize: '0.875rem',
    fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
    transition: 'all 0.15s ease',
    background: '#FFFFFF',
    color: '#333333',
    ...style,
  };

  const errorStyles: CSSProperties = {
    marginTop: '4px',
    fontSize: '0.75rem',
    color: '#C53030',
  };

  return (
    <div style={containerStyles}>
      {label && <label style={labelStyles}>{label}</label>}
      <input
        style={inputStyles}
        {...props}
        onFocus={(e) => {
          e.currentTarget.style.borderColor = '#0F6F6F';
          e.currentTarget.style.outline = 'none';
          e.currentTarget.style.boxShadow = '0 0 0 2px rgba(15, 111, 111, 0.12)';
        }}
        onBlur={(e) => {
          e.currentTarget.style.borderColor = error ? 'rgba(197, 48, 48, 0.4)' : '#D0D0D0';
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
    marginBottom: '20px',
    width: fullWidth ? '100%' : 'auto',
  };

  const labelStyles: CSSProperties = {
    display: 'block',
    marginBottom: '6px',
    fontWeight: 500,
    fontSize: '0.813rem',
    color: '#666666',
    textTransform: 'uppercase',
    letterSpacing: '0.05em',
  };

  const textareaStyles: CSSProperties = {
    width: '100%',
    padding: '10px 14px',
    border: `1px solid ${error ? 'rgba(197, 48, 48, 0.4)' : '#D0D0D0'}`,
    borderRadius: '4px',
    fontSize: '0.875rem',
    fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
    transition: 'all 0.15s ease',
    background: '#FFFFFF',
    color: '#333333',
    resize: 'vertical',
    minHeight: `${rows * 24}px`,
    ...style,
  };

  const errorStyles: CSSProperties = {
    marginTop: '4px',
    fontSize: '0.75rem',
    color: '#C53030',
  };

  return (
    <div style={containerStyles}>
      {label && <label style={labelStyles}>{label}</label>}
      <textarea
        style={textareaStyles}
        rows={rows}
        {...(props as any)}
        onFocus={(e) => {
          e.currentTarget.style.borderColor = '#0F6F6F';
          e.currentTarget.style.outline = 'none';
          e.currentTarget.style.boxShadow = '0 0 0 2px rgba(15, 111, 111, 0.12)';
        }}
        onBlur={(e) => {
          e.currentTarget.style.borderColor = error ? 'rgba(197, 48, 48, 0.4)' : '#D0D0D0';
          e.currentTarget.style.boxShadow = 'none';
        }}
      />
      {error && <div style={errorStyles}>{error}</div>}
    </div>
  );
};
