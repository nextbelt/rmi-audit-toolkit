import React, { useState, useEffect } from "react";
import { v2API } from "../../api/clientV2";
import type { ISOGapReport, ISOClauseResult, ISOSection } from "../../api/clientV2";

const ISO_STATUS_META: Record<
  ISOClauseResult["status"],
  { label: string; tone: string; bg: string }
> = {
  exceeds:    { label: "Exceeds",    tone: "var(--ok)",      bg: "rgba(47,138,107,0.10)" },
  ready:      { label: "Ready",      tone: "var(--ok)",      bg: "rgba(47,138,107,0.10)" },
  gap:        { label: "Gap",        tone: "var(--warn)",    bg: "rgba(192,138,46,0.10)" },
  major_gap:  { label: "Major gap",  tone: "var(--danger)",  bg: "rgba(194,83,60,0.10)" },
  unanswered: { label: "Unanswered", tone: "var(--muted)",   bg: "var(--surface-2)" },
  unmapped:   { label: "Unmapped",   tone: "var(--muted-2)", bg: "var(--surface-2)" },
};

const ClauseRow: React.FC<{ clause: ISOClauseResult; floor: number }> = ({
  clause,
  floor,
}) => {
  const [open, setOpen] = useState(false);
  const meta = ISO_STATUS_META[clause.status];
  const score = clause.score;
  const pct = ((score ?? 0) / 5) * 100;
  const targetPct = (floor / 5) * 100;
  const hasDetails = clause.low_questions.length > 0;
  return (
    <div style={{ borderTop: "1px solid var(--line-2)" }}>
      <div
        onClick={() => hasDetails && setOpen(!open)}
        style={{
          display: "grid",
          gridTemplateColumns: "70px minmax(240px, 1fr) 1fr 80px 100px 20px",
          gap: 14,
          alignItems: "center",
          padding: "14px 24px",
          cursor: hasDetails ? "pointer" : "default",
        }}
      >
        <span
          style={{
            fontFamily: "'JetBrains Mono', monospace",
            fontSize: 12,
            color: "var(--muted)",
            fontWeight: 600,
          }}
        >
          {clause.clause}
        </span>
        <span style={{ fontSize: 13.5, color: "var(--ink)", fontWeight: 500 }}>
          {clause.name}
        </span>
        <div
          style={{
            position: "relative",
            height: 10,
            background: "var(--surface-2)",
            borderRadius: 5,
            overflow: "visible",
          }}
        >
          {clause.status !== "unanswered" && clause.status !== "unmapped" && (
            <div
              style={{
                position: "absolute",
                left: 0,
                top: 0,
                bottom: 0,
                width: `${pct}%`,
                background: meta.tone,
                borderRadius: 5,
                transition: "width 0.4s ease-out",
              }}
            />
          )}
          {/* Target line at the floor */}
          <div
            style={{
              position: "absolute",
              left: `${targetPct}%`,
              top: -3,
              bottom: -3,
              width: 2,
              background: "var(--ink)",
              opacity: 0.55,
              borderRadius: 1,
            }}
            title={`Target ${floor.toFixed(1)}`}
          />
        </div>
        <span
          className="chip"
          style={{ background: meta.bg, color: meta.tone, whiteSpace: "nowrap" }}
        >
          <span className="dot" />
          {meta.label}
        </span>
        <span
          style={{
            fontFamily: "'Instrument Serif', serif",
            fontSize: 22,
            color: meta.tone,
            textAlign: "right",
          }}
        >
          {score != null ? score.toFixed(1) : "—"}
        </span>
        <span
          style={{
            color: "var(--muted)",
            fontSize: 12,
            display: "inline-flex",
            justifyContent: "flex-end",
            opacity: hasDetails ? 1 : 0,
            transform: open ? "rotate(90deg)" : "none",
            transition: "transform 0.15s ease",
          }}
        >
          ›
        </span>
      </div>

      {open && hasDetails && (
        <div
          style={{
            padding: "0 24px 16px 94px",
            background: "var(--surface-2)",
            borderTop: "1px solid var(--line-2)",
          }}
        >
          <div
            style={{
              fontSize: 11,
              color: "var(--muted)",
              textTransform: "uppercase",
              letterSpacing: "0.08em",
              fontWeight: 600,
              padding: "10px 0 6px",
            }}
          >
            Pulling this clause down ({clause.questions_answered}/{clause.questions_total} questions answered)
          </div>
          {clause.low_questions.map((q) => (
            <div
              key={q.id}
              style={{
                display: "grid",
                gridTemplateColumns: "80px 1fr 50px",
                gap: 12,
                alignItems: "center",
                padding: "8px 0",
                fontSize: 12.5,
                color: "var(--ink-2)",
                borderTop: "1px dashed var(--line)",
              }}
            >
              <span
                style={{
                  fontFamily: "'JetBrains Mono', monospace",
                  fontSize: 11,
                  color: "var(--muted)",
                }}
              >
                {q.code}
              </span>
              <span>{q.text}</span>
              <span
                style={{
                  fontFamily: "'Instrument Serif', serif",
                  fontSize: 18,
                  color: q.score < 2 ? "var(--danger)" : "var(--warn)",
                  textAlign: "right",
                }}
              >
                {q.score.toFixed(1)}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

const SectionCard: React.FC<{ section: ISOSection; floor: number }> = ({
  section,
  floor,
}) => {
  return (
    <div
      style={{
        background: "var(--surface)",
        border: "1px solid var(--line)",
        borderRadius: "var(--radius)",
        overflow: "hidden",
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "16px 24px",
          borderBottom: "1px solid var(--line-2)",
          gap: 12,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
          <span
            style={{
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: 14,
              fontWeight: 600,
              padding: "6px 12px",
              borderRadius: 8,
              background: "var(--accent-soft)",
              color: "var(--accent)",
              letterSpacing: "0.04em",
            }}
          >
            §{section.section}
          </span>
          <h3
            style={{
              fontFamily: "'Instrument Serif', serif",
              fontWeight: 400,
              fontSize: 22,
              letterSpacing: "-0.005em",
              margin: 0,
              color: "var(--ink)",
            }}
          >
            {section.title}
          </h3>
        </div>
        <div style={{ fontSize: 12, color: "var(--muted)" }}>
          <span style={{ color: "var(--ok)", fontWeight: 600 }}>
            {section.ready}
          </span>
          <span> / {section.total} clauses ready</span>
        </div>
      </div>
      <div>
        {section.clauses.map((c) => (
          <ClauseRow key={c.clause} clause={c} floor={floor} />
        ))}
      </div>
    </div>
  );
};

export const IsoGapsTab: React.FC<{ assessmentId: number }> = ({ assessmentId }) => {
  const [report, setReport] = useState<ISOGapReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    setLoading(true);
    setError(null);
    v2API
      .getISOGapReport(assessmentId)
      .then((r) => {
        if (alive) setReport(r);
      })
      .catch((e: any) => {
        if (alive)
          setError(e?.response?.data?.detail || e?.message || "Could not load gap report");
      })
      .finally(() => {
        if (alive) setLoading(false);
      });
    return () => {
      alive = false;
    };
  }, [assessmentId]);

  if (loading)
    return (
      <div style={{ textAlign: "center", padding: 40 }}>
        <div className="spinner" />
      </div>
    );

  if (error)
    return (
      <div
        className="card"
        style={{
          padding: 24,
          color: "var(--danger)",
          fontSize: 13,
        }}
      >
        {error}
      </div>
    );

  if (!report) return null;

  const s = report.summary;

  return (
    <div>
      {/* Summary strip */}
      <div className="stat-strip">
        <div className="stat">
          <div className="label">Overall Readiness</div>
          <div className="stat-num-wrap">
            <span
              className="num stat-num"
              style={{
                color:
                  s.overall_readiness_pct < 50
                    ? "var(--danger)"
                    : s.overall_readiness_pct < 70
                    ? "var(--warn)"
                    : "var(--ok)",
              }}
            >
              {s.overall_readiness_pct.toFixed(0)}
            </span>
            <span className="stat-unit">%</span>
          </div>
          <div className="stat-sub">
            {s.clauses_ready} of {s.total_clauses_mapped} clauses ready
          </div>
          <div className="stat-hint">
            Clauses scoring ≥ {report.floor.toFixed(1)} (Systematic)
          </div>
        </div>
        <div className="stat">
          <div className="label">Ready</div>
          <div className="stat-num-wrap">
            <span className="num stat-num" style={{ color: "var(--ok)" }}>
              {s.clauses_ready}
            </span>
          </div>
          <div className="stat-sub">Audit-defensible</div>
          <div className="stat-hint">Maintain & document evidence</div>
        </div>
        <div className="stat">
          <div className="label">Gaps</div>
          <div className="stat-num-wrap">
            <span className="num stat-num" style={{ color: "var(--warn)" }}>
              {s.clauses_with_gap}
            </span>
          </div>
          <div className="stat-sub">Close to floor</div>
          <div className="stat-hint">Score 2.0 – 3.0; targeted lift</div>
        </div>
        <div className="stat">
          <div className="label">Major Gaps</div>
          <div className="stat-num-wrap">
            <span className="num stat-num" style={{ color: "var(--danger)" }}>
              {s.clauses_major_gap}
            </span>
          </div>
          <div className="stat-sub">Material findings</div>
          <div className="stat-hint">Score &lt; 2.0; remediation required</div>
        </div>
      </div>

      <div
        className="card"
        style={{
          padding: "18px 22px",
          marginBottom: 24,
          display: "flex",
          alignItems: "flex-start",
          gap: 14,
          background: "var(--surface)",
        }}
      >
        <div
          style={{
            width: 38,
            height: 38,
            borderRadius: 10,
            background: "var(--accent-soft)",
            color: "var(--accent)",
            display: "grid",
            placeItems: "center",
            flexShrink: 0,
          }}
        >
          <svg
            width="18"
            height="18"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M9 11l3 3L22 4" />
            <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11" />
          </svg>
        </div>
        <div style={{ fontSize: 13, color: "var(--ink-2)", lineHeight: 1.55, maxWidth: 800 }}>
          <strong>ISO 55001:2014</strong> readiness is computed clause-by-clause from
          the questions tagged to each clause. A clause is <em>Ready</em> when its
          mean response score reaches the {report.floor.toFixed(1)} floor
          (Systematic — documented, followed, measured). Click any clause row to
          see the questions pulling it down.
        </div>
      </div>

      <div className="domain-section-head" style={{ margin: "0 0 14px" }}>
        <h2 className="section-title">Clauses by section</h2>
        <span className="chip muted" style={{ fontFamily: "'JetBrains Mono', monospace" }}>
          Target {report.floor.toFixed(1)}
        </span>
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
        {report.sections.map((sec) => (
          <SectionCard key={sec.section} section={sec} floor={report.floor} />
        ))}
      </div>
    </div>
  );
};
