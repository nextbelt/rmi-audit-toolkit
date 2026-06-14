/**
 * RMI Assessments API Client
 * All endpoints under /api/v2/ (route prefix is historical).
 */
import api from "./client";

// ═══════════════════════════════════════════
//  Types
// ═══════════════════════════════════════════

export interface DomainInfo {
  code: string;
  name: string;
  description: string;
  subdomains: SubdomainInfo[];
}

export interface SubdomainInfo {
  code: string;
  name: string;
}

export interface FrameworkResponse {
  domains: DomainInfo[];
}

export interface AssessmentV2 {
  id: number;
  organization_name: string;
  site_name: string;
  industry: string | null;
  assessment_mode: "quickscan" | "standard" | "deepdive";
  industry_module: string | null;
  status: string;
  assessment_date: string;
  created_at: string;
  overall_rmi: number | null;
  maturity_level: string | null;
  confidence_score: number | null;
  finalized_at?: string | null;
}

export interface QuestionV2 {
  id: number;
  question_code: string;
  question_text: string;
  question_type: string;
  domain?: string;
  domain_code?: string;
  domain_name?: string;
  subdomain_code: string;
  subdomain_name: string;
  target_role: string;
  weight: number;
  is_critical: boolean;
  evidence_required: boolean;
  evidence_guidance: string | null;
  scoring_rubric: Record<string, string>;
  calibration_anchor: string | null;
  practice_link: string | null;
}

export interface ProgressInfo {
  assessment_id: number;
  mode: string;
  total_questions: number;
  answered: number;
  completion_pct: number;
  by_domain: Record<string, { total: number; answered: number; pct: number }>;
}

export interface SubdomainScoreResult {
  subdomain_code: string;
  subdomain_name: string;
  raw_score: number;
  weighted_score: number;
  final_score: number;
  cap_applied: boolean;
  cap_reason: string | null;
  confidence: number;
}

export interface DomainScoreResult {
  domain_code: string;
  domain_name: string;
  score: number;
  subdomains: SubdomainScoreResult[];
}

export interface ScoringResult {
  assessment_id: number;
  overall_rmi: number;
  maturity_level: string;
  confidence: number | null;
  confidence_score: number;
  confidence_band: [number | null, number | null];
  domains: DomainScoreResult[];
  blind_spots: string[];
  cross_domain_caps: string[];
  caps_applied: string[];
  iso_55001_readiness: number;
  velocity: Record<string, any> | null;
  domain_weights: Record<string, number>;
  calculated_at: string;
}

export interface BenchmarkResult {
  assessment_id: number;
  status: "benchmarked" | "insufficient_peers";
  overall_rmi: number | null;
  overall_percentile: number;
  peer_count: number;
  min_required?: number;
  message?: string;
  domain_percentiles: Record<
    string,
    { score: number; percentile: number; quartile: number }
  >;
  quartile: number;
  quartile_label: string;
  peer_stats: {
    count: number;
    mean: number | null;
    std_dev: number | null;
    min: number | null;
    max: number | null;
  };
}

export interface PracticeRecommendation {
  practice_id: number;
  title: string;
  description: string;
  subdomain_code: string;
  subdomain_name: string;
  current_score: number;
  target_level: number;
  priority_score: number;
  impact: string;
  effort: string;
  timeline: string;
  practice_link: string | null;
  tools: string[];
  success_metrics: string[];
  resources: string[];
}

export interface RecommendationsResponse {
  assessment_id: number;
  overall_rmi: number | null;
  current_maturity: number;
  target_maturity: number;
  pathway: {
    from_level: number;
    to_level: number;
    focus: string;
    typical_timeline: string;
    key_themes: string[];
  };
  total_recommendations: number;
  top_recommendations: PracticeRecommendation[];
  by_domain: Record<string, PracticeRecommendation[]>;
}

export interface PracticeDetail {
  id: number;
  practice_id: string;
  title: string;
  subdomain_code: string;
  pathways: Record<string, any>;
  references: any;
  industry_variations: any;
  tools: any;
}

