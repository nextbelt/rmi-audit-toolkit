import React, {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { useNavigate, useParams } from "react-router-dom";
import type { QuestionV2 } from "../api/clientV2";
import { useV2Store } from "../api/storeV2";
import { Button, Card } from "../components";
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
  } = useV2Store();

  const [selectedRole, setSelectedRole] = useState("ALL");
  const [activeTab, setActiveTab] = useState<
    "interview" | "scores" | "benchmark" | "practices"
  >("interview");
  const [currentDomain, setCurrentDomain] = useState<string | null>(null);
  const [currentSubdomain, setCurrentSubdomain] = useState<string | null>(null);
  const [responses, setResponses] = useState<
    Record<number, { score: number; notes: string }>
  >({});
  const [showRubric, setShowRubric] = useState<number | null>(null);
  // Auto-save status: 'saving' | 'saved' | 'error' per question
  const [saveStatus, setSaveStatus] = useState<
    Record<number, "saving" | "saved" | "error">
  >({});
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
      try {
        await submitResponse(id, {
          question_id: questionId,
          response_value: score.toString(),
          numeric_score: score,
          respondent_role: selectedRole === "ALL" ? undefined : selectedRole,
          evidence_notes: notes || undefined,
        });
        setSaveStatus((prev) => ({ ...prev, [questionId]: "saved" }));
        // Note: submitResponse already calls loadProgress internally
        // Clear 'saved' indicator after 2s
        setTimeout(() => {
          setSaveStatus((prev) => {
            const next = { ...prev };
            if (next[questionId] === "saved") delete next[questionId];
            return next;
          });
        }, 2000);
      } catch {
        setSaveStatus((prev) => ({ ...prev, [questionId]: "error" }));
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

  const currentQuestions =
    currentDomain && currentSubdomain
      ? questionTree[currentDomain]?.[currentSubdomain] || []
      : [];

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
    <div style={{ padding: "24px", maxWidth: "1400px", margin: "0 auto" }}>
      {/* Assessment Header */}
      <div style={{ marginBottom: "24px" }}>
        <button
          onClick={() => navigate("/dashboard")}
          style={{
            background: "none",
            border: "none",
            color: theme.colors.primary,
            cursor: "pointer",
            fontSize: "0.875rem",
            fontWeight: 500,
            padding: 0,
            marginBottom: "12px",
            fontFamily: theme.typography.fontFamily.primary,
          }}
        >
          ← Back to Dashboard
        </button>

        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "flex-start",
            flexWrap: "wrap",
            gap: "16px",
          }}
        >
          <div>
            <h1
              style={{
                fontSize: "1.5rem",
                margin: "0 0 4px 0",
                color: "#1A1A1A",
              }}
            >
              {currentAssessment.organization_name}
            </h1>
            <p style={{ color: "#8A8A86", fontSize: "0.875rem", margin: 0 }}>
              {currentAssessment.site_name} ·{" "}
              {currentAssessment.assessment_mode.toUpperCase()} mode
              {currentAssessment.industry_module &&
                ` · ${currentAssessment.industry_module}`}
            </p>
          </div>
          {currentAssessment.overall_rmi != null && (
            <div style={{ textAlign: "right" }}>
              <div
                style={{
                  fontSize: "2rem",
                  fontWeight: 700,
                  color: theme.colors.primary,
                }}
              >
                {Number(currentAssessment.overall_rmi).toFixed(2)}
              </div>
              <div style={{ fontSize: "0.75rem", color: "#666666" }}>
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
          gap: "0",
          borderBottom: "1px solid rgba(0,0,0,0.08)",
          marginBottom: "24px",
        }}
      >
        {(["interview", "scores", "benchmark", "practices"] as const).map(
          (tab) => (
            <button
              key={tab}
              onClick={() => {
                setActiveTab(tab);
                if (tab === "scores" && !scoringResult) calculateScores(id);
              }}
              style={{
                padding: "12px 20px",
                background: "none",
                border: "none",
                cursor: "pointer",
                fontSize: "0.875rem",
                fontWeight: 600,
                textTransform: "capitalize",
                color: activeTab === tab ? theme.colors.primary : "#666666",
                borderBottom:
                  activeTab === tab
                    ? `2px solid ${theme.colors.primary}`
                    : "2px solid transparent",
                marginBottom: "-2px",
                fontFamily: theme.typography.fontFamily.primary,
                transition: "all 0.2s ease",
              }}
            >
              {tab}
            </button>
          )
        )}
      </div>

      {/* Tab Content */}
      {activeTab === "interview" && (
        <div>
          {/* Assessor Guide Banner */}
          <Card>
            <div
              style={{
                padding: "16px 20px",
                background: "#F0F7FF",
                borderRadius: "8px",
                borderLeft: "4px solid #2563EB",
                marginBottom: "20px",
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
                  style={{ display: "flex", alignItems: "center", gap: "10px" }}
                >
                  <span style={{ fontSize: "1.25rem" }}>📋</span>
                  <div>
                    <strong style={{ fontSize: "0.875rem", color: "#1E40AF" }}>
                      NextBelt Assessment Guide
                    </strong>
                    <div
                      style={{
                        fontSize: "0.75rem",
                        color: "#475569",
                        marginTop: "2px",
                      }}
                    >
                      Score each question 1-5 using the rubric. Select the
                      respondent role. Responses auto-save.
                    </div>
                  </div>
                </div>
                <button
                  onClick={() => setShowGuide(!showGuide)}
                  style={{
                    background: "none",
                    border: "1px solid #93C5FD",
                    borderRadius: "6px",
                    cursor: "pointer",
                    padding: "4px 12px",
                    fontSize: "0.75rem",
                    color: "#2563EB",
                    fontWeight: 600,
                    fontFamily: theme.typography.fontFamily.primary,
                  }}
                >
                  {showGuide ? "Hide Guide" : "Show Full Guide"}
                </button>
              </div>
              {showGuide && (
                <div
                  style={{
                    marginTop: "16px",
                    paddingTop: "16px",
                    borderTop: "1px solid #BFDBFE",
                  }}
                >
                  <div
                    style={{
                      display: "grid",
                      gridTemplateColumns: "1fr 1fr",
                      gap: "20px",
                      fontSize: "0.8rem",
                      color: "#334155",
                      lineHeight: 1.7,
                    }}
                  >
                    <div>
                      <h4
                        style={{
                          margin: "0 0 8px 0",
                          color: "#1E40AF",
                          fontSize: "0.85rem",
                        }}
                      >
                        🎯 Scoring Scale (1-5)
                      </h4>
                      <table
                        style={{
                          width: "100%",
                          borderCollapse: "collapse",
                          fontSize: "0.75rem",
                        }}
                      >
                        <tbody>
                          <tr style={{ borderBottom: "1px solid #DBEAFE" }}>
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
                          <tr style={{ borderBottom: "1px solid #DBEAFE" }}>
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
                          <tr style={{ borderBottom: "1px solid #DBEAFE" }}>
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
                          <tr style={{ borderBottom: "1px solid #DBEAFE" }}>
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
                          color: "#1E40AF",
                          fontSize: "0.85rem",
                        }}
                      >
                        📝 Assessment Best Practices
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
                      marginTop: "16px",
                      padding: "12px",
                      background: "#DBEAFE",
                      borderRadius: "6px",
                    }}
                  >
                    <h4
                      style={{
                        margin: "0 0 6px 0",
                        color: "#1E40AF",
                        fontSize: "0.8rem",
                      }}
                    >
                      🏗 Assessment Workflow
                    </h4>
                    <div
                      style={{
                        display: "flex",
                        gap: "4px",
                        alignItems: "center",
                        fontSize: "0.75rem",
                        color: "#1E3A5F",
                        flexWrap: "wrap",
                      }}
                    >
                      <span
                        style={{
                          padding: "4px 10px",
                          background:
                            activeTab === "interview"
                              ? theme.colors.primary
                              : "#93C5FD",
                          color: "#fff",
                          borderRadius: "12px",
                          fontWeight: 600,
                        }}
                      >
                        1. Interview
                      </span>
                      <span>→</span>
                      <span
                        style={{
                          padding: "4px 10px",
                          background: "#93C5FD",
                          borderRadius: "12px",
                          fontWeight: 600,
                        }}
                      >
                        2. Calculate Scores
                      </span>
                      <span>→</span>
                      <span
                        style={{
                          padding: "4px 10px",
                          background: "#93C5FD",
                          borderRadius: "12px",
                          fontWeight: 600,
                        }}
                      >
                        3. Review Benchmark
                      </span>
                      <span>→</span>
                      <span
                        style={{
                          padding: "4px 10px",
                          background: "#93C5FD",
                          borderRadius: "12px",
                          fontWeight: 600,
                        }}
                      >
                        4. Practices & Roadmap
                      </span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </Card>

          <div
            style={{
              display: "grid",
              gridTemplateColumns: "240px 1fr",
              gap: "24px",
            }}
          >
            {/* Domain/Subdomain Sidebar */}
            <div>
              <div style={{ marginBottom: "16px" }}>
                <label
                  style={{
                    fontSize: "0.75rem",
                    fontWeight: 600,
                    color: "#666666",
                    textTransform: "uppercase",
                    letterSpacing: "0.05em",
                  }}
                >
                  Respondent Role
                </label>
                <select
                  value={selectedRole}
                  onChange={(e) => setSelectedRole(e.target.value)}
                  style={{
                    width: "100%",
                    padding: "8px",
                    borderRadius: "6px",
                    border: "1px solid rgba(0,0,0,0.12)",
                    fontSize: "0.8rem",
                    marginTop: "4px",
                    fontFamily: theme.typography.fontFamily.primary,
                    background: "#FFFFFF",
                    color: "#333333",
                  }}
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
                <div style={{ marginBottom: "20px" }}>
                  <div
                    style={{
                      fontSize: "0.75rem",
                      color: "#666666",
                      marginBottom: "6px",
                    }}
                  >
                    {progress.answered}/{progress.total_questions} answered (
                    {progress.completion_pct}%)
                  </div>
                  <div
                    style={{
                      height: "4px",
                      background: "rgba(0,0,0,0.06)",
                      borderRadius: "2px",
                      overflow: "hidden",
                    }}
                  >
                    <div
                      style={{
                        height: "100%",
                        width: `${progress.completion_pct}%`,
                        background: theme.colors.primary,
                        borderRadius: "2px",
                        transition: "width 0.3s ease",
                      }}
                    />
                  </div>
                </div>
              )}

              {/* Domain Tree */}
              <div
                style={{ display: "flex", flexDirection: "column", gap: "2px" }}
              >
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
                            ? `${theme.colors.primary}10`
                            : "transparent",
                        borderRadius: "6px",
                        cursor: "pointer",
                        fontSize: "0.825rem",
                        fontWeight: 600,
                        color:
                          currentDomain === domCode
                            ? theme.colors.primary
                            : "#333333",
                        fontFamily: theme.typography.fontFamily.primary,
                      }}
                    >
                      {domCode} · {domainName(domCode)}
                    </button>
                    {currentDomain === domCode &&
                      Object.keys(questionTree[domCode]).map((sdCode) => (
                        <button
                          key={sdCode}
                          onClick={() => setCurrentSubdomain(sdCode)}
                          style={{
                            width: "100%",
                            textAlign: "left",
                            padding: "6px 10px 6px 24px",
                            border: "none",
                            background:
                              currentSubdomain === sdCode
                                ? `${theme.colors.primary}18`
                                : "transparent",
                            borderRadius: "4px",
                            cursor: "pointer",
                            fontSize: "0.775rem",
                            color:
                              currentSubdomain === sdCode
                                ? theme.colors.primary
                                : "#8A8A86",
                            fontFamily: theme.typography.fontFamily.primary,
                          }}
                        >
                          {sdCode} ({questionTree[domCode][sdCode].length})
                        </button>
                      ))}
                  </div>
                ))}
              </div>

              {/* Actions */}
              <div
                style={{
                  marginTop: "24px",
                  display: "flex",
                  flexDirection: "column",
                  gap: "8px",
                }}
              >
                <div
                  style={{
                    fontSize: "0.7rem",
                    color: "#666666",
                    textAlign: "center",
                    padding: "6px 0",
                  }}
                >
                  ✓ Responses auto-save on selection
                </div>
                <Button
                  onClick={handleCalculateScores}
                  style={{ width: "100%", fontSize: "0.8rem" }}
                >
                  {scoringLoading ? "Calculating..." : "Calculate Scores"}
                </Button>
              </div>
            </div>

            {/* Questions Panel */}
            <div>
              {currentSubdomain && (
                <div style={{ marginBottom: "16px" }}>
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
                    {currentSubdomain} · {currentQuestions.length} questions
                  </p>
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
                              ✗ Error — click score to retry
                            </span>
                          )}
                        </span>
                      </div>

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

      {activeTab === "scores" && <ScoresTab assessmentId={id} />}

      {activeTab === "benchmark" && <BenchmarkTab assessmentId={id} />}

      {activeTab === "practices" && <PracticesTab assessmentId={id} />}
    </div>
  );
};

