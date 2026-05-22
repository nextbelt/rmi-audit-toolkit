/**
 * RMI Assessment Store (Zustand)
 * Manages assessment state, scoring, benchmarks, and practice recommendations.
 */
import { create } from 'zustand';
import { v2API } from './clientV2';
import type {
  AssessmentV2,
  QuestionV2,
  ProgressInfo,
  ScoringResult,
  BenchmarkResult,
  PracticeRecommendation,
  RecommendationsResponse,
  DomainInfo,
  AIEvidenceAnalysis,
  CMMSUpload,
} from './clientV2';

interface V2State {
  // Framework
  domains: DomainInfo[];
  frameworkLoaded: boolean;

  // Assessment list
  assessments: AssessmentV2[];
  assessmentsLoading: boolean;

  // Current assessment
  currentAssessment: AssessmentV2 | null;
  questions: QuestionV2[];
  roleCounts: Record<string, number>;
  progress: ProgressInfo | null;
  questionsLoading: boolean;

  // Saved responses (loaded from backend)
  savedResponses: Record<number, { score: number; notes: string }>;

  // Evidence + CMMS state (keyed per question / assessment)
  responseExtras: Record<number, {
    evidence_file?: {
      filename: string | null;
      mime: string | null;
      size_bytes: number | null;
      uploaded_at: string | null;
    } | null;
    ai_analysis?: {
      suggested_score: number | null;
      observations: string | null;
      confidence: string | null;
      analyzed_at: string | null;
    } | null;
  }>;
  cmmsUploads: CMMSUpload[];
  cmmsLoading: boolean;

  // Scoring
  scoringResult: ScoringResult | null;
  scoringLoading: boolean;

  // Benchmarking
  benchmark: BenchmarkResult | null;
  benchmarkLoading: boolean;

  // Practice Library
  recommendations: PracticeRecommendation[];
  recommendationsData: RecommendationsResponse | null;
  recommendationsLoading: boolean;

  // Error
  error: string | null;

  // ── Actions ──
  loadFramework: () => Promise<void>;
  loadAssessments: () => Promise<void>;
  createAssessment: (data: {
    organization_name: string;
    site_name: string;
    assessment_date: string;
    assessment_mode: 'quickscan' | 'standard' | 'deepdive';
    industry_module?: string;
    industry?: string;
  }) => Promise<AssessmentV2>;
  loadAssessment: (id: number) => Promise<void>;
  loadQuestions: (assessmentId: number, role?: string) => Promise<void>;
  loadProgress: (assessmentId: number) => Promise<void>;
  loadResponses: (assessmentId: number) => Promise<Record<number, { score: number; notes: string }>>;
  submitResponse: (assessmentId: number, data: {
    question_id: number;
    response_value: string;
    numeric_score: number;
    respondent_role?: string;
    evidence_status?: string;
    evidence_notes?: string;
    evidence_grade?: string;
    is_draft?: boolean;
    is_na?: boolean;
  }) => Promise<void>;
  calculateScores: (assessmentId: number) => Promise<void>;
  loadBenchmark: (assessmentId: number) => Promise<void>;
  loadRecommendations: (assessmentId: number) => Promise<void>;
  upgradeMode: (assessmentId: number, newMode: string) => Promise<void>;

  // Evidence
  uploadEvidence: (assessmentId: number, questionId: number, file: File) => Promise<void>;
  deleteEvidence: (assessmentId: number, questionId: number) => Promise<void>;
  analyzeEvidence: (assessmentId: number, questionId: number) => Promise<AIEvidenceAnalysis>;

  // CMMS
  loadCMMSUploads: (assessmentId: number) => Promise<void>;
  uploadCMMS: (assessmentId: number, file: File, kind: 'work_orders' | 'pm') => Promise<CMMSUpload>;
  deleteCMMSUpload: (assessmentId: number, uploadId: number) => Promise<void>;

  clearError: () => void;
  reset: () => void;
}