export interface ISOClauseResult {
  clause: string;
  name: string;
  score: number | null;
  gap: number | null;
  status: "ready" | "exceeds" | "gap" | "major_gap" | "unanswered" | "unmapped";
  questions_total: number;
  questions_answered: number;
  low_questions: Array<{ id: number; code: string; text: string; score: number }>;
}

export interface ISOSection {
  section: string;
  title: string;
  ready: number;
  total: number;
  clauses: ISOClauseResult[];
}

export interface ISOGapReport {
  assessment_id: number;
  floor: number;
  summary: {
    total_clauses_mapped: number;
    clauses_ready: number;
    clauses_with_gap: number;
    clauses_major_gap: number;
    overall_readiness_pct: number;
  };
  sections: ISOSection[];
}

export interface EvidenceFileMeta {
  filename: string | null;
  mime: string | null;
  size_bytes: number | null;
  uploaded_at: string | null;
}

export interface AIEvidenceAnalysis {
  suggested_score: number | null;
  observations: string;
  confidence: "HIGH" | "MEDIUM" | "LOW";
  key_findings: string[];
  analyzed_kind: "image" | "pdf" | "unsupported";
  analyzed_at: string;
}

export interface CMMSUpload {
  id: number;
  assessment_id: number;
  kind: "work_orders" | "pm";
  original_filename: string | null;
  file_size_bytes: number | null;
  status: "processed" | "processing" | "error";
  error_message: string | null;
  metrics: Record<string, any> | null;
  bad_actors: Array<[string, number]> | null;
  record_count: number | null;
  uploaded_at: string;
}

// ═══════════════════════════════════════════
//  API Methods
// ═══════════════════════════════════════════

