import React from 'react';

export const AuditLog: React.FC = () => {
  return (
    <div className="page">
      <div className="pg-head">
        <div>
          <div className="pg-crumb">
            <span>Admin</span>
            <span style={{ color: 'var(--muted-2)' }}>›</span>
            <span className="crumb-cur">Audit log</span>
          </div>
          <h1 className="pg-title">Audit log</h1>
          <div className="pg-sub">
            <span>System events and user actions</span>
          </div>
        </div>
      </div>

      <div className="empty-state">
        <div className="empty-mark">
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
            <path d="M18.5 2.5a2.12 2.12 0 0 1 3 3L12 15l-4 1 1-4z" />
          </svg>
        </div>
        <h2 className="empty-title">Audit log coming soon</h2>
        <p className="empty-sub">
          The backend tracks audit events; this page will surface them once the
          read endpoint is wired up.
        </p>
      </div>
    </div>
  );
};
