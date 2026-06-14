import React, { useRef, useState } from 'react';
import { v2API } from '../api/clientV2';
import { useV2Store } from '../api/storeV2';

interface EvidenceFile {
  filename: string | null;
  mime: string | null;
  size_bytes: number | null;
  uploaded_at: string | null;
}

interface AIAnalysis {
  suggested_score: number | null;
  observations: string | null;
  confidence: string | null;
  analyzed_at: string | null;
}

interface EvidenceWidgetProps {
  assessmentId: number;
  questionId: number;
  evidenceFile?: EvidenceFile | null;
  aiAnalysis?: AIAnalysis | null;
  /** Called when AI returns a suggested score and the auditor accepts it. */
  onAcceptSuggestedScore?: (score: number) => void;
  disabled?: boolean;
}

const ACCEPTED_EXTENSIONS = '.pdf,.png,.jpg,.jpeg';

const formatBytes = (n: number | null) => {
  if (n == null) return '';
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(0)} KB`;
  return `${(n / 1024 / 1024).toFixed(1)} MB`;
};

const confidenceColor = (c: string | null | undefined) => {
  if (c === 'HIGH') return 'var(--ok)';
  if (c === 'LOW') return 'var(--danger)';
  return 'var(--warn)';
};

export const EvidenceWidget: React.FC<EvidenceWidgetProps> = ({
  assessmentId,
  questionId,
  evidenceFile,
  aiAnalysis,
  onAcceptSuggestedScore,
  disabled,
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { uploadEvidence, deleteEvidence, analyzeEvidence } = useV2Store();
  const [busy, setBusy] = useState<null | 'upload' | 'analyze' | 'delete' | 'preview'>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [verdict, setVerdict] = useState<{
    accepted: boolean;
    ai_verdict: 'relevant' | 'irrelevant' | 'unclear';
    ai_reason: string | null;
  } | null>(null);

  const isImage = evidenceFile?.mime?.startsWith('image/');

  const handleUpload = async (file: File) => {
    setError(null);
    setVerdict(null);
    setBusy('upload');
    try {
      const res = await uploadEvidence(assessmentId, questionId, file);
      setVerdict(res);
      setPreviewUrl(null);
    } catch (e: any) {
      setError(e?.response?.data?.detail || e?.message || 'Upload failed');
    } finally {
      setBusy(null);
    }
  };

  const handleAnalyze = async () => {
    setError(null);
    setBusy('analyze');
    try {
      await analyzeEvidence(assessmentId, questionId);
    } catch (e: any) {
      setError(e?.response?.data?.detail || e?.message || 'AI analysis failed');
    } finally {
      setBusy(null);
    }
  };

  const handleDelete = async () => {
    if (!evidenceFile) return;
    if (!confirm(`Remove "${evidenceFile.filename || 'evidence'}"?`)) return;
    setError(null);
    setVerdict(null);
    setBusy('delete');
    try {
      await deleteEvidence(assessmentId, questionId);
      if (previewUrl) {
        URL.revokeObjectURL(previewUrl);
        setPreviewUrl(null);
      }
    } catch (e: any) {
      setError(e?.response?.data?.detail || e?.message || 'Delete failed');
    } finally {
      setBusy(null);
    }
  };

  const handleShowPreview = async () => {
    if (previewUrl) {
      window.open(previewUrl, '_blank');
      return;
    }
    setBusy('preview');
    try {
      const blob = await v2API.fetchEvidenceBlob(assessmentId, questionId);
      const url = URL.createObjectURL(blob);
      setPreviewUrl(url);
      window.open(url, '_blank');
    } catch (e: any) {
      setError(e?.message || 'Could not load preview');
    } finally {
      setBusy(null);
    }
  };

  const hasFile = !!evidenceFile;
  const hasAI = !!aiAnalysis && aiAnalysis.analyzed_at;

  return (
    <div
      style={{
        marginTop: 10,
        padding: 10,
        borderRadius: 8,
        border: '1px dashed var(--line)',
        background: 'var(--surface-2)',
        fontSize: 12.5,
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ fontWeight: 600, color: 'var(--ink)' }}>Evidence</span>
          {hasFile ? (
            <span style={{ color: 'var(--muted)', fontSize: 11.5 }}>
              {evidenceFile?.filename} · {formatBytes(evidenceFile?.size_bytes || null)}
            </span>
          ) : (
            <span style={{ color: 'var(--muted)', fontSize: 11.5 }}>
              Attach a photo, screenshot, or PDF
            </span>
          )}
        </div>
        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
          <input
            ref={fileInputRef}
            type="file"
            accept={ACCEPTED_EXTENSIONS}
            style={{ display: 'none' }}
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (f) handleUpload(f);
              if (fileInputRef.current) fileInputRef.current.value = '';
            }}
          />
          {hasFile && (
            <button
              type="button"
              className="btn sm ghost"
              onClick={handleShowPreview}
              disabled={busy !== null || disabled}
            >
              {busy === 'preview' ? '…' : 'View'}
            </button>
          )}
          <button
            type="button"
            className="btn sm"
            onClick={() => fileInputRef.current?.click()}
            disabled={busy !== null || disabled}
          >
            {busy === 'upload' ? 'Uploading…' : hasFile ? 'Replace' : 'Upload'}
          </button>
          {hasFile && (
            <button
              type="button"
              className="btn sm danger"
              onClick={handleDelete}
              disabled={busy !== null || disabled}
            >
              {busy === 'delete' ? '…' : 'Remove'}
            </button>
          )}
          {hasFile && (
            <button
              type="button"
              className="btn sm primary"
              onClick={handleAnalyze}
              disabled={busy !== null || disabled}
              title={isImage ? 'Analyze image with OpenAI vision' : 'Analyze document with OpenAI'}
            >
              {busy === 'analyze' ? 'Analyzing…' : hasAI ? 'Re-analyze' : 'Analyze with AI'}
            </button>
          )}
        </div>
      </div>

      {error && (
        <div style={{ marginTop: 8, color: 'var(--danger)', fontSize: 11.5 }}>
          {error}
        </div>
      )}

      {verdict && (
        (() => {
          const v = verdict.ai_verdict;
          const tone =
            v === 'irrelevant'
              ? { bg: 'rgba(194,83,60,0.08)', bd: 'rgba(194,83,60,0.35)', fg: 'var(--danger)', icon: '⚠', label: 'Rejected — not valid evidence' }
              : v === 'relevant'
              ? { bg: 'rgba(13,138,94,0.08)', bd: 'rgba(13,138,94,0.30)', fg: 'var(--ok)', icon: '✓', label: 'Accepted — relevant evidence' }
              : { bg: 'rgba(184,134,11,0.08)', bd: 'rgba(184,134,11,0.35)', fg: 'var(--warn)', icon: '⏸', label: 'Not counted — could not verify' };
          return (
            <div style={{ marginTop: 8, padding: '8px 10px', borderRadius: 6, background: tone.bg, border: `1px solid ${tone.bd}`, fontSize: 11.5 }}>
              <div style={{ color: tone.fg, fontWeight: 700 }}>{tone.icon} Reliability reviewer · {tone.label}</div>
              {verdict.ai_reason && (
                <div style={{ marginTop: 3, color: 'var(--ink-2)', lineHeight: 1.45 }}>{verdict.ai_reason}</div>
              )}
              {v === 'irrelevant' && (
                <div style={{ marginTop: 3, color: 'var(--muted)' }}>
                  This file does not count toward scoring confidence. Upload evidence that actually addresses the question.
                </div>
              )}
              {v === 'unclear' && (
                <div style={{ marginTop: 3, color: 'var(--muted)' }}>
                  It does not count toward confidence yet. Re-run “Analyze with AI”, or replace it with clearer evidence.
                </div>
              )}
            </div>
          );
        })()
      )}

      {hasAI && aiAnalysis && (
        <div
          style={{
            marginTop: 10,
            padding: 10,
            borderRadius: 6,
            background: 'var(--surface)',
            border: '1px solid var(--line)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8 }}>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
              <span style={{ fontSize: 11, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.08em', fontWeight: 600 }}>
                AI suggestion
              </span>
              {aiAnalysis.suggested_score != null && (
                <span style={{ fontFamily: "'Instrument Serif', serif", fontSize: 22, color: 'var(--accent)', lineHeight: 1 }}>
                  {aiAnalysis.suggested_score.toFixed(1)}
                  <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 10, color: 'var(--muted)', marginLeft: 2 }}>/5</span>
                </span>
              )}
              <span style={{ color: confidenceColor(aiAnalysis.confidence), fontSize: 11, fontWeight: 600 }}>
                {aiAnalysis.confidence}
              </span>
            </div>
            {aiAnalysis.suggested_score != null && onAcceptSuggestedScore && (
              <button
                type="button"
                className="btn sm"
                onClick={() => onAcceptSuggestedScore(Math.round(aiAnalysis.suggested_score!))}
                disabled={disabled}
              >
                Accept score
              </button>
            )}
          </div>
          {aiAnalysis.observations && (
            <div style={{ marginTop: 6, color: 'var(--ink-2)', lineHeight: 1.5, fontSize: 12 }}>
              {aiAnalysis.observations}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default EvidenceWidget;
