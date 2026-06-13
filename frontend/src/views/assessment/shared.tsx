import React, { useState } from "react";

const MATURITY_LEVELS = [
  { n: 1, label: "Reactive",     from: 1.0, to: 2.0 },
  { n: 2, label: "Emerging",     from: 2.0, to: 3.0 },
  { n: 3, label: "Systematic",   from: 3.0, to: 3.6 },
  { n: 4, label: "Proactive",    from: 3.6, to: 4.3 },
  { n: 5, label: "Prescriptive", from: 4.3, to: 5.01 },
];

const colorForScore = (s: number | null | undefined): string => {
  if (s == null) return "var(--muted-2)";
  if (s < 1.5) return "var(--danger)";
  if (s < 2.5) return "var(--warn)";
  if (s < 3.5) return "var(--accent)";
  return "var(--ok)";
};

const levelForScore = (s: number | null | undefined) => {
  if (s == null) return MATURITY_LEVELS[0];
  return (
    MATURITY_LEVELS.find((l) => s >= l.from && s < l.to) ||
    MATURITY_LEVELS[MATURITY_LEVELS.length - 1]
  );
};

const ScaleRuler: React.FC = () => (
  <div className="ruler">
    {MATURITY_LEVELS.map((l) => (
      <div key={l.n} className="ruler-cell">
        <span className="ruler-n mono">L{l.n}</span>
        <span className="ruler-label">{l.label}</span>
      </div>
    ))}
  </div>
);

const StatCard: React.FC<{
  label: string;
  value: string;
  unit?: string;
  tone?: string;
  sub: React.ReactNode;
  hint?: string;
}> = ({ label, value, unit, tone, sub, hint }) => (
  <div className="stat">
    <div className="label">{label}</div>
    <div className="stat-num-wrap">
      <span className="num stat-num" style={{ color: tone || "var(--ink)" }}>{value}</span>
      {unit && <span className="stat-unit">{unit}</span>}
    </div>
    <div className="stat-sub">{sub}</div>
    {hint && <div className="stat-hint">{hint}</div>}
  </div>
);

interface EvidenceBlockedQuestion {
  question_id: number;
  code: string;
  claimed: number;
  capped_to: number;
  evidence_status: string | null;
}

const SubRow: React.FC<{
  code: string;
  name: string;
  score: number | null;
  capApplied: boolean;
  evidenceBlocked?: number;
  evidenceBlockedQuestions?: EvidenceBlockedQuestion[];
}> = ({
  code,
  name,
  score,
  capApplied,
  evidenceBlocked = 0,
  evidenceBlockedQuestions = [],
}) => {
  const c = colorForScore(score);
  const pct = ((score ?? 0) / 5) * 100;
  const [showDetails, setShowDetails] = useState(false);
  const hasEvidenceCap = evidenceBlocked > 0;
  return (
    <>
      <div className="sub-row">
        <span className="sub-code">{code}</span>
        <span className="sub-name">{name}</span>
        <div className="sub-track">
          <div className="sub-track-ticks">
            {[1, 2, 3, 4, 5].map((n) => (
              <div key={n} className="sub-tick" />
            ))}
          </div>
          <div className="sub-fill" style={{ width: `${pct}%`, background: c }} />
          <div className="sub-target" title="Target 3.0" />
        </div>
        <span className="sub-score" style={{ color: c }}>
          {score != null ? score.toFixed(1) : "—"}
        </span>
        <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
          {capApplied && (
            <span className="chip-capped" title="Score capped by a weakest-link rule">
              CAPPED
            </span>
          )}
          {hasEvidenceCap && (
            <button
              type="button"
              onClick={() => setShowDetails(!showDetails)}
              title={`${evidenceBlocked} question${evidenceBlocked === 1 ? "" : "s"} capped — evidence missing or unverified`}
              style={{
                cursor: "pointer",
                fontFamily: "'JetBrains Mono', monospace",
                fontSize: 9.5,
                fontWeight: 600,
                letterSpacing: "0.06em",
                padding: "3px 7px",
                borderRadius: 4,
                background: "rgba(192, 138, 46, 0.12)",
                color: "var(--warn)",
                border: "1px solid rgba(192, 138, 46, 0.35)",
                textTransform: "uppercase",
                display: "inline-flex",
                alignItems: "center",
                gap: 4,
              }}
            >
              <svg
                width="10"
                height="10"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                <polyline points="14 2 14 8 20 8" />
              </svg>
              {evidenceBlocked} no evid.
              <span style={{ marginLeft: 2 }}>{showDetails ? "▴" : "▾"}</span>
            </button>
          )}
        </div>
      </div>

      {showDetails && hasEvidenceCap && (
        <div
          style={{
            background: "rgba(192, 138, 46, 0.06)",
            borderTop: "1px solid var(--line-2)",
            padding: "12px 24px 14px",
          }}
        >
          <div
            style={{
              fontSize: 11,
              color: "var(--warn)",
              textTransform: "uppercase",
              letterSpacing: "0.08em",
              fontWeight: 600,
              marginBottom: 8,
            }}
          >
            Capped questions in this subdomain
          </div>
          <div style={{ fontSize: 12.5, color: "var(--ink-2)", lineHeight: 1.5, marginBottom: 10 }}>
            These were scored ≥ 4 (Proactive/Prescriptive) on questions that
            require auditable evidence. Each is capped at 3.0 until accepted
            evidence is on file.
          </div>
          {evidenceBlockedQuestions.map((q) => (
            <div
              key={q.question_id}
              style={{
                display: "grid",
                gridTemplateColumns: "100px 1fr auto auto",
                gap: 14,
                alignItems: "center",
                padding: "6px 0",
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
                  fontWeight: 600,
                }}
              >
                {q.code}
              </span>
              <span style={{ color: "var(--muted)" }}>
                Status: <span style={{ color: "var(--warn)", fontWeight: 600 }}>
                  {q.evidence_status || "—"}
                </span>
              </span>
              <span style={{ color: "var(--muted)" }}>
                claimed{" "}
                <span style={{ color: "var(--ink-2)", fontWeight: 600 }}>
                  {q.claimed.toFixed(1)}
                </span>
              </span>
              <span style={{ color: "var(--muted)" }}>
                capped to{" "}
                <span style={{ color: "var(--warn)", fontWeight: 600 }}>
                  {q.capped_to.toFixed(1)}
                </span>
              </span>
            </div>
          ))}
        </div>
      )}
    </>
  );
};

