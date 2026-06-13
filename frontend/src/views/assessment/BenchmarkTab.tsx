import React, { useEffect } from "react";
import { useV2Store } from "../../api/storeV2";
import { Card } from "../../components";
import { theme } from "../../styles/theme";

export const BenchmarkTab: React.FC<{ assessmentId: number }> = ({ assessmentId }) => {
  const {
    benchmark,
    benchmarkLoading,
    loadBenchmark,
    currentAssessment,
    scoringResult,
    domains,
  } = useV2Store();
  const domainName = (code: string) =>
    domains.find((d) => d.code === code)?.name || code;
  const hasScores =
    (currentAssessment?.overall_rmi != null &&
      currentAssessment.overall_rmi > 0) ||
    scoringResult != null;

  useEffect(() => {
    if (hasScores) {
      loadBenchmark(assessmentId);
    }
  }, [assessmentId, hasScores]);

  if (!hasScores)
    return (
      <div style={{ textAlign: "center", padding: "60px", color: "var(--muted)" }}>
        <div style={{ fontSize: "3rem", marginBottom: "16px" }}>📊</div>
        <h3 style={{ color: "var(--ink)" }}>Score the Assessment First</h3>
        <p>
          Go to the Interview tab, answer questions, then click "Calculate
          Scores" to enable benchmarking.
        </p>
      </div>
    );

  if (benchmarkLoading)
    return (
      <div style={{ textAlign: "center", padding: "40px" }}>
        <div className="spinner" />
      </div>
    );

  // Handle insufficient peers or no benchmark yet
  if (!benchmark || benchmark.status === "insufficient_peers") {
    const peerCount = benchmark?.peer_count ?? 0;
    const minReq = benchmark?.min_required ?? 5;
    return (
      <div style={{ padding: "0" }}>
        {/* Explanation Banner */}
        <Card>
          <div
            style={{
              padding: "24px",
              background: "var(--accent-soft)",
              borderRadius: "8px",
              borderLeft: "4px solid var(--accent)",
            }}
          >
            <h3
              style={{
                margin: "0 0 8px 0",
                fontSize: "1rem",
                color: "var(--accent)",
              }}
            >
              What is Benchmarking?
            </h3>
            <p
              style={{
                margin: "0 0 12px 0",
                fontSize: "0.875rem",
                color: "var(--ink-2)",
                lineHeight: 1.6,
              }}
            >
              Benchmarking compares this site's RMI scores against{" "}
              <strong>anonymized peer assessments</strong> from similar
              organizations. It shows where the site ranks in percentile terms
              (e.g., P75 = better than 75% of peers).
            </p>
            <div
              style={{
                display: "flex",
                gap: "16px",
                flexWrap: "wrap",
                fontSize: "0.8rem",
                color: "var(--muted)",
              }}
            >
              <span>
                🏭 Peers matched by:{" "}
                <strong>Industry, Size, Assessment Mode</strong>
              </span>
              <span>
                🔒 All peer data is <strong>anonymized</strong> — no site names
                revealed
              </span>
              <span>
                Minimum <strong>{minReq} peers</strong> required for
                statistical validity
              </span>
            </div>
          </div>
        </Card>

        <div
          style={{
            marginTop: "24px",
            textAlign: "center",
            padding: "40px",
            color: "var(--muted)",
          }}
        >
          <div style={{ fontSize: "2.5rem", marginBottom: "12px" }}>🔍</div>
          <h3 style={{ color: "var(--ink)", marginBottom: "8px" }}>
            Building Peer Group
          </h3>
          <p style={{ maxWidth: "500px", margin: "0 auto", lineHeight: 1.6 }}>
            Currently <strong>{peerCount}</strong> of <strong>{minReq}</strong>{" "}
            required comparable assessments found. As NextBelt conducts more
            assessments in this industry segment, benchmarking will
            automatically activate.
          </p>
          <div style={{ marginTop: "24px" }}>
            <Card>
              <div style={{ padding: "20px" }}>
                <div
                  style={{
                    fontSize: "0.75rem",
                    color: "var(--muted)",
                    textTransform: "uppercase",
                    letterSpacing: "0.05em",
                    marginBottom: "12px",
                  }}
                >
                  Your Current Score
                </div>
                <div
                  style={{
                    fontSize: "2.5rem",
                    fontWeight: 700,
                    color: theme.colors.primary,
                  }}
                >
                  {Number(currentAssessment?.overall_rmi ?? 0).toFixed(2)}
                </div>
                <div
                  style={{
                    fontSize: "0.825rem",
                    color: "var(--muted)",
                    marginTop: "4px",
                  }}
                >
                  {currentAssessment?.maturity_level}
                </div>
              </div>
            </Card>
          </div>
        </div>
      </div>
    );
  }

  const getQuartileColor = (q: number) => {
    if (q === 1) return "var(--ok)";
    if (q === 2) return theme.colors.primary;
    if (q === 3) return "var(--warn)";
    return "var(--danger)";
  };

  const getQuartileLabel = (q: number) => {
    if (q === 1) return "Top Quartile";
    if (q === 2) return "2nd Quartile";
    if (q === 3) return "3rd Quartile";
    return "Bottom Quartile";
  };

  return (
    <div>
      {/* Info Banner */}
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
          <div
            style={{ display: "flex", alignItems: "flex-start", gap: "12px" }}
          >
            <span style={{ fontSize: "1.25rem" }}>ℹ️</span>
            <div
              style={{
                fontSize: "0.825rem",
                color: "var(--ink-2)",
                lineHeight: 1.6,
              }}
            >
              <strong>How to read this:</strong> Percentile (P) shows what
              percentage of peer sites scored lower.
              <strong> P75</strong> = better than 75% of peers.{" "}
              <strong>Quartile 1</strong> = top 25%. Compared against{" "}
              <strong>{benchmark.peer_count}</strong> anonymized sites in the
              same industry.
            </div>
          </div>
        </div>
      </Card>

      {/* Summary Cards */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr 1fr 1fr",
          gap: "20px",
          marginBottom: "32px",
        }}
      >
        <Card>
          <div style={{ padding: "20px", textAlign: "center" }}>
            <div
              style={{
                fontSize: "0.7rem",
                color: "var(--muted)",
                textTransform: "uppercase",
                letterSpacing: "0.05em",
                marginBottom: "8px",
              }}
            >
              Your RMI Score
            </div>
            <div
              style={{
                fontSize: "2rem",
                fontWeight: 700,
                color: theme.colors.primary,
              }}
            >
              {Number(benchmark.overall_rmi ?? 0).toFixed(2)}
            </div>
          </div>
        </Card>
        <Card>
          <div style={{ padding: "20px", textAlign: "center" }}>
            <div
              style={{
                fontSize: "0.7rem",
                color: "var(--muted)",
                textTransform: "uppercase",
                letterSpacing: "0.05em",
                marginBottom: "8px",
              }}
            >
              Percentile Rank
            </div>
            <div
              style={{
                fontSize: "2rem",
                fontWeight: 700,
                color: getQuartileColor(benchmark.quartile),
              }}
            >
              P{benchmark.overall_percentile}
            </div>
            <div
              style={{ fontSize: "0.7rem", color: "#999", marginTop: "2px" }}
            >
              Better than {benchmark.overall_percentile}% of peers
            </div>
          </div>
        </Card>
        <Card>
          <div style={{ padding: "20px", textAlign: "center" }}>
            <div
              style={{
                fontSize: "0.7rem",
                color: "var(--muted)",
                textTransform: "uppercase",
                letterSpacing: "0.05em",
                marginBottom: "8px",
              }}
            >
              Quartile
            </div>
            <div
              style={{
                fontSize: "2rem",
                fontWeight: 700,
                color: getQuartileColor(benchmark.quartile),
              }}
            >
              Q{benchmark.quartile}
            </div>
            <div
              style={{ fontSize: "0.7rem", color: "#999", marginTop: "2px" }}
            >
              {getQuartileLabel(benchmark.quartile)}
            </div>
          </div>
        </Card>
        <Card>
          <div style={{ padding: "20px", textAlign: "center" }}>
            <div
              style={{
                fontSize: "0.7rem",
                color: "var(--muted)",
                textTransform: "uppercase",
                letterSpacing: "0.05em",
                marginBottom: "8px",
              }}
            >
              Peer Group
            </div>
            <div
              style={{ fontSize: "2rem", fontWeight: 700, color: "var(--ink-2)" }}
            >
              {benchmark.peer_count}
            </div>
            <div
              style={{ fontSize: "0.7rem", color: "#999", marginTop: "2px" }}
            >
              comparable sites
            </div>
          </div>
        </Card>
      </div>

      {/* Peer Group Statistics */}
      {benchmark.peer_stats && benchmark.peer_stats.mean != null && (
        <>
          <h3
            style={{ fontSize: "1rem", marginBottom: "12px", color: "var(--ink)" }}
          >
            Peer Group Statistics
          </h3>
          <Card>
            <div style={{ padding: "20px" }}>
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(4, 1fr)",
                  gap: "16px",
                  textAlign: "center",
                }}
              >
                <div>
                  <div
                    style={{
                      fontSize: "0.7rem",
                      color: "#999",
                      textTransform: "uppercase",
                      marginBottom: "4px",
                    }}
                  >
                    Peer Average
                  </div>
                  <div
                    style={{
                      fontSize: "1.25rem",
                      fontWeight: 700,
                      color: "#333",
                    }}
                  >
                    {benchmark.peer_stats.mean?.toFixed(2)}
                  </div>
                </div>
                <div>
                  <div
                    style={{
                      fontSize: "0.7rem",
                      color: "#999",
                      textTransform: "uppercase",
                      marginBottom: "4px",
                    }}
                  >
                    Peer Min
                  </div>
                  <div
                    style={{
                      fontSize: "1.25rem",
                      fontWeight: 700,
                      color: "var(--danger)",
                    }}
                  >
                    {benchmark.peer_stats.min?.toFixed(2)}
                  </div>
                </div>
                <div>
                  <div
                    style={{
                      fontSize: "0.7rem",
                      color: "#999",
                      textTransform: "uppercase",
                      marginBottom: "4px",
                    }}
                  >
                    Peer Max
                  </div>
                  <div
                    style={{
                      fontSize: "1.25rem",
                      fontWeight: 700,
                      color: "var(--ok)",
                    }}
                  >
                    {benchmark.peer_stats.max?.toFixed(2)}
                  </div>
                </div>
                <div>
                  <div
                    style={{
                      fontSize: "0.7rem",
                      color: "#999",
                      textTransform: "uppercase",
                      marginBottom: "4px",
                    }}
                  >
                    Std Deviation
                  </div>
                  <div
                    style={{
                      fontSize: "1.25rem",
                      fontWeight: 700,
                      color: "#666",
                    }}
                  >
                    {benchmark.peer_stats.std_dev?.toFixed(2) ?? "—"}
                  </div>
                </div>
              </div>
              {/* Visual position indicator */}
              <div
                style={{
                  marginTop: "20px",
                  padding: "16px",
                  background: "var(--surface-2)",
                  borderRadius: "8px",
                }}
              >
                <div
                  style={{
                    fontSize: "0.75rem",
                    color: "#666",
                    marginBottom: "8px",
                  }}
                >
                  Your position among peers:
                </div>
                <div
                  style={{
                    position: "relative",
                    height: "24px",
                    background: "var(--line)",
                    borderRadius: "12px",
                    overflow: "visible",
                  }}
                >
                  {/* Peer range bar */}
                  <div
                    style={{
                      position: "absolute",
                      height: "100%",
                      borderRadius: "12px",
                      background: "linear-gradient(90deg, #FCD34D, #34D399)",
                      left: `${((benchmark.peer_stats.min ?? 1) / 5) * 100}%`,
                      width: `${
                        (((benchmark.peer_stats.max ?? 5) -
                          (benchmark.peer_stats.min ?? 1)) /
                          5) *
                        100
                      }%`,
                    }}
                  />
                  {/* Your score marker */}
                  <div
                    style={{
                      position: "absolute",
                      top: "-4px",
                      width: "32px",
                      height: "32px",
                      borderRadius: "50%",
                      background: theme.colors.primary,
                      border: "3px solid white",
                      boxShadow: "0 2px 8px rgba(0,0,0,0.2)",
                      left: `calc(${
                        ((benchmark.overall_rmi ?? 0) / 5) * 100
                      }% - 16px)`,
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      color: "white",
                      fontSize: "0.6rem",
                      fontWeight: 700,
                    }}
                  >
                    You
                  </div>
                </div>
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    marginTop: "8px",
                    fontSize: "0.7rem",
                    color: "#999",
                  }}
                >
                  <span>1.0</span>
                  <span>2.0</span>
                  <span>3.0</span>
                  <span>4.0</span>
                  <span>5.0</span>
                </div>
              </div>
            </div>
          </Card>
        </>
      )}

      {/* Domain Percentiles */}
      {benchmark.domain_percentiles &&
        Object.keys(benchmark.domain_percentiles).length > 0 && (
          <div style={{ marginTop: "24px" }}>
            <h3
              style={{
                fontSize: "1rem",
                marginBottom: "12px",
                color: "var(--ink)",
              }}
            >
              Domain Percentiles
            </h3>
            <Card>
              <div style={{ padding: "20px" }}>
                {Object.entries(benchmark.domain_percentiles).map(
                  ([domain, data]: [string, any]) => {
                    const pct =
                      typeof data === "object" ? data.percentile : data;
                    const score = typeof data === "object" ? data.score : null;
                    const dq = typeof data === "object" ? data.quartile : null;
                    return (
                      <div
                        key={domain}
                        style={{
                          display: "flex",
                          alignItems: "center",
                          gap: "12px",
                          padding: "12px 0",
                          borderBottom: "1px solid rgba(0,0,0,0.04)",
                        }}
                      >
                        <div
                          style={{
                            width: "200px",
                            fontWeight: 600,
                            fontSize: "0.825rem",
                            color: "var(--ink-2)",
                          }}
                        >
                          {domainName(domain)}
                        </div>
                        {score != null && (
                          <div
                            style={{
                              width: "50px",
                              fontSize: "0.8rem",
                              fontWeight: 600,
                              color: "#666",
                            }}
                          >
                            {score.toFixed(1)}
                          </div>
                        )}
                        <div
                          style={{
                            flex: 1,
                            height: "10px",
                            background: "var(--line)",
                            borderRadius: "5px",
                            overflow: "hidden",
                          }}
                        >
                          <div
                            style={{
                              height: "100%",
                              width: `${pct ?? 0}%`,
                              borderRadius: "5px",
                              background:
                                (pct ?? 0) >= 75
                                  ? "var(--ok)"
                                  : (pct ?? 0) >= 50
                                  ? theme.colors.primary
                                  : (pct ?? 0) >= 25
                                  ? "var(--warn)"
                                  : "var(--danger)",
                              transition: "width 0.5s ease",
                            }}
                          />
                        </div>
                        <div
                          style={{
                            width: "45px",
                            textAlign: "right",
                            fontWeight: 700,
                            fontSize: "0.825rem",
                            color: getQuartileColor(dq ?? 4),
                          }}
                        >
                          P{pct ?? 0}
                        </div>
                        {dq != null && (
                          <div
                            style={{
                              width: "30px",
                              textAlign: "center",
                              fontSize: "0.7rem",
                              fontWeight: 600,
                              color: getQuartileColor(dq),
                              background: `${getQuartileColor(dq)}15`,
                              padding: "2px 6px",
                              borderRadius: "4px",
                            }}
                          >
                            Q{dq}
                          </div>
                        )}
                      </div>
                    );
                  }
                )}
              </div>
            </Card>
          </div>
        )}

      {/* Assessment Tips */}
      <Card>
        <div
          style={{
            padding: "16px 20px",
            marginTop: "24px",
            background: "#FFFBEB",
            borderRadius: "8px",
            borderLeft: "4px solid #F59E0B",
          }}
        >
          <h4
            style={{
              margin: "0 0 8px 0",
              fontSize: "0.875rem",
              color: "#92400E",
            }}
          >
            Assessor Guidance
          </h4>
          <ul
            style={{
              margin: 0,
              paddingLeft: "20px",
              fontSize: "0.8rem",
              color: "#78350F",
              lineHeight: 1.8,
            }}
          >
            <li>
              Percentile rankings are based on{" "}
              <strong>anonymized peer data</strong> — never share raw peer
              scores with clients.
            </li>
            <li>
              Q1 (Top Quartile) sites typically have mature, proactive
              reliability programs with formal processes.
            </li>
            <li>
              Domain-level gaps highlight where the client can focus improvement
              efforts for maximum impact.
            </li>
            <li>
              Use the <strong>Practices tab</strong> to generate specific,
              prioritized improvement recommendations.
            </li>
          </ul>
        </div>
      </Card>
    </div>
  );
};

// ═══════════════════════════════════════════
//  Practices Tab
// ═══════════════════════════════════════════