export const v2API = {
  // ── Health & Framework ──
  health: async () => {
    const r = await api.get("/api/v2/health");
    return r.data;
  },

  getFramework: async (): Promise<FrameworkResponse> => {
    const r = await api.get("/api/v2/framework");
    return r.data;
  },

  // ── Assessments ──
  createAssessment: async (data: {
    organization_name: string;
    site_name: string;
    assessment_date: string;
    assessment_mode: "quickscan" | "standard" | "deepdive";
    industry_module?: string;
    industry?: string;
  }): Promise<AssessmentV2> => {
    const r = await api.post("/api/v2/assessments", data);
    return r.data;
  },

  listAssessments: async (): Promise<AssessmentV2[]> => {
    const r = await api.get("/api/v2/assessments");
    return r.data;
  },

  getAssessment: async (id: number): Promise<AssessmentV2> => {
    const r = await api.get(`/api/v2/assessments/${id}`);
    return r.data;
  },

  // ── Questions & Routing ──
  getQuestions: async (
    assessmentId: number,
    role?: string
  ): Promise<{
    questions: QuestionV2[];
    roleCounts: Record<string, number>;
  }> => {
    const params = role ? { respondent_role: role } : {};
    const r = await api.get(`/api/v2/assessments/${assessmentId}/questions`, {
      params,
    });
    const questions = Array.isArray(r.data) ? r.data : r.data.questions ?? [];
    const roleCounts = r.data.role_counts ?? {};
    return { questions, roleCounts };
  },

  getProgress: async (assessmentId: number): Promise<ProgressInfo> => {
    const r = await api.get(`/api/v2/assessments/${assessmentId}/progress`);
    return r.data;
  },

  upgradeMode: async (assessmentId: number, newMode: string) => {
    const r = await api.post(
      `/api/v2/assessments/${assessmentId}/upgrade-mode`,
      {
        new_mode: newMode,
      }
    );
    return r.data;
  },

  // ── Responses ──
  getResponses: async (
    assessmentId: number
  ): Promise<
    Array<{
      id: number;
      question_id: number;
      numeric_score: number | null;
      response_value: string | null;
      respondent_role: string | null;
      evidence_notes: string | null;
      is_na: boolean;
    }>
  > => {
    const r = await api.get(`/api/v2/assessments/${assessmentId}/responses`);
    return r.data;
  },

  submitResponse: async (
    assessmentId: number,
    data: {
      question_id: number;
      response_value: string;
      numeric_score: number;
      respondent_role?: string;
      evidence_status?: string;
      evidence_notes?: string;
      evidence_grade?: string;
      is_draft?: boolean;
      is_na?: boolean;
    }
  ) => {
    // Map frontend field names → backend Pydantic schema names
    const payload = {
      question_id: data.question_id,
      numeric_score: data.numeric_score,
      text_response: data.response_value,
      respondent_role: data.respondent_role,
      evidence_status: data.evidence_status || "not_required",
      evidence_grade: data.evidence_grade,
      notes: data.evidence_notes,
      is_draft: data.is_draft ?? false,
      is_na: data.is_na ?? false,
    };
    const r = await api.post(
      `/api/v2/assessments/${assessmentId}/responses`,
      payload
    );
    return r.data;
  },

  submitBulkResponses: async (
    assessmentId: number,
    responses: Array<{
      question_id: number;
      response_value: string;
      numeric_score: number;
      respondent_role?: string;
    }>
  ) => {
    const r = await api.post(
      `/api/v2/assessments/${assessmentId}/responses/bulk`,
      {
        responses,
      }
    );
    return r.data;
  },

  // ── Scoring ──
  calculateScores: async (assessmentId: number): Promise<ScoringResult> => {
    const r = await api.post(
      `/api/v2/assessments/${assessmentId}/calculate-scores`
    );
    return r.data;
  },

  // ── Benchmarking ──
  getBenchmark: async (assessmentId: number): Promise<BenchmarkResult> => {
    const r = await api.get(`/api/v2/assessments/${assessmentId}/benchmark`);
    const d = r.data;
    // Map backend field names → frontend types
    return {
      assessment_id: d.assessment_id,
      status: d.status,
      overall_rmi: d.overall_rmi ?? null,
      overall_percentile: d.percentile ?? 0,
      peer_count: d.peer_stats?.count ?? d.peer_count ?? 0,
      min_required: d.min_required,
      message: d.message,
      domain_percentiles: d.domain_benchmarks ?? {},
      quartile: d.quartile ?? 0,
      quartile_label: d.quartile_label ?? "",
      peer_stats: d.peer_stats ?? {
        count: 0,
        mean: null,
        std_dev: null,
        min: null,
        max: null,
      },
    };
  },

  getIndustryStats: async (industry: string) => {
    const r = await api.get(`/api/v2/benchmarks/industry/${industry}`);
    return r.data;
  },

  portfolioBenchmark: async (assessmentIds: number[]) => {
    const r = await api.post("/api/v2/benchmarks/portfolio", {
      assessment_ids: assessmentIds,
    });
    return r.data;
  },

  // ── Practice Library ──
  getRecommendations: async (
    assessmentId: number,
    topN = 10
  ): Promise<RecommendationsResponse> => {
    const r = await api.get(
      `/api/v2/assessments/${assessmentId}/recommendations`,
      {
        params: { top_n: topN },
      }
    );
    return r.data;
  },

  getPracticeDetail: async (practiceId: number): Promise<PracticeDetail> => {
    const r = await api.get(`/api/v2/practices/${practiceId}`);
    return r.data;
  },

  getSubdomainPractices: async (subdomainCode: string) => {
    const r = await api.get(`/api/v2/practices/subdomain/${subdomainCode}`);
    return r.data;
  },

  // ── ISO 55001 gap report ──
  getISOGapReport: async (assessmentId: number): Promise<ISOGapReport> => {
    const r = await api.get(`/api/v2/assessments/${assessmentId}/iso-55001-gaps`);
    return r.data;
  },

  // ── Evidence ──
  uploadEvidence: async (
    assessmentId: number,
    questionId: number,
    file: File,
  ): Promise<{
    filename: string;
    mime: string;
    size_bytes: number;
    uploaded_at: string;
    evidence_status: string | null;
    ai_verdict: "relevant" | "irrelevant" | "unclear";
    ai_reason: string | null;
    ai_suggested_score: number | null;
    ai_confidence: string | null;
    accepted: boolean;
  }> => {
    const fd = new FormData();
    fd.append("file", file);
    const r = await api.post(
      `/api/v2/assessments/${assessmentId}/responses/${questionId}/evidence`,
      fd,
      { headers: { "Content-Type": "multipart/form-data" } },
    );
    return r.data;
  },

  fetchEvidenceBlob: async (
    assessmentId: number,
    questionId: number,
  ): Promise<Blob> => {
    const r = await api.get(
      `/api/v2/assessments/${assessmentId}/responses/${questionId}/evidence`,
      { responseType: "blob" },
    );
    return r.data;
  },

  deleteEvidence: async (assessmentId: number, questionId: number) => {
    const r = await api.delete(
      `/api/v2/assessments/${assessmentId}/responses/${questionId}/evidence`,
    );
    return r.data;
  },

  analyzeEvidence: async (
    assessmentId: number,
    questionId: number,
  ): Promise<AIEvidenceAnalysis> => {
    const r = await api.post(
      `/api/v2/assessments/${assessmentId}/responses/${questionId}/analyze-evidence`,
    );
    return r.data;
  },

  // ── CMMS snapshot ──
  uploadCMMS: async (
    assessmentId: number,
    file: File,
    kind: "work_orders" | "pm" = "work_orders",
  ): Promise<CMMSUpload> => {
    const fd = new FormData();
    fd.append("file", file);
    fd.append("kind", kind);
    const r = await api.post(
      `/api/v2/assessments/${assessmentId}/cmms-uploads`,
      fd,
      { headers: { "Content-Type": "multipart/form-data" } },
    );
    return r.data;
  },

  listCMMSUploads: async (assessmentId: number): Promise<CMMSUpload[]> => {
    const r = await api.get(`/api/v2/assessments/${assessmentId}/cmms-uploads`);
    return r.data;
  },

  deleteCMMSUpload: async (assessmentId: number, uploadId: number) => {
    const r = await api.delete(
      `/api/v2/assessments/${assessmentId}/cmms-uploads/${uploadId}`,
    );
    return r.data;
  },

  // ── Reports ──
  generateReport: async (
    assessmentId: number,
  ): Promise<{ message: string; file_path: string; download_url: string }> => {
    const r = await api.post(`/assessments/${assessmentId}/generate-report`);
    return r.data;
  },

  downloadReport: async (assessmentId: number): Promise<Blob> => {
    const r = await api.get(`/assessments/${assessmentId}/report/download`, {
      responseType: "blob",
    });
    return r.data;
  },

  finalizeAssessment: async (assessmentId: number) => {
    const r = await api.post(`/assessments/${assessmentId}/finalize`);
    return r.data;
  },

  // ── Direct Questions ──
  listAllQuestions: async (
    domain?: string,
    subdomain?: string
  ): Promise<QuestionV2[]> => {
    const params: Record<string, string> = {};
    if (domain) params.domain = domain;
    if (subdomain) params.subdomain = subdomain;
    const r = await api.get("/api/v2/questions", { params });
    return r.data;
  },

  getCalibration: async (questionId: number) => {
    const r = await api.get(`/api/v2/questions/${questionId}/calibration`);
    return r.data;
  },
};

/**
 * Generate (if needed) and download the executive PDF for an assessment,
 * triggering a browser "Save as". Returns nothing; throws on failure so the
 * caller can surface an error.
 */
export async function generateAndDownloadReport(
  assessmentId: number,
  orgName: string,
  siteName: string,
): Promise<void> {
  await v2API.generateReport(assessmentId);
  const blob = await v2API.downloadReport(assessmentId);
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  const safe = `RMI_Audit_Report_${orgName}_${siteName}`.replace(/[^A-Za-z0-9._-]+/g, "_");
  link.download = `${safe}.pdf`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
}

export default v2API;
