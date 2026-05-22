import React, { useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useV2Store } from '../api/storeV2';

export const Benchmarks: React.FC = () => {
  const navigate = useNavigate();
  const { assessments, loadAssessments } = useV2Store();

  useEffect(() => {
    loadAssessments();
  }, []);

  const scored = useMemo(
    () => assessments.filter((a) => a.overall_rmi != null),
    [assessments],
  );

  return (
    <div className="page">
      <div className="pg-head">
        <div>
          <div className="pg-crumb">
            <span>Insights</span>
            <span style={{ color: 'var(--muted-2)' }}>›</span>
            <span className="crumb-cur">Benchmarks</span>
          </div>
          <h1 className="pg-title">Benchmarks</h1>
          <div className="pg-sub">
            <span>Percentile rankings against the peer cohort</span>
          </div>
        </div>
      </div>

      {scored.length === 0 ? (
        <div className="empty-state">
          <div className="empty-mark">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="10" />
              <circle cx="12" cy="12" r="6" />
              <circle cx="12" cy="12" r="2" />
            </svg>
          </div>
          <h2 className="empty-title">No benchmark data yet</h2>
          <p className="empty-sub">
            Once you have scored assessments, open one to see its percentile against
            the peer cohort. Portfolio rollups will land here.
          </p>
          <div className="row" style={{ gap: 10 }}>
            <button className="btn primary lg" onClick={() => navigate('/dashboard')}>
              Go to Assessments
            </button>
          </div>
        </div>
      ) : (
        <section className="table-card">
          <div className="table-head">
            <div>
              <h3>Open a scored assessment</h3>
              <div style={{ color: 'var(--muted)', fontSize: 12, marginTop: 4 }}>
                Benchmarks are computed per assessment
              </div>
            </div>
          </div>
          {scored.map((a) => (
            <div key={a.id} className="a-row" onClick={() => navigate(`/assessment/${a.id}`)}>
              <div className="a-icon scored">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="20 6 9 17 4 12" />
                </svg>
              </div>
              <div>
                <div className="a-meta-title">
                  {a.organization_name}
                  <span style={{ color: 'var(--muted)', fontWeight: 500 }}> — {a.site_name}</span>
                </div>
                <div className="a-meta-sub">
                  <span className="id">RMI-{String(a.id).padStart(4, '0')}</span>
                </div>
              </div>
              <div />
              <div />
              <div className="a-rmi">
                {Number(a.overall_rmi).toFixed(1)}
                <span className="of">/5</span>
              </div>
              <div className="a-updated">
                {new Date(a.assessment_date).toLocaleDateString()}
              </div>
              <div />
            </div>
          ))}
        </section>
      )}
    </div>
  );
};
