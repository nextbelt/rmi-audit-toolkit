import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useV2Store } from '../api/storeV2';
import { Button, Card, Input, Modal } from '../components';
import { theme } from '../styles/theme';

const MODE_LABELS: Record<string, { label: string; color: string; desc: string }> = {
  quickscan: { label: 'QuickScan', color: '#0D8A5E', desc: '15 questions · Free tier' },
  standard:  { label: 'Standard',  color: theme.colors.primary, desc: '60-75 questions · Full assessment' },
  deepdive:  { label: 'DeepDive',  color: theme.colors.accent, desc: '150+ questions · Comprehensive audit' },
};

const INDUSTRY_OPTIONS = [
  { value: '', label: 'No industry module' },
  { value: 'MFG', label: 'Manufacturing (General)' },
  { value: 'FNB', label: 'Food & Beverage' },
  { value: 'ONG', label: 'Oil & Gas' },
  { value: 'MNM', label: 'Mining & Minerals' },
  { value: 'UTL', label: 'Utilities' },
  { value: 'PHA', label: 'Pharmaceuticals' },
];

export const DashboardV2: React.FC = () => {
  const navigate = useNavigate();
  const { assessments, assessmentsLoading, loadAssessments, createAssessment } = useV2Store();
  const [showCreate, setShowCreate] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);
  const [form, setForm] = useState({
    organization_name: '',
    site_name: '',
    assessment_date: '',
    assessment_mode: 'standard' as 'quickscan' | 'standard' | 'deepdive',
    industry_module: '',
  });

  useEffect(() => { loadAssessments(); }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreateError(null);
    try {
      const created = await createAssessment({
        ...form,
        assessment_date: new Date(form.assessment_date).toISOString(),
        industry_module: form.industry_module || undefined,
      });
      setShowCreate(false);
      setForm({ organization_name: '', site_name: '', assessment_date: '', assessment_mode: 'standard', industry_module: '' });
      navigate(`/assessment/${created.id}`);
    } catch (err: any) {
      const msg = err?.response?.data?.detail || err?.message || 'Failed to create assessment';
      setCreateError(typeof msg === 'string' ? msg : JSON.stringify(msg));
    }
  };

  const getStatusBadge = (status: string) => {
    const s = (status || 'DRAFT').toUpperCase();
    const colors: Record<string, string> = {
      DRAFT: '#999999', IN_PROGRESS: '#C0603F', COMPLETED: '#0D8A5E', FINALIZED: theme.colors.primary,
    };
    return (
      <span style={{
        display: 'inline-block', padding: '2px 10px', borderRadius: '12px', fontSize: '0.75rem',
        fontWeight: 600, letterSpacing: '0.02em', textTransform: 'uppercase',
        background: `${colors[s] || '#8A8A8A'}18`, color: colors[s] || '#8A8A8A',
      }}>{s.replace('_', ' ')}</span>
    );
  };

  if (assessmentsLoading) {
    return <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '80vh' }}><div className="spinner" /></div>;
  }

  const stats = {
    total: assessments.length,
    inProgress: assessments.filter(a => a.status === 'IN_PROGRESS').length,
    completed: assessments.filter(a => a.overall_rmi !== null).length,
    avgRMI: assessments.filter(a => a.overall_rmi).length > 0
      ? (assessments.filter(a => a.overall_rmi).reduce((s, a) => s + (a.overall_rmi || 0), 0) / assessments.filter(a => a.overall_rmi).length).toFixed(1)
      : '—',
  };

  return (
    <div style={{ padding: '40px 24px', maxWidth: '1200px', margin: '0 auto' }}>
      {/* Header */}
      <div style={{ marginBottom: '40px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
            <h1 style={{ fontSize: '1.75rem', margin: 0, color: '#1A1A1A' }}>RMI Assessments</h1>
            <span style={{
              fontSize: '0.625rem', fontWeight: 700, padding: '2px 8px', borderRadius: '4px',
              background: theme.colors.primary, color: '#fff', letterSpacing: '0.05em',
            }}>v2.0</span>
          </div>
          <p style={{ color: '#666666', fontSize: '0.8125rem' }}>
            5-domain taxonomy · 150 questions · Subdomain-level scoring
          </p>
        </div>
        <Button onClick={() => setShowCreate(true)}>+ New Assessment</Button>
      </div>

      {/* Stats */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '24px', marginBottom: '40px' }}>
        {[
          { label: 'Total', value: stats.total, color: theme.colors.primary },
          { label: 'In Progress', value: stats.inProgress, color: '#C0603F' },
          { label: 'Scored', value: stats.completed, color: '#0D8A5E' },
          { label: 'Avg RMI', value: stats.avgRMI, color: theme.colors.primary },
        ].map(s => (
          <Card key={s.label}>
            <div style={{ padding: '20px' }}>
              <div style={{ fontSize: '0.6875rem', color: '#666666', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '8px' }}>{s.label}</div>
              <div style={{ fontSize: '2rem', fontWeight: 700, color: s.color }}>{s.value}</div>
            </div>
          </Card>
        ))}
      </div>

      {/* Assessment List */}
      {assessments.length === 0 ? (
        <Card>
          <div style={{ padding: '60px', textAlign: 'center' }}>
            <div style={{ fontSize: '3rem', marginBottom: '16px' }}>📋</div>
            <h3 style={{ marginBottom: '8px', color: '#1A1A1A' }}>No Assessments Yet</h3>
            <p style={{ color: '#666666', marginBottom: '24px' }}>Create your first assessment using the 5-domain framework.</p>
            <Button onClick={() => setShowCreate(true)}>Create Assessment</Button>
          </div>
        </Card>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {assessments.map(a => (
            <Card key={a.id}>
              <div
                onClick={() => navigate(`/assessment/${a.id}`)}
                style={{ padding: '20px', cursor: 'pointer', display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '16px' }}
              >
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '4px' }}>
                    <span style={{ fontWeight: 600, fontSize: '1.05rem', color: '#1A1A1A' }}>{a.organization_name}</span>
                    <span style={{
                      fontSize: '0.7rem', padding: '1px 6px', borderRadius: '4px', fontWeight: 600,
                      background: `${MODE_LABELS[a.assessment_mode]?.color || '#888'}18`,
                      color: MODE_LABELS[a.assessment_mode]?.color || '#888',
                    }}>{MODE_LABELS[a.assessment_mode]?.label || a.assessment_mode}</span>
                    {getStatusBadge(a.status)}
                  </div>
                  <div style={{ fontSize: '0.825rem', color: '#8A8A86' }}>
                    {a.site_name} · {new Date(a.assessment_date).toLocaleDateString()}
                    {a.industry_module && ` · ${a.industry_module}`}
                  </div>
                </div>
                <div style={{ textAlign: 'right', minWidth: '80px' }}>
                  {a.overall_rmi != null ? (
                    <>
                      <div style={{ fontSize: '1.5rem', fontWeight: 700, color: theme.colors.primary }}>{Number(a.overall_rmi).toFixed(1)}</div>
                      <div style={{ fontSize: '0.7rem', color: '#666666' }}>{a.maturity_level}</div>
                    </>
                  ) : (
                    <div style={{ fontSize: '0.8rem', color: '#666666' }}>Not scored</div>
                  )}
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Create Modal */}
      <Modal isOpen={showCreate} onClose={() => { setShowCreate(false); setCreateError(null); }} title="New vNext Assessment">
        <form onSubmit={handleCreate}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {createError && (
              <div style={{ padding: '10px 14px', borderRadius: '6px', background: '#FEF2F2', border: '1px solid #FECACA', color: '#991B1B', fontSize: '0.8125rem' }}>
                {createError}
              </div>
            )}
            <Input label="Organization Name" required value={form.organization_name} onChange={(e) => setForm({ ...form, organization_name: e.target.value })} />
            <Input label="Site Name" required value={form.site_name} onChange={(e) => setForm({ ...form, site_name: e.target.value })} />
            <Input label="Assessment Date" type="date" required value={form.assessment_date} onChange={(e) => setForm({ ...form, assessment_date: e.target.value })} />

            {/* Mode Selector */}
            <div>
              <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, marginBottom: '8px', color: '#8A8A86', textTransform: 'uppercase', letterSpacing: '0.06em' }}>Assessment Mode</label>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '8px' }}>
                {(['quickscan', 'standard', 'deepdive'] as const).map(mode => {
                  const info = MODE_LABELS[mode];
                  const isSelected = form.assessment_mode === mode;
                  return (
                    <div
                      key={mode}
                      onClick={() => setForm({ ...form, assessment_mode: mode })}
                      style={{
                        padding: '14px 12px', borderRadius: '8px', cursor: 'pointer', textAlign: 'center',
                        border: `2px solid ${isSelected ? info.color : 'rgba(0,0,0,0.08)'}`,
                        background: isSelected ? `${info.color}15` : '#FFFFFF',
                        transition: 'all 0.2s ease',
                      }}
                    >
                      <div style={{ fontWeight: 600, fontSize: '0.9rem', color: isSelected ? info.color : '#333333' }}>{info.label}</div>
                      <div style={{ fontSize: '0.7rem', color: '#666666', marginTop: '4px' }}>{info.desc}</div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Industry Module */}
            <div>
              <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, marginBottom: '8px', color: '#8A8A86', textTransform: 'uppercase', letterSpacing: '0.06em' }}>Industry Module (Optional)</label>
              <select
                value={form.industry_module}
                onChange={(e) => setForm({ ...form, industry_module: e.target.value })}
                style={{
                  width: '100%', padding: '10px 12px', borderRadius: '6px',
                  border: '1px solid rgba(0,0,0,0.12)', fontSize: '0.875rem',
                  background: '#FFFFFF', color: '#333333',
                  fontFamily: theme.typography.fontFamily.primary,
                }}
              >
                {INDUSTRY_OPTIONS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
              </select>
            </div>

            <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end', marginTop: '8px' }}>
              <Button variant="secondary" onClick={() => setShowCreate(false)} type="button">Cancel</Button>
              <Button type="submit">Create Assessment</Button>
            </div>
          </div>
        </form>
      </Modal>
    </div>
  );
};