const DomainCard: React.FC<{
  code: string;
  name: string;
  score: number | null;
  subdomains: Array<{
    code: string;
    name: string;
    score: number | null;
    capApplied: boolean;
    evidenceBlocked: number;
    evidenceBlockedQuestions: EvidenceBlockedQuestion[];
  }>;
}> = ({ code, name, score, subdomains }) => {
  const c = colorForScore(score);
  const lvl = levelForScore(score);
  const anyCapped = subdomains.some((s) => s.capApplied);
  return (
    <div className="domain-card">
      <div className="domain-card-head">
        <div className="domain-card-id">
          <span
            className="domain-code"
            style={{ color: c, background: `${c}22`, borderColor: `${c}44` }}
          >
            {code}
          </span>
          <div>
            <h3 className="domain-name">{name}</h3>
            <div className="domain-meta">
              <span>L{lvl.n} · {lvl.label}</span>
              <span className="dot" />
              <span>{subdomains.length} subdomains</span>
              {anyCapped && (
                <>
                  <span className="dot" />
                  <span className="chip-capped">Capped</span>
                </>
              )}
            </div>
          </div>
        </div>
        <div className="domain-score-wrap">
          <span className="num domain-score-num" style={{ color: c }}>
            {score != null ? score.toFixed(2) : "—"}
          </span>
          <span className="domain-score-of">/ 5.00</span>
        </div>
      </div>
      <div className="domain-card-body">
        {subdomains.map((s) => (
          <SubRow key={s.code} {...s} />
        ))}
      </div>
    </div>
  );
};

// ── Blind spots: role disagreement detail card ─────────────────────────────
interface BlindSpot {
  subdomain: string;
  variance: number;
  severity: "warning" | "critical";
  role_averages: Record<string, number>;
}

const ROLE_LABELS: Record<string, string> = {
  TECHNICIAN: "Technician",
  SUPERVISOR: "Supervisor",
  PLANNER: "Planner",
  MANAGER: "Manager",
  RELIABILITY_ENGINEER: "Reliability Eng.",
  UNKNOWN: "Unknown role",
};

