import React, { useState, useEffect } from "react";
import { generateAndDownloadReport } from "../../api/clientV2";
import { useV2Store } from "../../api/storeV2";
import { DomainRadar } from "../../components";
import { colorForScore, levelForScore, ScaleRuler, StatCard, DomainCard, BlindSpotsSection, PILLAR_GROUPS } from "./shared";
import type { EvidenceBlockedQuestion, RadarView } from "./shared";

export const ScoresTab: React.FC<{ assessmentId: number }> = ({ assessmentId }) => {
  const { scoringResult, scoringLoading, calculateScores, domains, progress, currentAssessment } =
    useV2Store();
  const [radarView, setRadarView] = useState<RadarView>("domains");
  const [reportBusy, setReportBusy] = useState(false);
  const [reportErr, setReportErr] = useState<string | null>(null);

  const handleDownloadReport = async () => {
    setReportErr(null);
    setReportBusy(true);
    try {
      await generateAndDownloadReport(
        assessmentId,
        currentAssessment?.organization_name || "Client",
        currentAssessment?.site_name || "Site",
      );
    } catch (e: any) {
      setReportErr(e?.response?.data?.detail || "Report generation failed.");
    } finally {
      setReportBusy(false);
    }
  };

  const domainName = (code: string) =>
    domains.find((d) => d.code === code)?.name || code;
  const subdomainName = (code: string) => {
    for (const d of domains) {
      const sd = d.subdomains.find((s: any) => s.code === code);
      if (sd) return sd.name;
    }
    return code;
  };

  useEffect(() => {
    if (!scoringResult) calculateScores(assessmentId);
  }, [assessmentId]);

  if (scoringLoading)
    return (
      <div style={{ textAlign: "center", padding: "40px" }}>
        <div className="spinner" />
      </div>
    );
  if (!scoringResult)
    return (
      <div style={{ textAlign: "center", padding: "40px", color: "var(--muted)" }}>
        No scores available. Complete some questions first.
      </div>
    );

  const {
    overall_rmi,
    confidence,
    confidence_score,
    blind_spots,
    iso_55001_readiness,
  } = scoringResult;
  const confidenceVal = confidence_score ?? confidence ?? 0;
  const overallTone = colorForScore(overall_rmi);
  const overallLevel = levelForScore(overall_rmi);
  const isoPct = Math.round(((iso_55001_readiness ?? 0) as number) * 100);
  const blindCount = (blind_spots ?? []).length;

  const domainScores = Object.entries(scoringResult.domains || {}).map(
    ([code, data]: [string, any]) => ({
      code,
      name: domainName(code),
      score: data.score as number | null,
      subdomains: Object.entries(data.subdomains || {}).map(
        ([sdCode, sdData]: [string, any]) => ({
          code: sdCode,
          name: subdomainName(sdCode),
          score: (sdData.final_score ?? null) as number | null,
          capApplied: !!sdData.cap_applied,
          evidenceBlocked: Number(sdData.evidence_blocked || 0),
          evidenceBlockedQuestions: (sdData.evidence_blocked_questions ||
            []) as EvidenceBlockedQuestion[],
        }),
      ),
    }),
  );

  const totalEvidenceBlocked = domainScores.reduce(
    (sum, d) => sum + d.subdomains.reduce((s, sd) => s + sd.evidenceBlocked, 0),
    0,
  );

  const answered = progress?.answered ?? 0;
  const total = progress?.total_questions ?? 0;

  return (
    <div>
      {/* Header + report download */}
      <div
        className="row"
        style={{ justifyContent: "space-between", alignItems: "center", marginBottom: 14, gap: 12, flexWrap: "wrap" }}
      >
        <div>
          <h2 style={{ margin: 0, fontSize: 18, color: "var(--ink)" }}>Scores & Maturity</h2>
          <div style={{ color: "var(--muted)", fontSize: 12 }}>
            Executive view across pillars, domains, and subdomains
          </div>
        </div>
        <div className="row" style={{ gap: 10, alignItems: "center" }}>
          {reportErr && (
            <span role="alert" style={{ color: "var(--danger)", fontSize: 12 }}>
              {reportErr}
            </span>
          )}
          <button className="btn primary" disabled={reportBusy} onClick={handleDownloadReport}>
            {reportBusy ? "Generating PDF…" : "Download Executive Report"}
          </button>
        </div>
      </div>

      {/* KPI strip */}
      <div className="stat-strip">
        <StatCard
          label="Overall RMI"
          value={(overall_rmi ?? 0).toFixed(2)}
          unit="/ 5.0"
          tone={overallTone}
          sub={
            <span>
              <span
                style={{
                  display: "inline-block",
                  width: 6,
                  height: 6,
                  borderRadius: 999,
                  background: overallTone,
                  marginRight: 6,
                  verticalAlign: "middle",
                }}
              />
              Level {overallLevel.n} · {overallLevel.label}
            </span>
          }
          hint={
            total > 0
              ? `${answered}/${total} questions answered`
              : "Score recalculates on submission"
          }
        />
        <StatCard
          label="Confidence"
          value={`${Math.round(confidenceVal * 100)}%`}
          tone={confidenceVal >= 0.8 ? "var(--ok)" : confidenceVal >= 0.5 ? "var(--warn)" : "var(--danger)"}
          sub={confidenceVal >= 0.8 ? "Evidence well supported" : "Coverage gaps reduce confidence"}
          hint={confidenceVal >= 0.8 ? "No unresolved flags" : "Add evidence to lift confidence"}
        />
        <StatCard
          label="ISO 55001 Ready"
          value={`${isoPct}%`}
          tone={isoPct < 50 ? "var(--danger)" : isoPct < 70 ? "var(--warn)" : "var(--ok)"}
          sub={
            isoPct < 50
              ? "Below readiness floor"
              : isoPct < 70
              ? "Approaching readiness"
              : "On track"
          }
          hint="Subdomains scoring ≥ 3.0 (Systematic)"
        />
        <StatCard
          label="Blind Spots"
          value={String(blindCount)}
          tone={blindCount === 0 ? "var(--ok)" : "var(--warn)"}
          sub={blindCount === 0 ? "None detected" : `${blindCount} subdomain${blindCount === 1 ? "" : "s"}`}
          hint="Areas with cross-role disagreement"
        />
      </div>

      {/* Radar snapshot */}
      {(() => {
        // P/P/T rollup: average constituent domain scores (skip nulls)
        const pillarScores = PILLAR_GROUPS.map((g) => {
          const vals = domainScores
            .filter((d) => g.domains.includes(d.code))
            .map((d) => d.score)
            .filter((s): s is number => s != null);
          const avg =
            vals.length > 0 ? vals.reduce((a, b) => a + b, 0) / vals.length : null;
          return {
            code: g.code,
            name: g.name,
            score: avg != null ? Number(avg.toFixed(2)) : null,
            domains: g.domains,
          };
        });

        const isPillars = radarView === "pillars";
        const radarPoints = isPillars
          ? pillarScores.map((p) => ({ code: p.name, name: p.name, score: p.score }))
          : domainScores.map((d) => ({ code: d.code, name: d.name, score: d.score }));
        const legendRows = isPillars ? pillarScores : domainScores;
        const headline = isPillars
          ? "People, Process & Technology rollup"
          : "Where you stand across the five domains";
        const sublabel = isPillars
          ? "3-pillar executive view"
          : "5-domain snapshot";
        const description = isPillars ? (
          <>
            The 5 maturity domains roll up under the classic People / Process /
            Technology trinity. Each pillar score is the mean of its
            constituent domains. Use this for exec readouts; switch back to
            5-domain for prescriptive analysis.
          </>
        ) : (
          <>
            Each axis is one domain on the 1–5 maturity scale. The dashed ring
            is your target ({(3.0).toFixed(1)}); the filled shape is your current
            score. Domains where the polygon falls short of the dashed ring are
            the ones to lift next.
          </>
        );

        return (
          <section
            className="card radar-snapshot"
            style={{ padding: "28px 32px", marginBottom: 24 }}
          >
            <div>
              <DomainRadar
                domains={radarPoints}
                overall={overall_rmi ?? null}
                target={3.0}
                size={360}
              />
            </div>
            <div>
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  gap: 12,
                  flexWrap: "wrap",
                  marginBottom: 10,
                }}
              >
                <div className="label">{sublabel}</div>
                <div className="seg" role="tablist" aria-label="Radar view">
                  <button
                    type="button"
                    role="tab"
                    aria-selected={radarView === "domains"}
                    className={radarView === "domains" ? "on" : ""}
                    onClick={() => setRadarView("domains")}
                  >
                    5 Domains
                  </button>
                  <button
                    type="button"
                    role="tab"
                    aria-selected={radarView === "pillars"}
                    className={radarView === "pillars" ? "on" : ""}
                    onClick={() => setRadarView("pillars")}
                  >
                    P · P · T
                  </button>
                </div>
              </div>
              <h3
                style={{
                  fontFamily: "'Instrument Serif', serif",
                  fontWeight: 400,
                  fontSize: 26,
                  letterSpacing: "-0.01em",
                  margin: "0 0 10px",
                  color: "var(--ink)",
                }}
              >
                {headline}
              </h3>
              <p
                style={{
                  fontSize: 13,
                  color: "var(--muted)",
                  lineHeight: 1.55,
                  margin: "0 0 18px",
                  maxWidth: 520,
                }}
              >
                {description}
              </p>
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: isPillars ? "1fr" : "1fr 1fr",
                  gap: "10px 24px",
                }}
              >
                {legendRows.map((row) => {
                  const c = colorForScore(row.score);
                  const isPillar = isPillars;
                  const tag = isPillar
                    ? (row as typeof pillarScores[number]).domains.join(" + ")
                    : row.code;
                  return (
                    <div
                      key={row.code}
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: 10,
                        fontSize: 13,
                      }}
                    >
                      <span
                        style={{
                          fontFamily: "'JetBrains Mono', monospace",
                          fontSize: 11,
                          fontWeight: 600,
                          padding: "3px 8px",
                          borderRadius: 6,
                          border: `1px solid ${c}44`,
                          background: `${c}18`,
                          color: c,
                          letterSpacing: "0.04em",
                          whiteSpace: "nowrap",
                        }}
                      >
                        {isPillar ? row.name.toUpperCase() : row.code}
                      </span>
                      <span
                        style={{
                          color: "var(--ink-2)",
                          flex: 1,
                          overflow: "hidden",
                          textOverflow: "ellipsis",
                          whiteSpace: "nowrap",
                        }}
                      >
                        {isPillar ? (
                          <span style={{ color: "var(--muted)", fontSize: 12 }}>
                            {tag}
                          </span>
                        ) : (
                          row.name
                        )}
                      </span>
                      <span
                        style={{
                          fontFamily: "'Instrument Serif', serif",
                          fontSize: 18,
                          color: c,
                          lineHeight: 1,
                        }}
                      >
                        {row.score != null ? row.score.toFixed(2) : "—"}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>
          </section>
        );
      })()}

      {/* Section head + scale ruler */}
      <div className="domain-section-head">
        <h2 className="section-title">Domain scores</h2>
        <div className="row" style={{ gap: 14, flexWrap: "wrap" }}>
          <span className="chip muted">
            <svg
              width="11"
              height="11"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <circle cx="12" cy="12" r="10" />
              <circle cx="12" cy="12" r="6" />
              <circle cx="12" cy="12" r="2" />
            </svg>
            Target 3.0
          </span>
          <ScaleRuler />
        </div>
      </div>

      {totalEvidenceBlocked > 0 && (
        <div
          style={{
            display: "flex",
            alignItems: "flex-start",
            gap: 14,
            padding: "14px 18px",
            marginBottom: 14,
            borderRadius: "var(--radius)",
            background: "rgba(192, 138, 46, 0.10)",
            border: "1px solid rgba(192, 138, 46, 0.30)",
          }}
        >
          <div
            style={{
              width: 32,
              height: 32,
              borderRadius: 8,
              background: "rgba(192, 138, 46, 0.18)",
              color: "var(--warn)",
              display: "grid",
              placeItems: "center",
              flexShrink: 0,
            }}
          >
            <svg
              width="16"
              height="16"
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
          <div style={{ fontSize: 13, color: "var(--ink-2)", lineHeight: 1.55 }}>
            <strong>{totalEvidenceBlocked}</strong> question{totalEvidenceBlocked === 1 ? "" : "s"} scored
            ≥ 4 (Proactive/Prescriptive) on items that require auditable
            evidence — each is capped at 3.0 until accepted evidence is on file.
            Look for the <span style={{
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: 11,
              padding: "2px 6px",
              borderRadius: 4,
              background: "rgba(192, 138, 46, 0.18)",
              color: "var(--warn)",
              fontWeight: 600,
            }}>NO EVID.</span> chip on a subdomain row, click it to see which
            questions need evidence to lift the score.
          </div>
        </div>
      )}

      <div className="domain-stack">
        {domainScores.map((d) => (
          <DomainCard
            key={d.code}
            code={d.code}
            name={d.name}
            score={d.score}
            subdomains={d.subdomains}
          />
        ))}
      </div>

      {/* Blind spots */}
      {blindCount > 0 && (
        <BlindSpotsSection
          blindSpots={blind_spots ?? []}
          subdomainName={subdomainName}
        />
      )}
    </div>
  );
};

// ═══════════════════════════════════════════
//  Benchmark Tab
// ═══════════════════════════════════════════
