import React, { useState, useEffect, useMemo, useCallback, useRef } from "react";
import { useNavigate, useParams } from "react-router-dom";
import type { QuestionV2 } from "../api/clientV2";
import { useV2Store } from "../api/storeV2";
import { Card, EvidenceWidget, CMMSUploadPanel, ErrorBoundary } from "../components";
import { theme } from "../styles/theme";
import { ScoresTab } from "./assessment/ScoresTab";
import { BenchmarkTab } from "./assessment/BenchmarkTab";
import { PracticesTab } from "./assessment/PracticesTab";
import { IsoGapsTab } from "./assessment/IsoGapsTab";

const ROLE_OPTIONS = [
  "ALL",
  "TECHNICIAN",
  "SUPERVISOR",
  "MANAGER",
  "PLANNER",
  "RELIABILITY_ENGINEER",
  "OPERATIONS",
];

// Mode tiers are one-way upgrades (free → paid → premium). Existing answers are
// always preserved; upgrading just widens the question set.
const MODE_ORDER = ["quickscan", "standard", "deepdive"] as const;
const MODE_META: Record<string, { label: string; scope: string }> = {
  quickscan: { label: "QuickScan", scope: "15 questions" },
  standard: { label: "Standard", scope: "~75 questions" },
  deepdive: { label: "DeepDive", scope: "150 questions" },
};