const BlindSpotCard: React.FC<{
  spot: BlindSpot;
  subdomainName: (code: string) => string;
}> = ({ spot, subdomainName }) => {
  const isCritical = spot.severity === "critical";
  const tone = isCritical ? "var(--danger)" : "var(--warn)";
  const bg = isCritical ? "rgba(194, 83, 60, 0.10)" : "rgba(192, 138, 46, 0.10)";

  // Sort roles low → high so the "outliers" sit at the ends
  const entries = Object.entries(spot.role_averages || {}).sort((a, b) => a[1] - b[1]);
  const lowest = entries[0];
  const highest = entries[entries.length - 1];

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
          padding: "16px 22px",
          borderBottom: "1px solid var(--line-2)",
          gap: 14,
          flexWrap: "wrap",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 12, flexWrap: "wrap" }}>
          <span
            className="chip"
            style={{ background: bg, color: tone, textTransform: "uppercase", letterSpacing: "0.04em" }}
          >
            <span className="dot" />
            {spot.severity}
          </span>
          <span
            style={{
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: 12.5,
              fontWeight: 600,
              padding: "4px 8px",
              borderRadius: 6,
              border: `1px solid ${tone}44`,
              background: `${tone}18`,
              color: tone,
              letterSpacing: "0.04em",
            }}
          >
            {spot.subdomain}
          </span>
          <span
            style={{
              fontFamily: "'Instrument Serif', serif",
              fontSize: 20,
              color: "var(--ink)",
              lineHeight: 1,
            }}
          >
            {subdomainName(spot.subdomain)}
          </span>
        </div>
        <div style={{ display: "flex", alignItems: "baseline", gap: 6 }}>
          <span
            style={{
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: 10.5,
              color: "var(--muted)",
              textTransform: "uppercase",
              letterSpacing: "0.1em",
              fontWeight: 600,
            }}
          >
            Variance
          </span>
          <span
            style={{
              fontFamily: "'Instrument Serif', serif",
              fontSize: 28,
              color: tone,
              lineHeight: 1,
            }}
          >
            {spot.variance.toFixed(1)}
          </span>
        </div>
      </div>

      <div style={{ padding: "16px 22px" }}>
        <div
          style={{
            fontSize: 11,
            color: "var(--muted)",
            textTransform: "uppercase",
            letterSpacing: "0.08em",
            fontWeight: 600,
            marginBottom: 10,
          }}
        >
          Role averages on this subdomain
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          {entries.map(([role, score]) => {
            const pct = (score / 5) * 100;
            const isLow = lowest && role === lowest[0];
            const isHigh = highest && role === highest[0] && lowest !== highest;
            const c = colorForScore(score);
            return (
              <div
                key={role}
                style={{
                  display: "grid",
                  gridTemplateColumns: "150px 1fr 48px",
                  gap: 14,
                  alignItems: "center",
                }}
              >
                <span
                  style={{
                    fontSize: 12.5,
                    color: "var(--ink-2)",
                    fontWeight: isLow || isHigh ? 600 : 500,
                    display: "flex",
                    alignItems: "center",
                    gap: 6,
                  }}
                >
                  {ROLE_LABELS[role] || role}
                  {isLow && (
                    <span
                      style={{
                        fontSize: 9.5,
                        fontFamily: "'JetBrains Mono', monospace",
                        padding: "1px 5px",
                        borderRadius: 3,
                        background: "rgba(194, 83, 60, 0.10)",
                        color: "var(--danger)",
                        letterSpacing: "0.04em",
                      }}
                    >
                      LOW
                    </span>
                  )}
                  {isHigh && (
                    <span
                      style={{
                        fontSize: 9.5,
                        fontFamily: "'JetBrains Mono', monospace",
                        padding: "1px 5px",
                        borderRadius: 3,
                        background: "rgba(47,138,107,0.10)",
                        color: "var(--ok)",
                        letterSpacing: "0.04em",
                      }}
                    >
                      HIGH
                    </span>
                  )}
                </span>
                <div
                  style={{
                    position: "relative",
                    height: 10,
                    background: "var(--surface-2)",
                    borderRadius: 5,
                    overflow: "hidden",
                  }}
                >
                  <div
                    style={{
                      position: "absolute",
                      inset: 0,
                      display: "grid",
                      gridTemplateColumns: "repeat(5, 1fr)",
                      pointerEvents: "none",
                    }}
                  >
                    {[1, 2, 3, 4, 5].map((n) => (
                      <div
                        key={n}
                        style={{
                          borderRight: n < 5 ? "1px solid var(--line)" : "none",
                        }}
                      />
                    ))}
                  </div>
                  <div
                    style={{
                      position: "absolute",
                      left: 0,
                      top: 0,
                      bottom: 0,
                      width: `${pct}%`,
                      background: c,
                      borderRadius: "5px 0 0 5px",
                      transition: "width 0.4s ease-out",
                    }}
                  />
                </div>
                <span
                  style={{
                    fontFamily: "'Instrument Serif', serif",
                    fontSize: 18,
                    color: c,
                    textAlign: "right",
                    lineHeight: 1,
                  }}
                >
                  {score.toFixed(1)}
                </span>
              </div>
            );
          })}
        </div>

        {lowest && highest && lowest !== highest && (
          <div
            style={{
              marginTop: 14,
              padding: "10px 12px",
              borderRadius: 8,
              background: bg,
              borderLeft: `3px solid ${tone}`,
              fontSize: 12.5,
              color: "var(--ink-2)",
              lineHeight: 1.5,
            }}
          >
            <strong>{ROLE_LABELS[highest[0]] || highest[0]}s</strong> rate this
            subdomain <strong>{(highest[1] - lowest[1]).toFixed(1)}</strong> higher
            than <strong>{ROLE_LABELS[lowest[0]] || lowest[0]}s</strong> on average.
            {isCritical
              ? " That's a serious disconnect — interview both groups before trusting the headline score."
              : " Worth a follow-up to reconcile what each role is actually observing on the floor."}
          </div>
        )}
      </div>
    </div>
  );
};