const initialState = {
  domains: [],
  frameworkLoaded: false,
  assessments: [],
  assessmentsLoading: false,
  currentAssessment: null,
  questions: [],
  roleCounts: {},
  progress: null,
  questionsLoading: false,
  savedResponses: {},
  responseExtras: {},
  cmmsUploads: [],
  cmmsLoading: false,
  scoringResult: null,
  scoringLoading: false,
  benchmark: null,
  benchmarkLoading: false,
  recommendations: [],
  recommendationsData: null,
  recommendationsLoading: false,
  error: null,
};

export const useV2Store = create<V2State>((set, get) => ({
  ...initialState,

  loadFramework: async () => {
    if (get().frameworkLoaded) return;
    try {
      const data = await v2API.getFramework();
      set({ domains: data.domains, frameworkLoaded: true });
    } catch (e: any) {
      set({ error: e.message || 'Failed to load framework' });
    }
  },

  loadAssessments: async () => {
    set({ assessmentsLoading: true, error: null });
    try {
      const assessments = await v2API.listAssessments();
      set({ assessments, assessmentsLoading: false });
    } catch (e: any) {
      set({ error: e.message || 'Failed to load assessments', assessmentsLoading: false });
    }
  },

  createAssessment: async (data) => {
    try {
      const created = await v2API.createAssessment(data);
      set((s) => ({ assessments: [...s.assessments, created] }));
      return created;
    } catch (e: any) {
      set({ error: e.message || 'Failed to create assessment' });
      throw e;
    }
  },

  loadAssessment: async (id) => {
    try {
      const assessment = await v2API.getAssessment(id);
      set({ currentAssessment: assessment });
    } catch (e: any) {
      set({ error: e.message || 'Failed to load assessment' });
    }
  },

  loadQuestions: async (assessmentId, role) => {
    set({ questionsLoading: true });
    try {
      const { questions, roleCounts } = await v2API.getQuestions(assessmentId, role);
      set({ questions, roleCounts, questionsLoading: false });
    } catch (e: any) {
      set({ error: e.message || 'Failed to load questions', questionsLoading: false });
    }
  },

  loadProgress: async (assessmentId) => {
    try {
      const progress = await v2API.getProgress(assessmentId);
      set({ progress });
    } catch (e: any) {
      set({ error: e.message || 'Failed to load progress' });
    }
  },

  loadResponses: async (assessmentId) => {
    try {
      const raw = await v2API.getResponses(assessmentId);
      const mapped: Record<number, { score: number; notes: string }> = {};
      const extras: Record<number, any> = {};
      for (const r of raw as any[]) {
        if (r.numeric_score != null) {
          mapped[r.question_id] = {
            score: r.numeric_score,
            notes: r.evidence_notes || '',
          };
        }
        if (r.evidence_file || r.ai_analysis) {
          extras[r.question_id] = {
            evidence_file: r.evidence_file ?? null,
            ai_analysis: r.ai_analysis ?? null,
          };
        }
      }
      set({ savedResponses: mapped, responseExtras: extras });
      return mapped;
    } catch (e: any) {
      set({ error: e.message || 'Failed to load responses' });
      return {};
    }
  },

  submitResponse: async (assessmentId, data) => {
    try {
      await v2API.submitResponse(assessmentId, data);
      // Reload progress after submission
      const progress = await v2API.getProgress(assessmentId);
      set({ progress });
    } catch (e: any) {
      set({ error: e.message || 'Failed to submit response' });
      throw e; // Re-throw so callers (autoSave) can handle it
    }
  },

  calculateScores: async (assessmentId) => {
    set({ scoringLoading: true });
    try {
      const result = await v2API.calculateScores(assessmentId);
      // Reload assessment so overall_rmi is updated for benchmark/practices guards
      const assessment = await v2API.getAssessment(assessmentId);
      set({ scoringResult: result, currentAssessment: assessment, scoringLoading: false });
    } catch (e: any) {
      set({ error: e.message || 'Failed to calculate scores', scoringLoading: false });
    }
  },

  loadBenchmark: async (assessmentId) => {
    set({ benchmarkLoading: true });
    try {
      const benchmark = await v2API.getBenchmark(assessmentId);
      set({ benchmark, benchmarkLoading: false });
    } catch (e: any) {
      // 400 = "not scored yet" — expected, don't show as global error
      const status = e?.response?.status;
      if (status === 400) {
        set({ benchmark: null, benchmarkLoading: false });
      } else {
        set({ error: e.message || 'Failed to load benchmark', benchmarkLoading: false });
      }
    }
  },

  loadRecommendations: async (assessmentId) => {
    set({ recommendationsLoading: true });
    try {
      const data = await v2API.getRecommendations(assessmentId);
      set({
        recommendations: data.top_recommendations ?? [],
        recommendationsData: data,
        recommendationsLoading: false,
      });
    } catch (e: any) {
      // 400 = "not scored yet" — expected, don't show as global error
      const status = e?.response?.status;
      if (status === 400) {
        set({ recommendations: [], recommendationsData: null, recommendationsLoading: false });
      } else {
        set({ error: e.message || 'Failed to load recommendations', recommendationsLoading: false });
      }
    }
  },

  upgradeMode: async (assessmentId, newMode) => {
    try {
      await v2API.upgradeMode(assessmentId, newMode);
      // Reload assessment to reflect new mode
      const assessment = await v2API.getAssessment(assessmentId);
      set({ currentAssessment: assessment });
    } catch (e: any) {
      set({ error: e.message || 'Failed to upgrade mode' });
    }
  },

  uploadEvidence: async (assessmentId, questionId, file) => {
    try {
      const meta = await v2API.uploadEvidence(assessmentId, questionId, file);
      set((s) => ({
        responseExtras: {
          ...s.responseExtras,
          [questionId]: {
            ...(s.responseExtras[questionId] || {}),
            evidence_file: {
              filename: meta.filename,
              mime: meta.mime,
              size_bytes: meta.size_bytes,
              uploaded_at: meta.uploaded_at,
            },
            ai_analysis: null, // stale once new file is uploaded
          },
        },
      }));
    } catch (e: any) {
      set({ error: e?.response?.data?.detail || e.message || 'Failed to upload evidence' });
      throw e;
    }
  },

  deleteEvidence: async (assessmentId, questionId) => {
    try {
      await v2API.deleteEvidence(assessmentId, questionId);
      set((s) => {
        const next = { ...s.responseExtras };
        delete next[questionId];
        return { responseExtras: next };
      });
    } catch (e: any) {
      set({ error: e?.response?.data?.detail || e.message || 'Failed to delete evidence' });
      throw e;
    }
  },

  analyzeEvidence: async (assessmentId, questionId) => {
    try {
      const result = await v2API.analyzeEvidence(assessmentId, questionId);
      set((s) => ({
        responseExtras: {
          ...s.responseExtras,
          [questionId]: {
            ...(s.responseExtras[questionId] || {}),
            ai_analysis: {
              suggested_score: result.suggested_score,
              observations: result.observations,
              confidence: result.confidence,
              analyzed_at: result.analyzed_at,
            },
          },
        },
      }));
      return result;
    } catch (e: any) {
      set({ error: e?.response?.data?.detail || e.message || 'AI analysis failed' });
      throw e;
    }
  },

  loadCMMSUploads: async (assessmentId) => {
    set({ cmmsLoading: true });
    try {
      const list = await v2API.listCMMSUploads(assessmentId);
      set({ cmmsUploads: list, cmmsLoading: false });
    } catch (e: any) {
      set({ error: e.message || 'Failed to load CMMS uploads', cmmsLoading: false });
    }
  },

  uploadCMMS: async (assessmentId, file, kind) => {
    try {
      const upload = await v2API.uploadCMMS(assessmentId, file, kind);
      set((s) => ({ cmmsUploads: [upload, ...s.cmmsUploads] }));
      return upload;
    } catch (e: any) {
      set({ error: e?.response?.data?.detail || e.message || 'Failed to upload CMMS snapshot' });
      throw e;
    }
  },

  deleteCMMSUpload: async (assessmentId, uploadId) => {
    try {
      await v2API.deleteCMMSUpload(assessmentId, uploadId);
      set((s) => ({ cmmsUploads: s.cmmsUploads.filter((u) => u.id !== uploadId) }));
    } catch (e: any) {
      set({ error: e?.response?.data?.detail || e.message || 'Failed to delete CMMS upload' });
      throw e;
    }
  },

  clearError: () => set({ error: null }),

  reset: () => set(initialState),
}));
