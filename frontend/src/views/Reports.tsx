import React, { useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useV2Store } from '../api/storeV2';

export const Reports: React.FC = () => {
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
            <span className="crumb-cur">Reports</span>
          </div>
          <h1 className="pg-title">Reports</h1>
          <div className="pg-sub">
            <span>Download executive PDFs for scored assessments</span>
          </div>
        </div>
      </div>

      {scored.length === 0 ? (
        <div className="empty-state">
          <div className="empty-mark">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="7 10 12 15 17 10" />
              <line x1="12" y1="15" x2="12" y2="3" />
            </svg>
          </div>
          <h2 className="empty-title">No reports available yet</h2>
          <p className="empty-sub">
            Reports unlock once an assessment is scored. Finish an in-progress assessment
            and run scoring to generate a downloadable PDF.
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
              <h3>Scored assessments</h3>
              <div style={{ color: 'var(--muted)', fontSize: 12, marginTop: 4 }}>
                {scored.length} ready for download
              </div>
            </div>
          </div>
          {scored.map((a) => (
            <div key={a.id} className="a-row" style={{ gridTemplateColumns: 'minmax(0, 1.8fr) 100px 100px 140px' }}>
              <div>
                <div className="a-meta-title">
                  {a.organization_name}
                  <span style={{ color: 'var(--muted)', fontWeight: 500 }}> — {a.site_name}</span>
                </div>
                <div className="a-meta-sub">
                  <span className="id">RMI-{String(a.id).padStart(4, '0')}</span>
                </div>
              </div>
              <div className="a-rmi">
                {Number(a.overall_rmi).toFixed(1)}
                <span className="of">/5</span>
              </div>
              <div className="a-updated">
                {new Date(a.assessment_date).toLocaleDateString()}
              </div>
              <button className="btn sm" onClick={() => navigate(`/assessment/${a.id}`)}>
                Open report
              </button>
            </div>
          ))}
        </section>
      )}
    </div>
  );
};
