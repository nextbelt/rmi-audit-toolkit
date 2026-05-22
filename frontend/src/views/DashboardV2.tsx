import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useV2Store } from '../api/storeV2';
import { Button, Input, Modal } from '../components';

const MODE_LABELS: Record<string, { label: string; cls: string; desc: string }> = {
  quickscan: { label: 'QuickScan', cls: 'ok',     desc: '15 questions · Free tier' },
  standard:  { label: 'Standard',  cls: 'accent', desc: '60-75 questions · Full assessment' },
  deepdive:  { label: 'DeepDive',  cls: 'warn',   desc: '150+ questions · Comprehensive audit' },
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

type StatusKey = 'DRAFT' | 'IN_PROGRESS' | 'COMPLETED' | 'FINALIZED';
const STATUS_META: Record<StatusKey, { label: string; chip: string; iconCls: string; icon: JSX.Element }> = {
  DRAFT: {
    label: 'Draft', chip: 'muted', iconCls: 'draft',
    icon: <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" /><path d="M18.5 2.5a2.12 2.12 0 0 1 3 3L12 15l-4 1 1-4z" /></svg>,
  },
  IN_PROGRESS: {
    label: 'In Progress', chip: 'warn', iconCls: 'progress',
    icon: <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><polygon points="6 4 20 12 6 20 6 4" /></svg>,
  },
  COMPLETED: {
    label: 'Scored', chip: 'ok', iconCls: 'scored',
    icon: <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12" /></svg>,
  },
  FINALIZED: {
    label: 'Finalized', chip: 'accent', iconCls: 'locked',
    icon: <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" /><path d="M7 11V7a5 5 0 0 1 10 0v4" /></svg>,
  },
};

const FilterIcon: React.FC = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3" />
  </svg>
);

const PlusIcon: React.FC = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <line x1="12" y1="5" x2="12" y2="19" />
    <line x1="5" y1="12" x2="19" y2="12" />
  </svg>
);

