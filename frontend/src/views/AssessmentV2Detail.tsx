import React, {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { useNavigate, useParams } from "react-router-dom";
import type { QuestionV2, ISOGapReport, ISOClauseResult, ISOSection } from "../api/clientV2";
import { v2API } from "../api/clientV2";
import { useV2Store } from "../api/storeV2";
import { Card, EvidenceWidget, CMMSUploadPanel, ErrorBoundary, DomainRadar } from "../components";
import { theme } from "../styles/theme";

const ROLE_OPTIONS = [
  "ALL",
  "TECHNICIAN",
  "SUPERVISOR",
  "MANAGER",
  "PLANNER",
  "RELIABILITY_ENGINEER",
];

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
                {currentAssessment.assessment_mode}
              </span>
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

const ScoresTab: React.FC<{ assessmentId: number }> = ({ assessmentId }) => {
  const { scoringResult, scoringLoading, calculateScores, domains, progress } =
    useV2Store();
  const [radarView, setRadarView] = useState<RadarView>("domains");

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
const BenchmarkTab: React.FC<{ assessmentId: number }> = ({ assessmentId }) => {
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
      <div style={{ textAlign: "center", padding: "60px", color: "#666666" }}>
        <div style={{ fontSize: "3rem", marginBottom: "16px" }}>📊</div>
        <h3 style={{ color: "#1A1A1A" }}>Score the Assessment First</h3>
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
              background: "#F0F7FF",
              borderRadius: "8px",
              borderLeft: "4px solid #2563EB",
            }}
          >
            <h3
              style={{
                margin: "0 0 8px 0",
                fontSize: "1rem",
                color: "#1E40AF",
              }}
            >
              📊 What is Benchmarking?
            </h3>
            <p
              style={{
                margin: "0 0 12px 0",
                fontSize: "0.875rem",
                color: "#334155",
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
                color: "#475569",
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
                📈 Minimum <strong>{minReq} peers</strong> required for
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
            color: "#666666",
          }}
        >
          <div style={{ fontSize: "2.5rem", marginBottom: "12px" }}>🔍</div>
          <h3 style={{ color: "#1A1A1A", marginBottom: "8px" }}>
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
                    color: "#666666",
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
                    color: "#666666",
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
    if (q === 1) return "#0D8A5E";
    if (q === 2) return theme.colors.primary;
    if (q === 3) return "#B8860B";
    return "#C53030";
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
            background: "#F0F7FF",
            borderRadius: "8px",
            borderLeft: "4px solid #2563EB",
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
                color: "#334155",
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
                color: "#666666",
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
                color: "#666666",
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
                color: "#666666",
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
                color: "#666666",
                textTransform: "uppercase",
                letterSpacing: "0.05em",
                marginBottom: "8px",
              }}
            >
              Peer Group
            </div>
            <div
              style={{ fontSize: "2rem", fontWeight: 700, color: "#333333" }}
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
            style={{ fontSize: "1rem", marginBottom: "12px", color: "#1A1A1A" }}
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
                      color: "#C53030",
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
                      color: "#0D8A5E",
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
                  background: "#FAFAFA",
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
                    background: "#E5E5E5",
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
                color: "#1A1A1A",
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
                            color: "#333333",
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
                            background: "#F0F0F0",
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
                                  ? "#0D8A5E"
                                  : (pct ?? 0) >= 50
                                  ? theme.colors.primary
                                  : (pct ?? 0) >= 25
                                  ? "#B8860B"
                                  : "#C53030",
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
            💡 Assessor Guidance
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
const PracticesTab: React.FC<{ assessmentId: number }> = ({ assessmentId }) => {
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
      <div style={{ textAlign: "center", padding: "60px", color: "#666666" }}>
        <div style={{ fontSize: "3rem", marginBottom: "16px" }}>📚</div>
        <h3 style={{ color: "#1A1A1A" }}>Score the Assessment First</h3>
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
      high: { bg: "rgba(13,138,94,0.1)", text: "#0D8A5E" },
      medium: { bg: "rgba(184,134,11,0.1)", text: "#B8860B" },
      low: { bg: "rgba(102,102,102,0.1)", text: "#666666" },
    };
    const c = colors[impact] || colors.medium;
    return { background: c.bg, color: c.text };
  };

  const getEffortBadge = (effort: string) => {
    const colors: Record<string, { bg: string; text: string }> = {
      low: { bg: "rgba(13,138,94,0.1)", text: "#0D8A5E" },
      medium: { bg: "rgba(184,134,11,0.1)", text: "#B8860B" },
      high: { bg: "rgba(197,48,48,0.1)", text: "#C53030" },
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
              background: "#F0FDF4",
              borderRadius: "8px",
              borderLeft: "4px solid #0D8A5E",
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
                <h3 style={{ margin: 0, fontSize: "1rem", color: "#166534" }}>
                  Maturity Pathway: Level {pathway.from_level} → Level{" "}
                  {pathway.to_level}
                </h3>
                <div
                  style={{
                    fontSize: "0.825rem",
                    color: "#15803D",
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
                    color: "#166534",
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
            background: "#F0F7FF",
            borderRadius: "8px",
            borderLeft: "4px solid #2563EB",
            marginBottom: "24px",
          }}
        >
          <h4
            style={{
              margin: "0 0 8px 0",
              fontSize: "0.875rem",
              color: "#1E40AF",
            }}
          >
            💡 Assessor Guidance — Presenting Recommendations
          </h4>
          <ul
            style={{
              margin: 0,
              paddingLeft: "20px",
              fontSize: "0.8rem",
              color: "#334155",
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
        <h3 style={{ fontSize: "1rem", margin: 0, color: "#1A1A1A" }}>
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
          <h3 style={{ color: "#1A1A1A" }}>No Recommendations Generated</h3>
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
                      background: i < 3 ? theme.colors.primary : "#E5E5E5",
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
                          color: "#1A1A1A",
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
                          background: "#F0F0F0",
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
                          background: "#F5F5F5",
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
                      borderTop: "1px solid #F0F0F0",
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
                                color: "#0D8A5E",
                                textTransform: "uppercase",
                                marginBottom: "6px",
                              }}
                            >
                              ✅ Success Metrics
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

const IsoGapsTab: React.FC<{ assessmentId: number }> = ({ assessmentId }) => {
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