export const AssessmentV2Detail: React.FC = () => {
  const { assessmentId } = useParams<{ assessmentId: string }>();
  const navigate = useNavigate();
  const id = Number(assessmentId);

  const {
    currentAssessment,
    questions,
    progress,
    roleCounts,
    loadAssessment,
    loadQuestions,
    loadProgress,
    loadResponses,
    submitResponse,
    upgradeMode,
    calculateScores,
    scoringResult,
    scoringLoading,
    loadFramework,
    domains,
    responseExtras,
  } = useV2Store();

  const [selectedRole, setSelectedRole] = useState("ALL");
  const [activeTab, setActiveTab] = useState<
    "interview" | "scores" | "benchmark" | "practices" | "iso"
  >("interview");
  const [currentDomain, setCurrentDomain] = useState<string | null>(null);
  const [currentSubdomain, setCurrentSubdomain] = useState<string | null>(null);
  const [evidenceFilter, setEvidenceFilter] = useState<"all" | "required" | "not_required">("all");
  const [responses, setResponses] = useState<
    Record<number, { score: number; notes: string }>
  >({});
  const [showRubric, setShowRubric] = useState<number | null>(null);
  // Auto-save status: 'saving' | 'saved' | 'error' per question
  const [saveStatus, setSaveStatus] = useState<
    Record<number, "saving" | "saved" | "error">
  >({});
  const [saveErrors, setSaveErrors] = useState<Record<number, string>>({});
  const [showGuide, setShowGuide] = useState(false);
  const saveTimers = useRef<Record<number, ReturnType<typeof setTimeout>>>({});
  const responsesLoaded = useRef(false);

  useEffect(() => {
    if (isNaN(id)) {
      navigate("/dashboard", { replace: true });
      return;
    }
    responsesLoaded.current = false;
    loadFramework();
    loadAssessment(id);
    loadQuestions(id, selectedRole);
    loadProgress(id);
    // Load existing responses so score buttons show as selected
    loadResponses(id).then((saved) => {
      if (Object.keys(saved).length > 0) {
        // Merge saved responses without overwriting any scores the user
        // may have clicked while this request was in flight
        setResponses((prev) => {
          const merged = { ...saved };
          for (const [qid, val] of Object.entries(prev)) {
            if (val.score) merged[Number(qid)] = val; // user click wins
          }
          return merged;
        });
      }
      responsesLoaded.current = true;
    });
  }, [id]);

  useEffect(() => {
    loadQuestions(id, selectedRole);
  }, [selectedRole]);

  // Auto-save a single response
  const autoSave = useCallback(
    async (questionId: number, score: number, notes: string) => {
      setSaveStatus((prev) => ({ ...prev, [questionId]: "saving" }));
      setSaveErrors((prev) => {
        const next = { ...prev };
        delete next[questionId];
        return next;
      });
      try {
        await submitResponse(id, {
          question_id: questionId,
          response_value: score.toString(),
          numeric_score: score,
          respondent_role: selectedRole === "ALL" ? undefined : selectedRole,
          evidence_notes: notes || undefined,
        });
        setSaveStatus((prev) => ({ ...prev, [questionId]: "saved" }));
        setTimeout(() => {
          setSaveStatus((prev) => {
            const next = { ...prev };
            if (next[questionId] === "saved") delete next[questionId];
            return next;
          });
        }, 2000);
      } catch (err: any) {
        const detail =
          err?.response?.data?.detail ||
          err?.response?.statusText ||
          err?.message ||
          "Unknown error";
        const msg = typeof detail === "string" ? detail : JSON.stringify(detail);
        setSaveStatus((prev) => ({ ...prev, [questionId]: "error" }));
        setSaveErrors((prev) => ({ ...prev, [questionId]: msg }));
        // eslint-disable-next-line no-console
        console.error(`autoSave q=${questionId} failed:`, err);
      }
    },
    [id, selectedRole, submitResponse]
  );

  // Group questions by domain > subdomain
  const questionTree = useMemo(() => {
    const tree: Record<string, Record<string, QuestionV2[]>> = {};
    questions.forEach((q) => {
      const domCode =
        q.domain_code ||
        q.domain ||
        (q.subdomain_code ? q.subdomain_code.split(".")[0] : "Unknown");
      const sdCode = q.subdomain_code || "Unknown";
      if (!tree[domCode]) tree[domCode] = {};
      if (!tree[domCode][sdCode]) tree[domCode][sdCode] = [];
      tree[domCode][sdCode].push(q);
    });
    return tree;
  }, [questions]);

  // Set default domain on first load
  useEffect(() => {
    const domainCodes = Object.keys(questionTree);
    if (domainCodes.length > 0 && !currentDomain) {
      setCurrentDomain(domainCodes[0]);
      const subs = Object.keys(questionTree[domainCodes[0]] || {});
      if (subs.length > 0) setCurrentSubdomain(subs[0]);
    }
  }, [questionTree]);

  const handleScoreSelect = (questionId: number, score: number) => {
    const notes = responses[questionId]?.notes || "";
    setResponses((prev) => ({
      ...prev,
      [questionId]: { ...prev[questionId], score, notes },
    }));
    // Auto-save immediately on score select
    autoSave(questionId, score, notes);
  };

  // Debounced auto-save for notes (fires 800ms after user stops typing)
  const handleNotesChange = (questionId: number, notes: string) => {
    setResponses((prev) => ({
      ...prev,
      [questionId]: {
        ...prev[questionId],
        notes,
        score: prev[questionId]?.score || 0,
      },
    }));
    // Clear existing timer for this question
    if (saveTimers.current[questionId])
      clearTimeout(saveTimers.current[questionId]);
    const score = responses[questionId]?.score;
    if (score) {
      saveTimers.current[questionId] = setTimeout(() => {
        autoSave(questionId, score, notes);
      }, 800);
    }
  };

  const handleCalculateScores = async () => {
    await calculateScores(id);
    setActiveTab("scores");
  };

  const [modeChanging, setModeChanging] = useState(false);
  const handleChangeMode = async (newMode: string) => {
    const cur = MODE_META[currentAssessment?.assessment_mode || ""]?.label || "current";
    const next = MODE_META[newMode]?.label || newMode;
    if (
      !window.confirm(
        `Upgrade this assessment from ${cur} to ${next}?\n\n` +
          `Your existing answers are preserved — upgrading only adds more questions ` +
          `(${MODE_META[newMode]?.scope}).`
      )
    )
      return;
    setModeChanging(true);
    try {
      await upgradeMode(id, newMode);
      // Refresh in place so the wider question set appears without leaving the page.
      await Promise.all([loadQuestions(id, selectedRole), loadProgress(id)]);
    } finally {
      setModeChanging(false);
    }
  };

  const currentQuestionsAll =
    currentDomain && currentSubdomain
      ? questionTree[currentDomain]?.[currentSubdomain] || []
      : [];
  const currentQuestions = currentQuestionsAll.filter((q) => {
    if (evidenceFilter === "required") return q.evidence_required === true;
    if (evidenceFilter === "not_required") return q.evidence_required === false;
    return true;
  });

  // Per-subdomain answered counts (any saved response with a numeric score counts)
  const subdomainAnswered = useMemo(() => {
    const counts: Record<string, number> = {};
    Object.values(questionTree).forEach((subs) => {
      Object.entries(subs).forEach(([sdCode, qs]) => {
        counts[sdCode] = qs.reduce(
          (n, q) => n + ((responses[q.id]?.score ?? 0) > 0 ? 1 : 0),
          0
        );
      });
    });
    return counts;
  }, [questionTree, responses]);

  const domainName = (code: string) =>
    domains.find((d) => d.code === code)?.name || code;
  const subdomainName = (code: string) => {
    for (const d of domains) {
      const sd = d.subdomains.find((s) => s.code === code);
      if (sd) return sd.name;
    }
    return code;
  };

  if (!currentAssessment) {
    return (
      <div
        style={{
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          height: "80vh",
        }}
      >
        <div className="spinner" />
      </div>
    );
  }

  return (
    <div className="page">
      {/* Assessment Header */}
      <div style={{ marginBottom: 24 }}>
        <button
          onClick={() => navigate("/dashboard")}
          style={{
            background: "none",
            border: "none",
            color: "var(--accent)",
            cursor: "pointer",
            fontSize: "0.8125rem",
            fontWeight: 500,
            padding: 0,
            marginBottom: 14,
            fontFamily: "inherit",
            display: "inline-flex",
            alignItems: "center",
            gap: 6,
          }}
        >
          ← Back to Assessments
        </button>

        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "flex-start",
            flexWrap: "wrap",
            gap: 16,
          }}
        >
          <div>
            <div className="pg-crumb" style={{ marginBottom: 6 }}>
              <span>Assessments</span>
              <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="9 18 15 12 9 6" /></svg>
              <span className="crumb-cur">{currentAssessment.site_name}</span>
            </div>
            <h1 className="pg-title" style={{ fontSize: 36, margin: "0 0 8px" }}>
              <em>{currentAssessment.organization_name.split(" ")[0]}</em>
              {currentAssessment.organization_name.includes(" ") &&
                " " + currentAssessment.organization_name.split(" ").slice(1).join(" ")}
            </h1>
            <div className="pg-sub">
              <span>{currentAssessment.site_name}</span>
              <span className="dot" />
              <span className="mono" style={{ textTransform: "uppercase" }}>
                {MODE_META[currentAssessment.assessment_mode]?.label ||
                  currentAssessment.assessment_mode}
              </span>
              {(() => {
                const curIdx = MODE_ORDER.indexOf(
                  currentAssessment.assessment_mode as (typeof MODE_ORDER)[number]
                );
                const upgrades = MODE_ORDER.slice(curIdx + 1);
                if (currentAssessment.finalized_at || upgrades.length === 0) return null;
                return (
                  <>
                    <span className="dot" />
                    <select
                      aria-label="Change assessment mode"
                      className="field-input"
                      value=""
                      disabled={modeChanging}
                      onChange={(e) => {
                        if (e.target.value) handleChangeMode(e.target.value);
                      }}
                      style={{
                        width: "auto",
                        padding: "3px 8px",
                        fontSize: 11.5,
                        height: "auto",
                        cursor: "pointer",
                      }}
                    >
                      <option value="">
                        {modeChanging ? "Upgrading…" : "Upgrade mode…"}
                      </option>
                      {upgrades.map((m) => (
                        <option key={m} value={m}>
                          {MODE_META[m].label} ({MODE_META[m].scope})
                        </option>
                      ))}
                    </select>
                  </>
                );
              })()}
              {currentAssessment.industry_module && (
                <>
                  <span className="dot" />
                  <span>{currentAssessment.industry_module}</span>
                </>
              )}
            </div>
          </div>
          {currentAssessment.overall_rmi != null && (
            <div className="card" style={{ padding: "14px 20px", textAlign: "right", minWidth: 160 }}>
              <div className="label" style={{ marginBottom: 6 }}>Overall RMI</div>
              <div className="num" style={{ fontSize: 36, color: "var(--accent)" }}>
                {Number(currentAssessment.overall_rmi).toFixed(2)}
                <span className="unit" style={{ fontSize: 14, color: "var(--muted)" }}> / 5.0</span>
              </div>
              <div style={{ fontSize: 11.5, color: "var(--muted)", marginTop: 4 }}>
                {currentAssessment.maturity_level}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Tab Nav */}
      <div
        style={{
          display: "flex",
          gap: 4,
          borderBottom: "1px solid var(--line)",
          marginBottom: 24,
        }}
      >
        {([
          ["interview",  "Interview"],
          ["scores",     "Scores"],
          ["benchmark",  "Benchmark"],
          ["practices",  "Practices"],
          ["iso",        "ISO 55001"],
        ] as const).map(
          ([tab, label]) => (
            <button
              key={tab}
              onClick={() => {
                setActiveTab(tab);
                if (tab === "scores" && !scoringResult) calculateScores(id);
              }}
              style={{
                padding: "10px 16px",
                background: "none",
                border: "none",
                cursor: "pointer",
                fontSize: 13.5,
                fontWeight: 600,
                color: activeTab === tab ? "var(--accent)" : "var(--ink-2)",
                borderBottom:
                  activeTab === tab
                    ? "2px solid var(--accent)"
                    : "2px solid transparent",
                marginBottom: -1,
                fontFamily: "inherit",
                transition: "all 0.15s ease",
              }}
            >
              {label}
            </button>
          )
        )}
      </div>

      {/* Tab Content */}
      {activeTab === "interview" && (
        <div>
          {/* CMMS data snapshot */}
          <ErrorBoundary fallbackLabel="CMMS upload panel failed to render.">
            <CMMSUploadPanel assessmentId={id} disabled={!!currentAssessment.finalized_at} />
          </ErrorBoundary>

          {/* Assessor Guide Banner */}
          <Card style={{ marginBottom: 20 }}>
            <div
              style={{
                padding: "16px 20px",
                background: "var(--accent-soft)",
                borderRadius: 10,
                borderLeft: "3px solid var(--accent)",
              }}
            >
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                }}
              >
                <div
                  style={{ display: "flex", alignItems: "center", gap: 12 }}
                >
                  <div
                    className="brand-mark"
                    style={{ width: 28, height: 28, fontSize: 10 }}
                  >
                    NB
                  </div>
                  <div>
                    <strong style={{ fontSize: 13.5, color: "var(--accent)" }}>
                      NextBelt Assessment Guide
                    </strong>
                    <div
                      style={{
                        fontSize: 11.5,
                        color: "var(--ink-2)",
                        marginTop: 3,
                      }}
                    >
                      Score each question 1-5 using the rubric. Select the
                      respondent role. Responses auto-save.
                    </div>
                  </div>
                </div>
                <button
                  className="btn sm"
                  onClick={() => setShowGuide(!showGuide)}
                >
                  {showGuide ? "Hide Guide" : "Show Full Guide"}
                </button>
              </div>
              {showGuide && (
                <div
                  style={{
                    marginTop: 14,
                    paddingTop: 14,
                    borderTop: "1px solid rgba(14, 110, 98, 0.20)",
                  }}
                >
                  <div
                    style={{
                      display: "grid",
                      gridTemplateColumns: "1fr 1fr",
                      gap: 20,
                      fontSize: 12.5,
                      color: "var(--ink-2)",
                      lineHeight: 1.65,
                    }}
                  >
                    <div>
                      <h4
                        style={{
                          margin: "0 0 8px 0",
                          color: "var(--accent)",
                          fontSize: 12.5,
                        }}
                      >
                        Scoring Scale (1-5)
                      </h4>
                      <table
                        style={{
                          width: "100%",
                          borderCollapse: "collapse",
                          fontSize: "0.75rem",
                        }}
                      >
                        <tbody>
                          <tr style={{ borderBottom: "1px solid var(--line-2)" }}>
                            <td
                              style={{
                                padding: "4px 8px",
                                fontWeight: 700,
                                color: "#C53030",
                              }}
                            >
                              1
                            </td>
                            <td style={{ padding: "4px 8px" }}>
                              <strong>Reactive</strong> — No formal process,
                              ad-hoc only
                            </td>
                          </tr>
                          <tr style={{ borderBottom: "1px solid var(--line-2)" }}>
                            <td
                              style={{
                                padding: "4px 8px",
                                fontWeight: 700,
                                color: "#C0603F",
                              }}
                            >
                              2
                            </td>
                            <td style={{ padding: "4px 8px" }}>
                              <strong>Emerging</strong> — Some processes exist
                              but inconsistent
                            </td>
                          </tr>
                          <tr style={{ borderBottom: "1px solid var(--line-2)" }}>
                            <td
                              style={{
                                padding: "4px 8px",
                                fontWeight: 700,
                                color: "#B8860B",
                              }}
                            >
                              3
                            </td>
                            <td style={{ padding: "4px 8px" }}>
                              <strong>Systematic</strong> — Documented,
                              followed, measured
                            </td>
                          </tr>
                          <tr style={{ borderBottom: "1px solid var(--line-2)" }}>
                            <td
                              style={{
                                padding: "4px 8px",
                                fontWeight: 700,
                                color: theme.colors.primary,
                              }}
                            >
                              4
                            </td>
                            <td style={{ padding: "4px 8px" }}>
                              <strong>Proactive</strong> — Optimized,
                              data-driven decisions
                            </td>
                          </tr>
                          <tr>
                            <td
                              style={{
                                padding: "4px 8px",
                                fontWeight: 700,
                                color: "#0D8A5E",
                              }}
                            >
                              5
                            </td>
                            <td style={{ padding: "4px 8px" }}>
                              <strong>World-Class</strong> — Industry-leading,
                              continuous improvement
                            </td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                    <div>
                      <h4
                        style={{
                          margin: "0 0 8px 0",
                          color: "var(--accent)",
                          fontSize: 12.5,
                        }}
                      >
                        Assessment Best Practices
                      </h4>
                      <ul
                        style={{
                          margin: 0,
                          paddingLeft: "16px",
                          lineHeight: 1.9,
                        }}
                      >
                        <li>
                          <strong>Use the rubric</strong> — click "Show scoring
                          rubric" for each question for specific level
                          descriptions.
                        </li>
                        <li>
                          <strong>Interview multiple roles</strong> — select the
                          appropriate respondent role; different roles see
                          different questions.
                        </li>
                        <li>
                          <strong>Gather evidence</strong> — add notes with
                          specific examples, document references, or
                          screenshots.
                        </li>
                        <li>
                          <strong>Be objective</strong> — score based on
                          observed practices, not aspirations or plans.
                        </li>
                        <li>
                          <strong>Calibrate</strong> — look for 💡 calibration
                          anchors that provide industry-standard reference
                          points.
                        </li>
                      </ul>
                    </div>
                  </div>
                  <div
                    style={{
                      marginTop: 14,
                      padding: 12,
                      background: "var(--surface-2)",
                      border: "1px solid var(--line-2)",
                      borderRadius: 10,
                    }}
                  >
                    <h4
                      style={{
                        margin: "0 0 8px 0",
                        color: "var(--ink)",
                        fontSize: 12,
                        letterSpacing: "0.08em",
                        textTransform: "uppercase",
                      }}
                    >
                      Assessment Workflow
                    </h4>
                    <div
                      style={{
                        display: "flex",
                        gap: 6,
                        alignItems: "center",
                        fontSize: 11.5,
                        color: "var(--ink-2)",
                        flexWrap: "wrap",
                      }}
                    >
                      {["Interview", "Calculate Scores", "Review Benchmark", "Practices & Roadmap"].map((step, i, arr) => (
                        <React.Fragment key={step}>
                          <span className={`chip ${i === 0 ? "accent" : "muted"}`}>
                            {i + 1}. {step}
                          </span>
                          {i < arr.length - 1 && <span style={{ color: "var(--muted-2)" }}>→</span>}
                        </React.Fragment>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>
          </Card>

          <div
            style={{
              display: "grid",
              gridTemplateColumns: "260px 1fr",
              gap: 24,
            }}
          >
            {/* Domain/Subdomain Sidebar */}
            <div className="card" style={{ padding: 16, alignSelf: "start", position: "sticky", top: 80 }}>
              <div className="field" style={{ marginBottom: 16 }}>
                <label className="field-label">Respondent Role</label>
                <select
                  className="field-input"
                  value={selectedRole}
                  onChange={(e) => setSelectedRole(e.target.value)}
                  style={{ fontSize: 12.5 }}
                >
                  {ROLE_OPTIONS.map((r) => {
                    const totalAll = Object.values(roleCounts).reduce(
                      (s, n) => s + n,
                      0
                    );
                    const count = r === "ALL" ? totalAll : roleCounts[r] || 0;
                    const label =
                      r === "ALL" ? "All Roles" : r.replace(/_/g, " ");
                    return (
                      <option key={r} value={r}>
                        {label} ({count})
                      </option>
                    );
                  })}
                </select>
              </div>

              {/* Progress Bar */}
              {progress && (
                <div style={{ marginBottom: 20 }}>
                  <div
                    style={{
                      fontSize: 11,
                      color: "var(--muted)",
                      marginBottom: 6,
                      fontFamily: "'JetBrains Mono', monospace",
                      display: "flex",
                      justifyContent: "space-between",
                    }}
                  >
                    <span>{progress.answered}/{progress.total_questions}</span>
                    <span>{progress.completion_pct}%</span>
                  </div>
                  <div
                    style={{
                      height: 4,
                      background: "var(--line-2)",
                      borderRadius: 999,
                      overflow: "hidden",
                    }}
                  >
                    <div
                      style={{
                        height: "100%",
                        width: `${progress.completion_pct}%`,
                        background: "var(--accent)",
                        borderRadius: 999,
                        transition: "width 0.3s ease",
                      }}
                    />
                  </div>
                </div>
              )}

              {/* Domain Tree */}
              <div
                style={{ display: "flex", flexDirection: "column", gap: 2 }}
              >
                <div className="label" style={{ marginBottom: 6 }}>Domains</div>
                {Object.keys(questionTree).map((domCode) => (
                  <div key={domCode}>
                    <button
                      onClick={() => {
                        setCurrentDomain(domCode);
                        const subs = Object.keys(questionTree[domCode]);
                        if (subs.length > 0) setCurrentSubdomain(subs[0]);
                      }}
                      style={{
                        width: "100%",
                        textAlign: "left",
                        padding: "8px 10px",
                        border: "none",
                        background:
                          currentDomain === domCode
                            ? "var(--accent-soft)"
                            : "transparent",
                        borderRadius: 8,
                        cursor: "pointer",
                        fontSize: 12.5,
                        fontWeight: 600,
                        color:
                          currentDomain === domCode
                            ? "var(--accent)"
                            : "var(--ink)",
                        fontFamily: "inherit",
                      }}
                    >
                      <span className="mono" style={{ fontSize: 10.5, color: "var(--muted)", marginRight: 6 }}>{domCode}</span>
                      {domainName(domCode)}
                      {(() => {
                        const subs = questionTree[domCode] || {};
                        const total = Object.values(subs).reduce((n, qs) => n + qs.length, 0);
                        const answered = Object.keys(subs).reduce(
                          (n, sd) => n + (subdomainAnswered[sd] ?? 0),
                          0
                        );
                        return (
                          <span style={{ float: "right", fontSize: 11, color: "var(--muted)", fontWeight: 500 }}>
                            {answered}/{total}
                          </span>
                        );
                      })()}
                    </button>
                    {Object.keys(questionTree[domCode]).map((sdCode) => (
                        <button
                          key={sdCode}
                          onClick={() => { setCurrentDomain(domCode); setCurrentSubdomain(sdCode); }}
                          style={{
                            width: "100%",
                            textAlign: "left",
                            padding: "6px 10px 6px 24px",
                            border: "none",
                            background:
                              currentSubdomain === sdCode
                                ? "var(--accent-soft)"
                                : "transparent",
                            borderRadius: 6,
                            cursor: "pointer",
                            fontSize: 11.5,
                            color:
                              currentSubdomain === sdCode
                                ? "var(--accent)"
                                : "var(--muted)",
                            fontFamily: "'JetBrains Mono', monospace",
                          }}
                        >
                          {sdCode} ({subdomainAnswered[sdCode] ?? 0}/{questionTree[domCode][sdCode].length})
                        </button>
                      ))}
                  </div>
                ))}
              </div>

              {/* Actions */}
              <div
                style={{
                  marginTop: 20,
                  paddingTop: 16,
                  borderTop: "1px solid var(--line-2)",
                  display: "flex",
                  flexDirection: "column",
                  gap: 8,
                }}
              >
                <div
                  style={{
                    fontSize: 11,
                    color: "var(--ok)",
                    textAlign: "center",
                    padding: 4,
                  }}
                >
                  ✓ Responses auto-save
                </div>
                <button
                  className="btn primary block"
                  onClick={handleCalculateScores}
                  disabled={scoringLoading}
                >
                  {scoringLoading ? "Calculating..." : "Calculate Scores"}
                </button>
              </div>
            </div>

            {/* Questions Panel */}
            <div>
              {currentSubdomain && (
                <div style={{ marginBottom: "16px", display: "flex", alignItems: "flex-end", justifyContent: "space-between", gap: 16, flexWrap: "wrap" }}>
                  <div>
                    <h2
                      style={{
                        fontSize: "1.125rem",
                        margin: "0 0 4px 0",
                        color: "#1A1A1A",
                      }}
                    >
                      {subdomainName(currentSubdomain)}
                    </h2>
                    <p
                      style={{ color: "#666666", fontSize: "0.8rem", margin: 0 }}
                    >
                      {currentSubdomain} · {subdomainAnswered[currentSubdomain] ?? 0}/{currentQuestionsAll.length} answered
                      {evidenceFilter !== "all" && (
                        <> · showing {currentQuestions.length} of {currentQuestionsAll.length}</>
                      )}
                    </p>
                  </div>
                  <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                    <label style={{ fontSize: 11, color: "var(--muted)", textTransform: "uppercase", letterSpacing: "0.06em" }}>
                      Evidence
                    </label>
                    <select
                      className="field-input"
                      value={evidenceFilter}
                      onChange={(e) => setEvidenceFilter(e.target.value as "all" | "required" | "not_required")}
                      style={{ fontSize: 12, padding: "6px 8px", width: "auto" }}
                    >
                      <option value="all">All questions</option>
                      <option value="required">Evidence required</option>
                      <option value="not_required">No evidence</option>
                    </select>
                  </div>
                </div>
              )}

              <div
                style={{
                  display: "flex",
                  flexDirection: "column",
                  gap: "16px",
                }}
              >
                {currentQuestions.map((q) => (
                  <Card key={q.id}>
                    <div style={{ padding: "20px" }}>
                      {/* Question Header */}
                      <div
                        style={{
                          display: "flex",
                          justifyContent: "space-between",
                          alignItems: "flex-start",
                          gap: "12px",
                          marginBottom: "12px",
                        }}
                      >
                        <div style={{ flex: 1 }}>
                          <div
                            style={{
                              display: "flex",
                              alignItems: "center",
                              gap: "8px",
                              marginBottom: "6px",
                            }}
                          >
                            <span
                              style={{
                                fontSize: "0.7rem",
                                fontFamily: theme.typography.fontFamily.mono,
                                color: "#666666",
                              }}
                            >
                              {q.question_code}
                            </span>
                            {q.is_critical && (
                              <span
                                style={{
                                  fontSize: "0.65rem",
                                  padding: "1px 6px",
                                  borderRadius: "4px",
                                  fontWeight: 700,
                                  background: "rgba(248,113,113,0.12)",
                                  color: "#F87171",
                                }}
                              >
                                CRITICAL
                              </span>
                            )}
                            {q.evidence_required && (
                              <span
                                style={{
                                  fontSize: "0.65rem",
                                  padding: "1px 6px",
                                  borderRadius: "4px",
                                  fontWeight: 600,
                                  background: "rgba(245,158,11,0.12)",
                                  color: "#F59E0B",
                                }}
                              >
                                EVIDENCE REQ
                              </span>
                            )}
                            <span
                              style={{ fontSize: "0.65rem", color: "#666666" }}
                            >
                              wt: {q.weight}
                            </span>
                          </div>
                          <p
                            style={{
                              margin: 0,
                              fontSize: "0.925rem",
                              lineHeight: 1.5,
                              color: "#333333",
                            }}
                          >
                            {q.question_text}
                          </p>
                        </div>
                      </div>

                      {/* Scoring Rubric Toggle */}
                      <button
                        onClick={() =>
                          setShowRubric(showRubric === q.id ? null : q.id)
                        }
                        style={{
                          background: "none",
                          border: "none",
                          cursor: "pointer",
                          fontSize: "0.75rem",
                          color: theme.colors.primary,
                          fontWeight: 500,
                          padding: 0,
                          marginBottom: "12px",
                          fontFamily: theme.typography.fontFamily.primary,
                        }}
                      >
                        {showRubric === q.id
                          ? "▾ Hide rubric"
                          : "▸ Show scoring rubric"}
                      </button>

                      {showRubric === q.id && (
                        <div
                          style={{
                            background: "rgba(0,0,0,0.02)",
                            borderRadius: "6px",
                            padding: "12px",
                            marginBottom: "12px",
                            fontSize: "0.8rem",
                            lineHeight: 1.6,
                            border: "1px solid rgba(0,0,0,0.06)",
                            color: "#666666",
                          }}
                        >
                          {(() => {
                            try {
                              const rubric =
                                typeof q.scoring_rubric === "string"
                                  ? JSON.parse(q.scoring_rubric)
                                  : q.scoring_rubric;
                              return Object.entries(rubric).map(
                                ([level, desc]) => (
                                  <div
                                    key={level}
                                    style={{ marginBottom: "4px" }}
                                  >
                                    <strong
                                      style={{ color: theme.colors.primary }}
                                    >
                                      {level}:
                                    </strong>{" "}
                                    {desc as string}
                                  </div>
                                )
                              );
                            } catch {
                              return <div>No rubric available</div>;
                            }
                          })()}
                        </div>
                      )}

                      {/* Score Selector — auto-saves on click */}
                      <div
                        style={{
                          display: "flex",
                          gap: "6px",
                          alignItems: "center",
                        }}
                      >
                        <span
                          style={{
                            fontSize: "0.75rem",
                            color: "#666666",
                            marginRight: "8px",
                          }}
                        >
                          Score:
                        </span>
                        {[1, 2, 3, 4, 5].map((s) => {
                          const isSelected = responses[q.id]?.score === s;
                          return (
                            <button
                              key={s}
                              onClick={() => handleScoreSelect(q.id, s)}
                              disabled={saveStatus[q.id] === "saving"}
                              style={{
                                width: "40px",
                                height: "40px",
                                borderRadius: "8px",
                                border: "2px solid",
                                borderColor: isSelected
                                  ? theme.colors.primary
                                  : "rgba(0,0,0,0.12)",
                                background: isSelected
                                  ? theme.colors.primary
                                  : "#FFFFFF",
                                color: isSelected ? "#fff" : "#333333",
                                fontWeight: 700,
                                fontSize: "1rem",
                                cursor: "pointer",
                                transition: "all 0.15s ease",
                                fontFamily: theme.typography.fontFamily.primary,
                                opacity:
                                  saveStatus[q.id] === "saving" ? 0.6 : 1,
                              }}
                            >
                              {s}
                            </button>
                          );
                        })}
                        {/* Auto-save status indicator */}
                        <span
                          style={{
                            marginLeft: "12px",
                            fontSize: "0.75rem",
                            fontWeight: 500,
                            transition: "opacity 0.3s ease",
                          }}
                        >
                          {saveStatus[q.id] === "saving" && (
                            <span style={{ color: "#B8860B" }}>⏳ Saving…</span>
                          )}
                          {saveStatus[q.id] === "saved" && (
                            <span style={{ color: "#0D8A5E" }}>✓ Saved</span>
                          )}
                          {saveStatus[q.id] === "error" && (
                            <span style={{ color: "#C53030" }}>
                              ✗ Save failed — click score to retry
                            </span>
                          )}
                        </span>
                      </div>
                      {saveStatus[q.id] === "error" && saveErrors[q.id] && (
                        <div
                          style={{
                            marginTop: 6,
                            fontSize: "0.72rem",
                            color: "#C53030",
                            background: "rgba(194, 83, 60, 0.08)",
                            border: "1px solid rgba(194, 83, 60, 0.25)",
                            borderRadius: 6,
                            padding: "6px 8px",
                          }}
                        >
                          {saveErrors[q.id]}
                        </div>
                      )}

                      {/* Notes — auto-saves after typing stops */}
                      {responses[q.id]?.score && (
                        <textarea
                          placeholder="Optional notes or evidence…"
                          value={responses[q.id]?.notes || ""}
                          onChange={(e) =>
                            handleNotesChange(q.id, e.target.value)
                          }
                          style={{
                            width: "100%",
                            marginTop: "10px",
                            padding: "8px 10px",
                            borderRadius: "6px",
                            border: "1px solid rgba(0,0,0,0.08)",
                            background: "#FFFFFF",
                            color: "#333333",
                            fontSize: "0.8rem",
                            fontFamily: theme.typography.fontFamily.primary,
                            resize: "vertical",
                            minHeight: "40px",
                            maxHeight: "120px",
                          }}
                        />
                      )}

                      {/* Evidence upload + AI analysis */}
                      <ErrorBoundary fallbackLabel="Evidence widget error.">
                        <EvidenceWidget
                          assessmentId={id}
                          questionId={q.id}
                          evidenceFile={responseExtras[q.id]?.evidence_file ?? null}
                          aiAnalysis={responseExtras[q.id]?.ai_analysis ?? null}
                          onAcceptSuggestedScore={(score) => handleScoreSelect(q.id, score)}
                        />
                      </ErrorBoundary>

                      {/* Calibration Anchor */}
                      {q.calibration_anchor && (
                        <div
                          style={{
                            marginTop: "10px",
                            fontSize: "0.75rem",
                            color: "#8A8A86",
                            fontStyle: "italic",
                          }}
                        >
                          💡 {q.calibration_anchor}
                        </div>
                      )}
                    </div>
                  </Card>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {activeTab === "scores" && (
        <ErrorBoundary fallbackLabel="Could not render Scores.">
          <ScoresTab assessmentId={id} />
        </ErrorBoundary>
      )}

      {activeTab === "benchmark" && (
        <ErrorBoundary fallbackLabel="Could not render Benchmark.">
          <BenchmarkTab assessmentId={id} />
        </ErrorBoundary>
      )}

      {activeTab === "practices" && (
        <ErrorBoundary fallbackLabel="Could not render Practices.">
          <PracticesTab assessmentId={id} />
        </ErrorBoundary>
      )}

      {activeTab === "iso" && (
        <ErrorBoundary fallbackLabel="Could not render ISO 55001 gap report.">
          <IsoGapsTab assessmentId={id} />
        </ErrorBoundary>
      )}
    </div>
  );
};

// ═══════════════════════════════════════════
//  Scores Tab — calibration-style maturity readout
// ═══════════════════════════════════════════