const BlindSpotsSection: React.FC<{
  blindSpots: any[];
  subdomainName: (code: string) => string;
}> = ({ blindSpots, subdomainName }) => {
  const valid: BlindSpot[] = blindSpots
    .filter(
      (b) =>
        b &&
        typeof b === "object" &&
        b.subdomain &&
        typeof b.variance === "number" &&
        b.role_averages,
    )
    .sort((a, b) => b.variance - a.variance);

  if (valid.length === 0) return null;

  const critical = valid.filter((b) => b.severity === "critical").length;

  return (
    <div style={{ marginTop: 28 }}>
      <div className="domain-section-head" style={{ margin: "0 0 14px" }}>
        <h2 className="section-title" style={{ color: "var(--warn)" }}>
          Blind spots detected
        </h2>
        <div className="row" style={{ gap: 10, flexWrap: "wrap" }}>
          <span className="chip muted">
            {valid.length} subdomain{valid.length === 1 ? "" : "s"}
          </span>
          {critical > 0 && (
            <span
              className="chip"
              style={{ background: "rgba(194, 83, 60, 0.10)", color: "var(--danger)" }}
            >
              <span className="dot" />
              {critical} critical
            </span>
          )}
        </div>
      </div>

      <div
        className="card"
        style={{
          padding: "18px 22px",
          marginBottom: 18,
          display: "flex",
          gap: 14,
          alignItems: "flex-start",
        }}
      >
        <div
          style={{
            width: 38,
            height: 38,
            borderRadius: 10,
            background: "rgba(192, 138, 46, 0.12)",
            color: "var(--warn)",
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
            <path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
            <line x1="12" y1="9" x2="12" y2="13" />
            <line x1="12" y1="17" x2="12.01" y2="17" />
          </svg>
        </div>
        <div style={{ fontSize: 13, color: "var(--ink-2)", lineHeight: 1.55, maxWidth: 820 }}>
          A <strong>blind spot</strong> is a subdomain where different respondent
          roles disagree by 1.5+ points on the 1–5 scale. It usually means one
          group sees a problem the other doesn't — e.g. technicians know PMs
          aren't actually being followed while managers report the policy as in
          place. The headline score averages this out, so the disconnect is
          hidden in the rollup. Reconcile these before signing off.
        </div>
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
        {valid.map((spot, i) => (
          <BlindSpotCard
            key={`${spot.subdomain}-${i}`}
            spot={spot}
            subdomainName={subdomainName}
          />
        ))}
      </div>
    </div>
  );
};

type RadarView = "domains" | "pillars";

const PILLAR_GROUPS: Array<{ code: string; name: string; domains: string[] }> = [
  { code: "PEOPLE",     name: "People",     domains: ["WC", "LC"] },
  { code: "PROCESS",    name: "Process",    domains: ["WM", "SG"] },
  { code: "TECHNOLOGY", name: "Technology", domains: ["AI"] },
];


export { colorForScore, levelForScore, MATURITY_LEVELS, ScaleRuler, StatCard, SubRow, DomainCard, ROLE_LABELS, BlindSpotCard, BlindSpotsSection, PILLAR_GROUPS };
export type { EvidenceBlockedQuestion, BlindSpot, RadarView };