const ChevronRightIcon: React.FC<{ size?: number }> = ({ size = 11 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="9 18 15 12 9 6" />
  </svg>
);

const VALID_STATUSES: StatusKey[] = ['DRAFT', 'IN_PROGRESS', 'COMPLETED', 'FINALIZED'];

export const DashboardV2: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const { assessments, assessmentsLoading, loadAssessments, createAssessment } = useV2Store();
  const [showCreate, setShowCreate] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);

  const statusParam = (searchParams.get('status') || '').toUpperCase();
  const filter: 'all' | StatusKey =
    VALID_STATUSES.includes(statusParam as StatusKey) ? (statusParam as StatusKey) : 'all';

  const setFilter = (next: 'all' | StatusKey) => {
    const params = new URLSearchParams(searchParams);
    if (next === 'all') params.delete('status');
    else params.set('status', next);
    setSearchParams(params, { replace: true });
  };
  const [form, setForm] = useState({
    organization_name: '',
    site_name: '',
    assessment_date: '',
    assessment_mode: 'standard' as 'quickscan' | 'standard' | 'deepdive',
    industry_module: '',
  });

  useEffect(() => {
    loadAssessments();
  }, []);

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
      setForm({
        organization_name: '',
        site_name: '',
        assessment_date: '',
        assessment_mode: 'standard',
        industry_module: '',
      });
      navigate(`/assessment/${created.id}`);
    } catch (err: any) {
      const msg = err?.response?.data?.detail || err?.message || 'Failed to create assessment';
      setCreateError(typeof msg === 'string' ? msg : JSON.stringify(msg));
    }
  };

  const counts = useMemo(() => {
    const c: Record<string, number> = { all: assessments.length };
    for (const a of assessments) {
      const s = (a.status || 'DRAFT').toUpperCase();
      c[s] = (c[s] || 0) + 1;
    }
    return c;
  }, [assessments]);

  const filtered = useMemo(() => {
    if (filter === 'all') return assessments;
    return assessments.filter((a) => (a.status || 'DRAFT').toUpperCase() === filter);
  }, [assessments, filter]);

  const stats = useMemo(() => {
    const scored = assessments.filter((a) => a.overall_rmi != null);
    const avg = scored.length
      ? scored.reduce((s, a) => s + (a.overall_rmi || 0), 0) / scored.length
      : null;
    return {
      total: assessments.length,
      inProgress: assessments.filter((a) => (a.status || '').toUpperCase() === 'IN_PROGRESS').length,
      completed: scored.length,
      avgRMI: avg,
    };
  }, [assessments]);

  if (assessmentsLoading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '80vh' }}>
        <div className="spinner" />
      </div>
    );
  }

  return (
    <div className="page">
      {/* Header */}
      <div className="pg-head">
        <div>
          <h1 className="pg-title">
            <em>Reliability</em> Assessments
          </h1>
          <div className="pg-sub">
            <span>5-domain maturity scoring across your sites</span>
          </div>
        </div>
        <div className="row" style={{ gap: 10, flexWrap: 'wrap' }}>
          <button className="btn primary lg" onClick={() => setShowCreate(true)}>
            <PlusIcon /> New Assessment
          </button>
        </div>
      </div>

      {/* KPI row */}
      <div className="kpi-row">
        <KpiCard label="Total"       swatch="var(--accent)" value={stats.total} sub="all assessments" />
        <KpiCard label="In Progress" swatch="var(--warn)"   value={stats.inProgress} sub="active" />
        <KpiCard label="Scored"      swatch="var(--ok)"     value={stats.completed} sub="finalized" />
        <KpiCard
          label="Avg RMI"
          swatch="var(--accent)"
          value={stats.avgRMI == null ? '—' : stats.avgRMI.toFixed(1)}
          unit={stats.avgRMI == null ? undefined : '/ 5.0'}
          empty={stats.avgRMI == null}
          sub="all sites"
        />
      </div>

      {/* Assessments table or empty state */}
      {assessments.length === 0 ? (
        <EmptyState onCreate={() => setShowCreate(true)} />
      ) : (
        <section className="table-card">
          <div className="table-head">
            <div>
              <h3>Recent assessments</h3>
              <div style={{ color: 'var(--muted)', fontSize: 12, marginTop: 4 }}>
                Sorted by last update · Showing {filtered.length} of {assessments.length}
              </div>
            </div>
            <div className="filter-row">
              {([
                ['all', 'All'],
                ['IN_PROGRESS', 'In Progress'],
                ['COMPLETED', 'Scored'],
                ['FINALIZED', 'Finalized'],
                ['DRAFT', 'Draft'],
              ] as Array<[ 'all' | StatusKey, string ]>).map(([k, l]) => (
                <button
                  key={k}
                  className={`filter-chip ${filter === k ? 'on' : ''}`}
                  onClick={() => setFilter(k)}
                >
                  {l} <span className="count">{counts[k] || 0}</span>
                </button>
              ))}
              <button className="filter-chip" title="Filter">
                <FilterIcon />
              </button>
            </div>
          </div>

          <div
            style={{
              display: 'grid',
              gridTemplateColumns: '36px minmax(0, 1.8fr) 1fr 110px 90px 90px 36px',
              gap: 14,
              padding: '10px 22px',
              borderBottom: '1px solid var(--line-2)',
              color: 'var(--muted)',
              fontSize: 10.5,
              textTransform: 'uppercase',
              letterSpacing: '0.1em',
              fontWeight: 600,
            }}
          >
            <span />
            <span>Site & scope</span>
            <span>Status</span>
            <span>Mode</span>
            <span style={{ textAlign: 'right' }}>RMI</span>
            <span style={{ textAlign: 'right' }}>Date</span>
            <span />
          </div>

          {filtered.map((a) => {
            const statusKey = ((a.status || 'DRAFT').toUpperCase() as StatusKey);
            const meta = STATUS_META[statusKey] || STATUS_META.DRAFT;
            const mode = MODE_LABELS[a.assessment_mode];
            return (
              <div key={a.id} className="a-row" onClick={() => navigate(`/assessment/${a.id}`)}>
                <div className={`a-icon ${meta.iconCls}`}>{meta.icon}</div>
                <div>
                  <div className="a-meta-title">
                    {a.organization_name}
                    <span style={{ color: 'var(--muted)', fontWeight: 500 }}>
                      {' '}— {a.site_name}
                    </span>
                  </div>
                  <div className="a-meta-sub">
                    <span className="id">RMI-{String(a.id).padStart(4, '0')}</span>
                    {a.industry_module && (
                      <>
                        <span className="pipe">·</span>
                        <span>{a.industry_module}</span>
                      </>
                    )}
                  </div>
                </div>
                <div>
                  <span className={`chip ${meta.chip}`}>
                    <span className="dot" />
                    {meta.label}
                  </span>
                </div>
                <div>
                  {mode && (
                    <span className={`chip ${mode.cls}`}>
                      {mode.label}
                    </span>
                  )}
                </div>
                <div className="a-rmi">
                  {a.overall_rmi != null ? (
                    <>
                      {Number(a.overall_rmi).toFixed(1)}
                      <span className="of">/5</span>
                    </>
                  ) : (
                    <span style={{ color: 'var(--muted-2)' }}>—</span>
                  )}
                </div>
                <div className="a-updated">
                  {new Date(a.assessment_date).toLocaleDateString()}
                </div>
                <button
                  className="icon-btn"
                  style={{ width: 28, height: 28 }}
                  onClick={(e) => {
                    e.stopPropagation();
                    navigate(`/assessment/${a.id}`);
                  }}
                  aria-label="Open"
                >
                  <ChevronRightIcon size={14} />
                </button>
              </div>
            );
          })}

          <div className="table-foot">
            <span>
              Showing {filtered.length} {filter === 'all' ? '' : `· filtered by ${STATUS_META[filter as StatusKey]?.label || filter}`}
            </span>
            <span className="mono">{assessments.length} total</span>
          </div>
        </section>
      )}

      {/* Create Modal */}
      <Modal
        isOpen={showCreate}
        onClose={() => {
          setShowCreate(false);
          setCreateError(null);
        }}
        title="New Assessment"
      >
        <form onSubmit={handleCreate}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            {createError && (
              <div
                style={{
                  padding: '10px 14px',
                  borderRadius: 8,
                  background: 'rgba(194, 83, 60, 0.08)',
                  border: '1px solid rgba(194, 83, 60, 0.30)',
                  color: 'var(--danger)',
                  fontSize: 12.5,
                  marginBottom: 8,
                }}
              >
                {createError}
              </div>
            )}
            <Input
              label="Organization Name"
              required
              value={form.organization_name}
              onChange={(e) => setForm({ ...form, organization_name: e.target.value })}
            />
            <Input
              label="Site Name"
              required
              value={form.site_name}
              onChange={(e) => setForm({ ...form, site_name: e.target.value })}
            />
            <Input
              label="Assessment Date"
              type="date"
              required
              value={form.assessment_date}
              onChange={(e) => setForm({ ...form, assessment_date: e.target.value })}
              onClick={(e) => {
                const el = e.currentTarget as HTMLInputElement & { showPicker?: () => void };
                if (typeof el.showPicker === 'function') {
                  try { el.showPicker(); } catch { /* ignore */ }
                }
              }}
              onFocus={(e) => {
                const el = e.currentTarget as HTMLInputElement & { showPicker?: () => void };
                if (typeof el.showPicker === 'function') {
                  try { el.showPicker(); } catch { /* ignore */ }
                }
              }}
              style={{ cursor: 'pointer' }}
            />

            <div className="field">
              <label className="field-label">Assessment Mode</label>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 8 }}>
                {(['quickscan', 'standard', 'deepdive'] as const).map((mode) => {
                  const info = MODE_LABELS[mode];
                  const isSelected = form.assessment_mode === mode;
                  return (
                    <button
                      type="button"
                      key={mode}
                      onClick={() => setForm({ ...form, assessment_mode: mode })}
                      style={{
                        padding: '14px 12px',
                        borderRadius: 10,
                        cursor: 'pointer',
                        textAlign: 'center',
                        border: `1px solid ${isSelected ? 'var(--accent)' : 'var(--line)'}`,
                        background: isSelected ? 'var(--accent-soft)' : 'var(--surface)',
                        transition: 'all 0.15s ease',
                        fontFamily: 'inherit',
                      }}
                    >
                      <div
                        style={{
                          fontWeight: 600,
                          fontSize: 13,
                          color: isSelected ? 'var(--accent)' : 'var(--ink)',
                        }}
                      >
                        {info.label}
                      </div>
                      <div style={{ fontSize: 11, color: 'var(--muted)', marginTop: 4 }}>
                        {info.desc}
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>

            <div className="field">
              <label className="field-label">Industry Module (Optional)</label>
              <select
                className="field-input"
                value={form.industry_module}
                onChange={(e) => setForm({ ...form, industry_module: e.target.value })}
              >
                {INDUSTRY_OPTIONS.map((o) => (
                  <option key={o.value} value={o.value}>
                    {o.label}
                  </option>
                ))}
              </select>
            </div>

            <div style={{ display: 'flex', gap: 12, justifyContent: 'flex-end', marginTop: 8 }}>
              <Button variant="outline" onClick={() => setShowCreate(false)} type="button">
                Cancel
              </Button>
              <Button type="submit">Create Assessment</Button>
            </div>
          </div>
        </form>
      </Modal>
    </div>
  );
};

const KpiCard: React.FC<{
  label: string;
  swatch: string;
  value: React.ReactNode;
  unit?: string;
  sub?: string;
  empty?: boolean;
}> = ({ label, swatch, value, unit, sub, empty }) => (
  <div className={`kpi ${empty ? 'empty' : ''}`}>
    <div className="label">
      <span className="swatch" style={{ background: swatch }} />
      {label}
    </div>
    <div className="num">
      {value}
      {unit && <span className="unit">{unit}</span>}
    </div>
    {sub && <div className="foot"><span /><span>{sub}</span></div>}
  </div>
);

const EmptyMarkIcon: React.FC = () => (
  <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="10" />
    <polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76" />
  </svg>
);

const EmptyState: React.FC<{ onCreate: () => void }> = ({ onCreate }) => (
  <div className="empty-state">
    <div className="empty-mark"><EmptyMarkIcon /></div>
    <h2 className="empty-title">No assessments yet</h2>
    <p className="empty-sub">
      Create your first assessment using the 5-domain framework. We'll walk you through the
      calibrated questions and produce subdomain-level scoring.
    </p>
    <div className="row" style={{ gap: 10 }}>
      <button className="btn primary lg" onClick={onCreate}>
        <PlusIcon /> Create Assessment
      </button>
    </div>
    <div className="empty-steps">
      <div className="empty-step">
        <div className="empty-step-n">1</div>
        <div className="empty-step-t">Pick a scope</div>
        <div className="empty-step-d">Site, line, or asset family</div>
      </div>
      <div className="empty-step">
        <div className="empty-step-n">2</div>
        <div className="empty-step-t">Answer the questions</div>
        <div className="empty-step-d">5 domains calibrated against industrial sites</div>
      </div>
      <div className="empty-step">
        <div className="empty-step-n">3</div>
        <div className="empty-step-t">Review your RMI</div>
        <div className="empty-step-d">Subdomain-level scoring with gap analysis</div>
      </div>
    </div>
  </div>
);
