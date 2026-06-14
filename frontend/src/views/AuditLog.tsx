import React, { useEffect, useState } from 'react';
import api from '../api/client';

interface AuditEntry {
  id: number;
  occurred_at: string | null;
  actor_email: string | null;
  action: string;
  target_type: string | null;
  target_id: string | null;
  ip_address: string | null;
  details: string | null;
}

const ACTION_LABELS: Record<string, string> = {
  'user.login': 'Signed in',
  'user.create': 'User created',
  'user.update': 'User updated',
  'assessment.finalize': 'Assessment finalized',
  'assessment.score': 'Scores calculated',
  'assessment.report.generate': 'Report generated',
  'assessment.cmms.upload': 'CMMS uploaded',
  'response.evidence.upload': 'Evidence uploaded',
  'response.evidence.analyze': 'Evidence analyzed',
};

export const AuditLog: React.FC = () => {
  const [rows, setRows] = useState<AuditEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const r = await api.get('/audit', { params: { limit: 200 } });
        if (alive) setRows(r.data);
      } catch (e: any) {
        if (alive) setError(e?.response?.data?.detail || 'Could not load the audit log.');
      } finally {
        if (alive) setLoading(false);
      }
    })();
    return () => {
      alive = false;
    };
  }, []);

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
            <span>Append-only record of security-relevant actions</span>
          </div>
        </div>
      </div>

      {error && <div className="banner error" role="alert" style={{ marginBottom: 16 }}>{error}</div>}

      {loading ? (
        <div style={{ display: 'grid', placeItems: 'center', padding: 48 }}><div className="spinner" /></div>
      ) : rows.length === 0 ? (
        <div className="empty-state">
          <h2 className="empty-title">No events yet</h2>
          <p className="empty-sub">Actions like sign-ins, scoring, and report generation will appear here.</p>
        </div>
      ) : (
        <section className="table-card">
          <div className="table-head"><div><h3>{rows.length} most recent events</h3></div></div>
          {rows.map((r) => (
            <div key={r.id} className="a-row" style={{ gridTemplateColumns: '160px minmax(0,1.4fr) minmax(0,1.2fr) 120px' }}>
              <div className="a-updated mono" style={{ fontSize: 12 }}>
                {r.occurred_at ? new Date(r.occurred_at).toLocaleString() : '—'}
              </div>
              <div>
                <div className="a-meta-title">{ACTION_LABELS[r.action] || r.action}</div>
                <div className="a-meta-sub">
                  <span className="mono" style={{ fontSize: 11, color: 'var(--muted)' }}>{r.action}</span>
                </div>
              </div>
              <div style={{ fontSize: 12.5, color: 'var(--ink-2)' }}>
                {r.actor_email || 'system'}
                {r.target_type && (
                  <span style={{ color: 'var(--muted)' }}> · {r.target_type}{r.target_id ? ` #${r.target_id}` : ''}</span>
                )}
              </div>
              <div className="mono" style={{ fontSize: 11, color: 'var(--muted-2)' }}>{r.ip_address || ''}</div>
            </div>
          ))}
        </section>
      )}
    </div>
  );
};
