import React, { useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useV2Store } from '../api/storeV2';
import { useAuthStore } from '../api/store';

const ArrowRight: React.FC = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <line x1="5" y1="12" x2="19" y2="12" />
    <polyline points="12 5 19 12 12 19" />
  </svg>
);

export const Home: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuthStore();
  const { assessments, loadAssessments } = useV2Store();

  useEffect(() => {
    loadAssessments();
  }, []);

  const stats = useMemo(() => {
    const scored = assessments.filter((a) => a.overall_rmi != null);
    const avg = scored.length
      ? scored.reduce((s, a) => s + (a.overall_rmi || 0), 0) / scored.length
      : null;
    return {
      total: assessments.length,
      inProgress: assessments.filter((a) => (a.status || '').toUpperCase() === 'IN_PROGRESS').length,
      scored: scored.length,
      avg,
    };
  }, [assessments]);

  const recent = assessments.slice(0, 5);
  const firstName = (user?.full_name || '').split(' ')[0] || 'there';

  return (
    <div className="page">
      <div className="pg-head">
        <div>
          <h1 className="pg-title">
            <em>Welcome back,</em> {firstName}
          </h1>
          <div className="pg-sub">
            <span>Reliability maturity at a glance</span>
          </div>
        </div>
        <div className="row" style={{ gap: 10 }}>
          <button className="btn lg" onClick={() => navigate('/dashboard')}>
            View all assessments <ArrowRight />
          </button>
        </div>
      </div>

      <div className="kpi-row">
        <KpiCard label="Total"       value={stats.total} sub="assessments" />
        <KpiCard label="In Progress" value={stats.inProgress} sub="active" />
        <KpiCard label="Scored"      value={stats.scored} sub="finalized" />
        <KpiCard
          label="Avg RMI"
          value={stats.avg == null ? '—' : stats.avg.toFixed(1)}
          unit={stats.avg == null ? undefined : '/ 5.0'}
          empty={stats.avg == null}
          sub="all sites"
        />
      </div>

      <section className="panel">
        <div className="panel-head">
          <h3>Recent assessments</h3>
          <button className="btn sm ghost" onClick={() => navigate('/dashboard')}>
            All <ArrowRight />
          </button>
        </div>
        <div style={{ padding: 6 }}>
          {recent.length === 0 ? (
            <div style={{ padding: '24px', textAlign: 'center', color: 'var(--muted)', fontSize: 13 }}>
              No assessments yet — head to <a onClick={() => navigate('/dashboard')} style={{ color: 'var(--accent)', cursor: 'pointer' }}>Assessments</a> to create one.
            </div>
          ) : (
            recent.map((a) => (
              <div
                key={a.id}
                onClick={() => navigate(`/assessment/${a.id}`)}
                style={{
                  display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                  padding: '12px 14px', borderRadius: 8, cursor: 'pointer',
                }}
                onMouseEnter={(e) => (e.currentTarget.style.background = 'var(--surface-2)')}
                onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}
              >
                <div>
                  <div style={{ fontSize: 13.5, fontWeight: 600, color: 'var(--ink)' }}>
                    {a.organization_name}
                    <span style={{ color: 'var(--muted)', fontWeight: 500 }}> — {a.site_name}</span>
                  </div>
                  <div style={{ fontSize: 11.5, color: 'var(--muted)', marginTop: 3, fontFamily: "'JetBrains Mono', monospace" }}>
                    RMI-{String(a.id).padStart(4, '0')} · {(a.status || 'DRAFT').toLowerCase()}
                  </div>
                </div>
                <div style={{ fontFamily: "'Instrument Serif', serif", fontSize: 22, color: 'var(--ink)' }}>
                  {a.overall_rmi != null ? Number(a.overall_rmi).toFixed(1) : '—'}
                  {a.overall_rmi != null && <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 11, color: 'var(--muted)', marginLeft: 2 }}>/5</span>}
                </div>
              </div>
            ))
          )}
        </div>
      </section>
    </div>
  );
};

const KpiCard: React.FC<{
  label: string;
  value: React.ReactNode;
  unit?: string;
  sub?: string;
  empty?: boolean;
}> = ({ label, value, unit, sub, empty }) => (
  <div className={`kpi ${empty ? 'empty' : ''}`}>
    <div className="label">
      <span className="swatch" />
      {label}
    </div>
    <div className="num">
      {value}
      {unit && <span className="unit">{unit}</span>}
    </div>
    {sub && <div className="foot"><span /><span>{sub}</span></div>}
  </div>
);
