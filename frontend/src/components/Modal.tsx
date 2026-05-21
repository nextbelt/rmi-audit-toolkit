import React, { CSSProperties, ReactNode } from 'react';

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  children: ReactNode;
  maxWidth?: string;
}

export const Modal: React.FC<ModalProps> = ({
  isOpen,
  onClose,
  title,
  children,
  maxWidth = '600px',
}) => {
  if (!isOpen) return null;

  const overlayStyles: CSSProperties = {
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    background: 'rgba(0, 0, 0, 0.7)',
    backdropFilter: 'blur(8px)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 9999,
    padding: '24px',
  };

  const contentStyles: CSSProperties = {
    background: '#FFFFFF',
    border: '1px solid #E5E5E5',
    borderRadius: '8px',
    padding: '24px',
    width: '100%',
    maxWidth,
    maxHeight: '90vh',
    overflow: 'auto',
    position: 'relative',
    boxShadow: '0 8px 30px rgba(0, 0, 0, 0.12)',
  };

  const closeButtonStyles: CSSProperties = {
    position: 'absolute',
    top: '16px',
    right: '16px',
    background: '#F5F5F5',
    border: '1px solid #E5E5E5',
    borderRadius: '4px',
    fontSize: '1rem',
    cursor: 'pointer',
    color: '#999999',
    padding: '4px 8px',
    lineHeight: 1,
    transition: 'all 0.15s ease',
  };

  const titleStyles: CSSProperties = {
    fontSize: '1.125rem',
    fontWeight: 600,
    marginBottom: '20px',
    color: '#1A1A1A',
  };

  return (
    <div
      style={overlayStyles}
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div style={contentStyles} onClick={(e) => e.stopPropagation()}>
        <button
          style={closeButtonStyles}
          onClick={onClose}
          onMouseEnter={(e) => {
            e.currentTarget.style.color = '#333333';
            e.currentTarget.style.background = '#EEEEEE';
            e.currentTarget.style.borderColor = '#D0D0D0';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.color = '#999999';
            e.currentTarget.style.background = '#F5F5F5';
            e.currentTarget.style.borderColor = '#E5E5E5';
          }}
        >
          ✕
        </button>
        {title && <h2 style={titleStyles}>{title}</h2>}
        {children}
      </div>
    </div>
  );
};
