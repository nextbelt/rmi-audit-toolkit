import React, { InputHTMLAttributes, TextareaHTMLAttributes } from 'react';

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  fullWidth?: boolean;
}

export const Input: React.FC<InputProps> = ({
  label,
  error,
  fullWidth = true,
  className,
  style,
  ...props
}) => {
  return (
    <div className="field" style={{ width: fullWidth ? '100%' : 'auto' }}>
      {label && <label className="field-label">{label}</label>}
      <input
        className={`field-input ${className || ''}`}
        style={{
          borderColor: error ? 'rgba(194, 83, 60, 0.5)' : undefined,
          ...style,
        }}
        {...props}
      />
      {error && <div className="field-error">{error}</div>}
    </div>
  );
};

interface TextAreaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
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
  className,
  style,
  ...props
}) => {
  return (
    <div className="field" style={{ width: fullWidth ? '100%' : 'auto' }}>
      {label && <label className="field-label">{label}</label>}
      <textarea
        className={`field-input ${className || ''}`}
        rows={rows}
        style={{
          resize: 'vertical',
          minHeight: rows * 24,
          borderColor: error ? 'rgba(194, 83, 60, 0.5)' : undefined,
          ...style,
        }}
        {...props}
      />
      {error && <div className="field-error">{error}</div>}
    </div>
  );
};
