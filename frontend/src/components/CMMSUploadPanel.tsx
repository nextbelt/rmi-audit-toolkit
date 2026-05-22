import React, { useEffect, useRef, useState } from 'react';
import { useV2Store } from '../api/storeV2';
import type { CMMSUpload } from '../api/clientV2';

interface CMMSUploadPanelProps {
  assessmentId: number;
  disabled?: boolean;
}

const formatBytes = (n: number | null) => {
  if (n == null) return '';
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(0)} KB`;
  return `${(n / 1024 / 1024).toFixed(1)} MB`;
};

const kindLabel = (k: string) => (k === 'pm' ? 'PM compliance' : 'Work orders');

const findMetric = (metrics: Record<string, any> | null, paths: string[][]): number | null => {
  if (!metrics) return null;
  for (const path of paths) {
    let cur: any = metrics;
    let ok = true;
    for (const key of path) {
      if (cur && typeof cur === 'object' && key in cur) cur = cur[key];
      else { ok = false; break; }
    }
    if (ok && typeof cur === 'number') return cur;
  }
  return null;
};

const Metric: React.FC<{ label: string; value: string; tone?: 'ok' | 'warn' | 'danger' }> = ({ label, value, tone }) => (
  <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
    <span style={{ fontSize: 10.5, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.08em', fontWeight: 600 }}>
      {label}
    </span>
    <span style={{
      fontFamily: "'Instrument Serif', serif",
      fontSize: 22,
      color: tone === 'ok' ? 'var(--ok)' : tone === 'warn' ? 'var(--warn)' : tone === 'danger' ? 'var(--danger)' : 'var(--ink)',
      lineHeight: 1,
    }}>
      {value}
    </span>
  </div>
);

const MetricRow: React.FC<{ upload: CMMSUpload }> = ({ upload }) => {
  const metrics = upload.metrics;
  if (upload.status === 'error') {
    return (
      <div style={{ color: 'var(--danger)', fontSize: 12, marginTop: 6 }}>
        Analysis failed: {upload.error_message || 'unknown error'}
      </div>
    );
  }
  if (!metrics) {
    return <div style={{ color: 'var(--muted)', fontSize: 12, marginTop: 6 }}>No metrics computed.</div>;
  }

  if (upload.kind === 'work_orders') {
    const reactiveRatio = findMetric(metrics, [
      ['reactive_ratio', 'reactive_ratio'],
      ['reactive_ratio', 'value'],
    ]);
    const dataQualityScore = findMetric(metrics, [
      ['data_quality', 'score'],
      ['data_quality', 'data_quality_score'],
    ]);
    return (
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: 14, marginTop: 10 }}>
        <Metric
          label="Records"
          value={upload.record_count != null ? upload.record_count.toLocaleString() : '—'}
        />
        <Metric
          label="Reactive ratio"
          value={reactiveRatio != null ? `${(reactiveRatio * 100).toFixed(0)}%` : '—'}
          tone={reactiveRatio == null ? undefined : reactiveRatio > 0.5 ? 'danger' : reactiveRatio > 0.3 ? 'warn' : 'ok'}
        />
        <Metric
          label="Data quality"
          value={dataQualityScore != null ? `${dataQualityScore.toFixed(1)} / 5` : '—'}
          tone={dataQualityScore == null ? undefined : dataQualityScore >= 4 ? 'ok' : dataQualityScore >= 3 ? 'warn' : 'danger'}
        />
      </div>
    );
  }

  // pm
  const compliance = findMetric(metrics, [
    ['pm_compliance_rate'],
    ['compliance_rate'],
    ['on_time_completion_pct'],
  ]);
  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: 14, marginTop: 10 }}>
      <Metric
        label="Records"
        value={upload.record_count != null ? upload.record_count.toLocaleString() : '—'}
      />
      <Metric
        label="PM compliance"
        value={compliance != null ? `${(compliance > 1 ? compliance : compliance * 100).toFixed(0)}%` : '—'}
        tone={compliance == null ? undefined : (compliance >= 0.9 || compliance >= 90) ? 'ok' : 'warn'}
      />
    </div>
  );
};

export const CMMSUploadPanel: React.FC<CMMSUploadPanelProps> = ({ assessmentId, disabled }) => {
  const { cmmsUploads, cmmsLoading, loadCMMSUploads, uploadCMMS, deleteCMMSUpload } = useV2Store();
  const woInputRef = useRef<HTMLInputElement>(null);
  const pmInputRef = useRef<HTMLInputElement>(null);
  const [busy, setBusy] = useState<'work_orders' | 'pm' | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadCMMSUploads(assessmentId);
  }, [assessmentId]);

  const handlePick = async (file: File, kind: 'work_orders' | 'pm') => {
    setError(null);
    setBusy(kind);
    try {
      await uploadCMMS(assessmentId, file, kind);
    } catch (e: any) {
      setError(e?.response?.data?.detail || e?.message || 'Upload failed');
    } finally {
      setBusy(null);
    }
  };

  const handleDelete = async (upload: CMMSUpload) => {
    if (!confirm(`Delete CMMS upload "${upload.original_filename || upload.kind}"?`)) return;
    try {
      await deleteCMMSUpload(assessmentId, upload.id);
    } catch (e: any) {
      setError(e?.response?.data?.detail || e?.message || 'Delete failed');
    }
  };

  return (
    <section className="card" style={{ marginBottom: 20 }}>
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap', marginBottom: 14 }}>
        <div>
          <h3 style={{ margin: 0, fontFamily: "'Instrument Serif', serif", fontWeight: 400, fontSize: 22, letterSpacing: '-0.01em' }}>
            CMMS data snapshot
          </h3>
          <div style={{ fontSize: 12.5, color: 'var(--muted)', marginTop: 4, maxWidth: 600 }}>
            Upload a CSV or Excel export from your CMMS. The system computes reactive ratio, data
            quality, and PM compliance — caps unverified AI.1, AI.2, and WM.2 scores.
          </div>
        </div>
        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
          <input
            ref={woInputRef}
            type="file"
            accept=".csv,.xls,.xlsx"
            style={{ display: 'none' }}
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (f) handlePick(f, 'work_orders');
              if (woInputRef.current) woInputRef.current.value = '';
            }}
          />
          <input
            ref={pmInputRef}
            type="file"
            accept=".csv,.xls,.xlsx"
            style={{ display: 'none' }}
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (f) handlePick(f, 'pm');
              if (pmInputRef.current) pmInputRef.current.value = '';
            }}
          />
          <button
            className="btn sm"
            disabled={busy !== null || disabled}
            onClick={() => woInputRef.current?.click()}
          >
            {busy === 'work_orders' ? 'Uploading…' : 'Upload work orders'}
          </button>
          <button
            className="btn sm"
            disabled={busy !== null || disabled}
            onClick={() => pmInputRef.current?.click()}
          >
            {busy === 'pm' ? 'Uploading…' : 'Upload PM data'}
          </button>
        </div>
      </div>

      {error && (
        <div style={{ color: 'var(--danger)', fontSize: 12.5, marginBottom: 10 }}>
          {error}
        </div>
      )}

      {cmmsLoading && (
        <div style={{ color: 'var(--muted)', fontSize: 12.5 }}>Loading…</div>
      )}

      {!cmmsLoading && cmmsUploads.length === 0 && (
        <div style={{ color: 'var(--muted)', fontSize: 12.5, padding: '12px 0' }}>
          No CMMS snapshots uploaded yet. Without one, AI.1 / AI.2 / WM.2 are
          capped during scoring.
        </div>
      )}

      <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        {cmmsUploads.map((u) => (
          <div
            key={u.id}
            style={{
              padding: 12,
              borderRadius: 8,
              border: '1px solid var(--line-2)',
              background: 'var(--surface-2)',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 10 }}>
              <div>
                <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--ink)' }}>
                  {kindLabel(u.kind)}
                  <span style={{ color: 'var(--muted)', fontWeight: 500 }}> · {u.original_filename || 'snapshot'}</span>
                </div>
                <div style={{ fontSize: 11.5, color: 'var(--muted)', marginTop: 2, fontFamily: "'JetBrains Mono', monospace" }}>
                  {formatBytes(u.file_size_bytes)} · uploaded {new Date(u.uploaded_at).toLocaleString()}
                </div>
              </div>
              <div style={{ display: 'flex', gap: 6 }}>
                <span className={`chip ${u.status === 'processed' ? 'ok' : u.status === 'error' ? 'danger' : 'warn'}`}>
                  <span className="dot" />
                  {u.status}
                </span>
                <button
                  className="btn sm danger"
                  onClick={() => handleDelete(u)}
                  disabled={disabled}
                >
                  Remove
                </button>
              </div>
            </div>
            <MetricRow upload={u} />
          </div>
        ))}
      </div>
    </section>
  );
};

export default CMMSUploadPanel;
