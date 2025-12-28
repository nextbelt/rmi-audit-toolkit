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
    background: 'rgba(0, 0, 0, 0.5)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 9999,
    padding: '24px',
  };

  const contentStyles: CSSProperties = {
    background: '#fff',
    borderRadius: '12px',
    padding: '40px',
    width: '100%',
    maxWidth,
    maxHeight: '90vh',
    overflow: 'auto',
    position: 'relative',
  };

  const closeButtonStyles: CSSProperties = {
    position: 'absolute',
    top: '24px',
    right: '24px',
    background: 'none',
    border: 'none',
    fontSize: '1.5rem',
    cursor: 'pointer',
    color: '#5C5C5C',
    padding: '8px',
    lineHeight: 1,
    transition: 'color 0.2s ease',
  };

  const titleStyles: CSSProperties = {
    fontSize: '1.5rem',
    fontWeight: 600,
    marginBottom: '24px',
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
            e.currentTarget.style.color = '#1A1A1A';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.color = '#5C5C5C';
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
