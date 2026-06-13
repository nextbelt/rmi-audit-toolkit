import React, { useState, useEffect } from "react";
import { useV2Store } from "../../api/storeV2";
import { Card } from "../../components";
import { theme } from "../../styles/theme";

export const PracticesTab: React.FC<{ assessmentId: number }> = ({ assessmentId }) => {
  const {
    recommendations,
    recommendationsData,
    recommendationsLoading,
    loadRecommendations,
    currentAssessment,
    scoringResult,
  } = useV2Store();
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const hasScores =
    (currentAssessment?.overall_rmi != null &&
      currentAssessment.overall_rmi > 0) ||
    scoringResult != null;

  useEffect(() => {
    if (hasScores) {
      loadRecommendations(assessmentId);
    }
  }, [assessmentId, hasScores]);

  if (!hasScores)
    return (
      <div style={{ textAlign: "center", padding: "60px", color: "var(--muted)" }}>
        <div style={{ fontSize: "3rem", marginBottom: "16px" }}>📚</div>
        <h3 style={{ color: "var(--ink)" }}>Score the Assessment First</h3>
        <p>
          Go to the Interview tab, answer questions, then click "Calculate
          Scores" to generate improvement recommendations.
        </p>
      </div>
    );

  if (recommendationsLoading)
    return (
      <div style={{ textAlign: "center", padding: "40px" }}>
        <div className="spinner" />
      </div>
    );

  const pathway = recommendationsData?.pathway;

  const getImpactBadge = (impact: string) => {
    const colors: Record<string, { bg: string; text: string }> = {
      high: { bg: "rgba(13,138,94,0.1)", text: "var(--ok)" },
      medium: { bg: "rgba(184,134,11,0.1)", text: "var(--warn)" },
      low: { bg: "rgba(102,102,102,0.1)", text: "var(--muted)" },
    };
    const c = colors[impact] || colors.medium;
    return { background: c.bg, color: c.text };
  };

  const getEffortBadge = (effort: string) => {
    const colors: Record<string, { bg: string; text: string }> = {
      low: { bg: "rgba(13,138,94,0.1)", text: "var(--ok)" },
      medium: { bg: "rgba(184,134,11,0.1)", text: "var(--warn)" },
      high: { bg: "rgba(197,48,48,0.1)", text: "var(--danger)" },
    };
    const c = colors[effort] || colors.medium;
    return { background: c.bg, color: c.text };
  };

  return (
    <div>
      {/* Maturity Pathway Card */}
      {pathway && (
        <Card>
          <div
            style={{
              padding: "20px",
              background: "var(--surface-2)",
              borderRadius: "8px",
              borderLeft: "4px solid var(--ok)",
              marginBottom: "24px",
            }}
          >
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: "12px",
                marginBottom: "12px",
              }}
            >
              <span style={{ fontSize: "1.5rem" }}>🎯</span>
              <div>
                <h3 style={{ margin: 0, fontSize: "1rem", color: "var(--ok)" }}>
                  Maturity Pathway: Level {pathway.from_level} → Level{" "}
                  {pathway.to_level}
                </h3>
                <div
                  style={{
                    fontSize: "0.825rem",
                    color: "var(--ok)",
                    marginTop: "2px",
                  }}
                >
                  Focus: <strong>{pathway.focus}</strong> · Timeline:{" "}
                  <strong>{pathway.typical_timeline}</strong>
                </div>
              </div>
            </div>
            <div
              style={{
                display: "flex",
                gap: "8px",
                flexWrap: "wrap",
                marginTop: "8px",
              }}
            >
              {(pathway.key_themes || []).map((t: string, i: number) => (
                <span
                  key={i}
                  style={{
                    fontSize: "0.75rem",
                    padding: "4px 10px",
                    borderRadius: "12px",
                    background: "rgba(13,138,94,0.08)",
                    color: "var(--ok)",
                    fontWeight: 500,
                  }}
                >
                  {t}
                </span>
              ))}
            </div>
          </div>
        </Card>
      )}

      {/* Assessor Guidance */}
      <Card>
        <div
          style={{
            padding: "16px 20px",
            background: "var(--accent-soft)",
            borderRadius: "8px",
            borderLeft: "4px solid var(--accent)",
            marginBottom: "24px",
          }}
        >
          <h4
            style={{
              margin: "0 0 8px 0",
              fontSize: "0.875rem",
              color: "var(--accent)",
            }}
          >
            Assessor Guidance — Presenting Recommendations
          </h4>
          <ul
            style={{
              margin: 0,
              paddingLeft: "20px",
              fontSize: "0.8rem",
              color: "var(--ink-2)",
              lineHeight: 1.8,
            }}
          >
            <li>
              <strong>Priority Score</strong> combines impact potential,
              feasibility (inverse of effort), and urgency (lower scores = more
              urgent).
            </li>
            <li>
              Start with <strong>high-impact, low-effort</strong> quick wins to
              build momentum.
            </li>
            <li>
              Critical path items (🔴) are prerequisites — they must be
              addressed before higher maturity levels are achievable.
            </li>
            <li>
              Discuss timelines and tools with the client to build a realistic
              implementation roadmap.
            </li>
          </ul>
        </div>
      </Card>

      {/* Summary */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          marginBottom: "16px",
        }}
      >
        <h3 style={{ fontSize: "1rem", margin: 0, color: "var(--ink)" }}>
          Top Improvement Recommendations
          <span
            style={{
              fontWeight: 400,
              color: "#999",
              marginLeft: "8px",
              fontSize: "0.825rem",
            }}
          >
            (
            {recommendationsData?.total_recommendations ??
              recommendations.length}{" "}
            total, showing top {recommendations.length})
          </span>
        </h3>
      </div>

      {/* No recommendations message */}
      {recommendations.length === 0 && (
        <div style={{ textAlign: "center", padding: "40px", color: "#666" }}>
          <div style={{ fontSize: "2.5rem", marginBottom: "12px" }}>📋</div>
          <h3 style={{ color: "var(--ink)" }}>No Recommendations Generated</h3>
          <p>
            This can happen if the practice library is still being loaded or if
            all subdomains are already at maximum maturity. Try recalculating
            scores.
          </p>
        </div>
      )}

      {/* Recommendation Cards */}
      <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
        {recommendations.map((rec, i) => {
          const isExpanded = expandedId === rec.practice_id;
          return (
            <Card key={rec.practice_id}>
              <div style={{ padding: "20px" }}>
                {/* Header Row */}
                <div
                  style={{
                    display: "flex",
                    gap: "16px",
                    alignItems: "flex-start",
                    cursor: "pointer",
                  }}
                  onClick={() =>
                    setExpandedId(isExpanded ? null : rec.practice_id)
                  }
                >
                  <div
                    style={{
                      width: "32px",
                      height: "32px",
                      borderRadius: "50%",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      background: i < 3 ? theme.colors.primary : "var(--line)",
                      color: i < 3 ? "#fff" : "#666",
                      fontWeight: 700,
                      fontSize: "0.875rem",
                      flexShrink: 0,
                    }}
                  >
                    {i + 1}
                  </div>
                  <div style={{ flex: 1 }}>
                    <div
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: "8px",
                        marginBottom: "4px",
                      }}
                    >
                      <span
                        style={{
                          fontWeight: 600,
                          fontSize: "0.95rem",
                          color: "var(--ink)",
                        }}
                      >
                        {rec.title}
                      </span>
                    </div>
                    <div
                      style={{
                        fontSize: "0.8rem",
                        color: "#666",
                        marginBottom: "8px",
                      }}
                    >
                      {rec.subdomain_code} · {rec.subdomain_name}
                    </div>

                    {/* Badges */}
                    <div
                      style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}
                    >
                      <span
                        style={{
                          fontSize: "0.7rem",
                          padding: "2px 8px",
                          borderRadius: "10px",
                          background: "var(--line)",
                          color: "#333",
                          fontWeight: 600,
                        }}
                      >
                        Score {rec.current_score?.toFixed(1)} → Level{" "}
                        {rec.target_level}
                      </span>
                      <span
                        style={{
                          fontSize: "0.7rem",
                          padding: "2px 8px",
                          borderRadius: "10px",
                          fontWeight: 600,
                          ...getImpactBadge(rec.impact),
                        }}
                      >
                        Impact: {rec.impact}
                      </span>
                      <span
                        style={{
                          fontSize: "0.7rem",
                          padding: "2px 8px",
                          borderRadius: "10px",
                          fontWeight: 600,
                          ...getEffortBadge(rec.effort),
                        }}
                      >
                        Effort: {rec.effort}
                      </span>
                      {rec.timeline && (
                        <span
                          style={{
                            fontSize: "0.7rem",
                            padding: "2px 8px",
                            borderRadius: "10px",
                            background: `${theme.colors.primary}10`,
                            color: theme.colors.primary,
                            fontWeight: 600,
                          }}
                        >
                          ⏱ {rec.timeline}
                        </span>
                      )}
                      <span
                        style={{
                          fontSize: "0.7rem",
                          padding: "2px 8px",
                          borderRadius: "10px",
                          background: "var(--surface-2)",
                          color: "#999",
                          fontWeight: 600,
                        }}
                      >
                        Priority: {((rec.priority_score ?? 0) * 100).toFixed(0)}
                      </span>
                    </div>
                  </div>
                  <span
                    style={{
                      fontSize: "0.75rem",
                      color: "#999",
                      marginTop: "4px",
                    }}
                  >
                    {isExpanded ? "▾" : "▸"}
                  </span>
                </div>

                {/* Expanded Details */}
                {isExpanded && (
                  <div
                    style={{
                      marginTop: "16px",
                      paddingTop: "16px",
                      borderTop: "1px solid var(--line)",
                    }}
                  >
                    {rec.description && (
                      <div
                        style={{
                          fontSize: "0.85rem",
                          color: "#333",
                          lineHeight: 1.7,
                          marginBottom: "16px",
                        }}
                      >
                        {rec.description}
                      </div>
                    )}

                    <div
                      style={{
                        display: "grid",
                        gridTemplateColumns: "1fr 1fr",
                        gap: "16px",
                      }}
                    >
                      {/* Success Metrics */}
                      {rec.success_metrics &&
                        rec.success_metrics.length > 0 && (
                          <div>
                            <div
                              style={{
                                fontSize: "0.75rem",
                                fontWeight: 700,
                                color: "var(--ok)",
                                textTransform: "uppercase",
                                marginBottom: "6px",
                              }}
                            >
                              Success Metrics
                            </div>
                            <ul
                              style={{
                                margin: 0,
                                paddingLeft: "16px",
                                fontSize: "0.8rem",
                                color: "#333",
                                lineHeight: 1.8,
                              }}
                            >
                              {rec.success_metrics.map(
                                (m: string, j: number) => (
                                  <li key={j}>{m}</li>
                                )
                              )}
                            </ul>
                          </div>
                        )}

                      {/* Tools */}
                      {rec.tools && rec.tools.length > 0 && (
                        <div>
                          <div
                            style={{
                              fontSize: "0.75rem",
                              fontWeight: 700,
                              color: theme.colors.primary,
                              textTransform: "uppercase",
                              marginBottom: "6px",
                            }}
                          >
                            🛠 Tools & Templates
                          </div>
                          <ul
                            style={{
                              margin: 0,
                              paddingLeft: "16px",
                              fontSize: "0.8rem",
                              color: "#333",
                              lineHeight: 1.8,
                            }}
                          >
                            {rec.tools.map((t: string, j: number) => (
                              <li key={j}>{t}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </Card>
          );
        })}
      </div>
    </div>
  );
};

// ═══════════════════════════════════════════
//  ISO 55001 Gap Report Tab
// ═══════════════════════════════════════════
