import React from 'react';
import { useAuthStore } from '../api/store';

export const Settings: React.FC = () => {
  const { user, logout } = useAuthStore();

  return (
    <div className="page">
      <div className="pg-head">
        <div>
          <div className="pg-crumb">
            <span>Admin</span>
            <span style={{ color: 'var(--muted-2)' }}>›</span>
            <span className="crumb-cur">Settings</span>
          </div>
          <h1 className="pg-title">Settings</h1>
          <div className="pg-sub">
            <span>Account and workspace preferences</span>
          </div>
        </div>
      </div>

      <div className="card" style={{ marginBottom: 16 }}>
        <div className="label" style={{ marginBottom: 12 }}>Account</div>
        <div style={{ display: 'grid', gridTemplateColumns: '180px 1fr', gap: '12px 24px', fontSize: 13 }}>
          <span style={{ color: 'var(--muted)' }}>Name</span>
          <span style={{ color: 'var(--ink)' }}>{user?.full_name || '—'}</span>
          <span style={{ color: 'var(--muted)' }}>Email</span>
          <span style={{ color: 'var(--ink)' }}>{user?.email || '—'}</span>
          <span style={{ color: 'var(--muted)' }}>Role</span>
          <span style={{ color: 'var(--ink)', textTransform: 'capitalize' }}>{user?.role || '—'}</span>
        </div>
      </div>

      <div className="card">
        <div className="label" style={{ marginBottom: 12 }}>Session</div>
        <div style={{ fontSize: 13, color: 'var(--muted)', marginBottom: 14 }}>
          Sign out of this browser session.
        </div>
        <button className="btn danger" onClick={logout}>
          Sign out
        </button>
      </div>
    </div>
  );
};