// ═══════════════════════════════════════════
//  Scores Tab
// ═══════════════════════════════════════════
const ScoresTab: React.FC<{ assessmentId: number }> = ({ assessmentId }) => {
  const { scoringResult, scoringLoading, calculateScores, domains } =
    useV2Store();

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
      <div style={{ textAlign: "center", padding: "40px", color: "#666666" }}>
        No scores available. Complete some questions first.
      </div>
    );

  const {
    overall_rmi,
    maturity_level,
    confidence,
    confidence_score,
    blind_spots,
    iso_55001_readiness,
  } = scoringResult;
  const confidenceVal = confidence_score ?? confidence ?? 0;

  // Backend returns domains as a dict { "AM": { score, subdomains: { "AM.1": {...} } } }
  // Convert to array for rendering
  const domainScores = Object.entries(scoringResult.domains || {}).map(
    ([code, data]: [string, any]) => ({
      domain_code: code,
      domain_name: domainName(code),
      score: data.score,
      subdomains: Object.entries(data.subdomains || {}).map(
        ([sdCode, sdData]: [string, any]) => ({
          subdomain_code: sdCode,
          subdomain_name: subdomainName(sdCode),
          final_score: sdData.final_score,
          cap_applied: sdData.cap_applied,
        })
      ),
    })
  );

  const getScoreColor = (score: number) => {
    if (score >= 4.3) return "#0D8A5E";
    if (score >= 3.6) return theme.colors.primary;
    if (score >= 3.0) return "#B8860B";
    if (score >= 2.0) return "#C0603F";
    return "#C53030";
  };

  return (
    <div>
      {/* Overall Score */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr 1fr 1fr",
          gap: "24px",
          marginBottom: "32px",
        }}
      >
        <Card>
          <div style={{ padding: "24px", textAlign: "center" }}>
            <div
              style={{
                fontSize: "0.75rem",
                color: "#666666",
                textTransform: "uppercase",
                letterSpacing: "0.05em",
                marginBottom: "8px",
              }}
            >
              Overall RMI
            </div>
            <div
              style={{
                fontSize: "2.5rem",
                fontWeight: 700,
                color: getScoreColor(overall_rmi ?? 0),
              }}
            >
              {(overall_rmi ?? 0).toFixed(2)}
            </div>
            <div
              style={{
                fontSize: "0.825rem",
                color: "#8A8A86",
                marginTop: "4px",
              }}
            >
              {maturity_level}
            </div>
          </div>
        </Card>
        <Card>
          <div style={{ padding: "24px", textAlign: "center" }}>
            <div
              style={{
                fontSize: "0.75rem",
                color: "#666666",
                textTransform: "uppercase",
                letterSpacing: "0.05em",
                marginBottom: "8px",
              }}
            >
              Confidence
            </div>
            <div
              style={{
                fontSize: "2.5rem",
                fontWeight: 700,
                color: theme.colors.primary,
              }}
            >
              {(confidenceVal * 100).toFixed(0)}%
            </div>
          </div>
        </Card>
        <Card>
          <div style={{ padding: "24px", textAlign: "center" }}>
            <div
              style={{
                fontSize: "0.75rem",
                color: "#666666",
                textTransform: "uppercase",
                letterSpacing: "0.05em",
                marginBottom: "8px",
              }}
            >
              ISO 55001 Ready
            </div>
            <div
              style={{
                fontSize: "2.5rem",
                fontWeight: 700,
                color: (iso_55001_readiness ?? 0) >= 70 ? "#0D8A5E" : "#C0603F",
              }}
            >
              {(iso_55001_readiness ?? 0).toFixed(0)}%
            </div>
          </div>
        </Card>
        <Card>
          <div style={{ padding: "24px", textAlign: "center" }}>
            <div
              style={{
                fontSize: "0.75rem",
                color: "#666666",
                textTransform: "uppercase",
                letterSpacing: "0.05em",
                marginBottom: "8px",
              }}
            >
              Blind Spots
            </div>
            <div
              style={{
                fontSize: "2.5rem",
                fontWeight: 700,
                color: (blind_spots ?? []).length > 0 ? "#C53030" : "#0D8A5E",
              }}
            >
              {(blind_spots ?? []).length}
            </div>
          </div>
        </Card>
      </div>

      {/* Domain Breakdown */}
      <h3
        style={{ fontSize: "1.125rem", marginBottom: "16px", color: "#1A1A1A" }}
      >
        Domain Scores
      </h3>
      <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
        {(domainScores || []).map((d) => (
          <Card key={d.domain_code}>
            <div style={{ padding: "20px" }}>
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  marginBottom: "12px",
                }}
              >
                <div>
                  <span style={{ fontWeight: 600, color: "#333333" }}>
                    {d.domain_code} · {d.domain_name}
                  </span>
                </div>
                <div
                  style={{
                    fontSize: "1.5rem",
                    fontWeight: 700,
                    color: getScoreColor(d.score ?? 0),
                  }}
                >
                  {(d.score ?? 0).toFixed(2)}
                </div>
              </div>
              {/* Subdomain bars */}
              <div
                style={{ display: "flex", flexDirection: "column", gap: "8px" }}
              >
                {(d.subdomains || []).map((sd) => (
                  <div
                    key={sd.subdomain_code}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "12px",
                    }}
                  >
                    <div
                      style={{
                        width: "220px",
                        fontSize: "0.75rem",
                        color: "#8A8A86",
                      }}
                    >
                      <span
                        style={{ fontFamily: "'IBM Plex Mono', monospace" }}
                      >
                        {sd.subdomain_code}
                      </span>
                      <span style={{ marginLeft: "6px", color: "#666666" }}>
                        {sd.subdomain_name}
                      </span>
                    </div>
                    <div
                      style={{
                        flex: 1,
                        height: "8px",
                        background: "rgba(0,0,0,0.06)",
                        borderRadius: "4px",
                        overflow: "hidden",
                      }}
                    >
                      <div
                        style={{
                          height: "100%",
                          width: `${((sd.final_score ?? 0) / 5) * 100}%`,
                          background: getScoreColor(sd.final_score ?? 0),
                          borderRadius: "4px",
                          transition: "width 0.5s ease",
                        }}
                      />
                    </div>
                    <div
                      style={{
                        width: "50px",
                        textAlign: "right",
                        fontSize: "0.825rem",
                        fontWeight: 600,
                        color: getScoreColor(sd.final_score ?? 0),
                      }}
                    >
                      {(sd.final_score ?? 0).toFixed(1)}
                    </div>
                    {sd.cap_applied && (
                      <span
                        style={{
                          fontSize: "0.65rem",
                          padding: "1px 6px",
                          borderRadius: "4px",
                          background: "rgba(248,113,113,0.12)",
                          color: "#F87171",
                          fontWeight: 600,
                        }}
                      >
                        CAPPED
                      </span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </Card>
        ))}
      </div>

      {/* Blind Spots */}
      {blind_spots.length > 0 && (
        <div style={{ marginTop: "24px" }}>
          <h3
            style={{
              fontSize: "1.125rem",
              marginBottom: "12px",
              color: "#C53030",
            }}
          >
            ⚠️ Blind Spots Detected
          </h3>
          <Card>
            <div style={{ padding: "16px" }}>
              {blind_spots.map((b, i) => (
                <div
                  key={i}
                  style={{
                    padding: "8px 0",
                    fontSize: "0.875rem",
                    color: "#333333",
                    borderBottom:
                      i < blind_spots.length - 1
                        ? "1px solid rgba(0,0,0,0.06)"
                        : "none",
                  }}
                >
                  {b}
                </div>
              ))}
            </div>
          </Card>
        </div>
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
