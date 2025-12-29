import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,  // Safari compatibility: enable credentials
  timeout: 30000,  // 30 second timeout
});

// ==================== OFFLINE QUEUE MANAGEMENT ====================
interface QueuedRequest {
  id: string;
  url: string;
  method: string;
  data: any;
  timestamp: number;
}

const QUEUE_KEY = 'pending_api_requests';

const getQueue = (): QueuedRequest[] => {
  try {
    const queue = localStorage.getItem(QUEUE_KEY);
    return queue ? JSON.parse(queue) : [];
  } catch {
    return [];
  }
};

const addToQueue = (request: Omit<QueuedRequest, 'id' | 'timestamp'>) => {
  const queue = getQueue();
  queue.push({
    ...request,
    id: `${Date.now()}-${Math.random()}`,
    timestamp: Date.now(),
  });
  localStorage.setItem(QUEUE_KEY, JSON.stringify(queue));
};

const removeFromQueue = (id: string) => {
  const queue = getQueue();
  const filtered = queue.filter(req => req.id !== id);
  localStorage.setItem(QUEUE_KEY, JSON.stringify(filtered));
};

// Sync pending requests when connection is restored
export const syncPendingRequests = async () => {
  const queue = getQueue();
  console.log(`🔄 Syncing ${queue.length} pending requests...`);
  
  for (const request of queue) {
    try {
      await api.request({
        url: request.url,
        method: request.method as any,
        data: request.data,
      });
      removeFromQueue(request.id);
      console.log(`✅ Synced: ${request.url}`);
    } catch (error) {
      console.error(`❌ Failed to sync: ${request.url}`, error);
      // Keep in queue for retry
    }
  }
};

// Add JWT token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle errors and queue for offline
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Handle 401 (unauthorized)
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token');
      window.location.href = '/login';
      return Promise.reject(error);
    }
    
    // Handle network errors (offline) - queue for later
    // Only treat as network error if there's no response AND no status code (true connection failure)
    if (!error.response && error.request && error.code === 'ERR_NETWORK') {
      console.warn('📡 Network error detected - queueing request for later sync');
      const originalRequest = error.config;
      
      // Only queue POST/PUT/PATCH requests (not GET)
      if (['post', 'put', 'patch'].includes(originalRequest.method?.toLowerCase() || '')) {
        addToQueue({
          url: originalRequest.url || '',
          method: originalRequest.method || 'post',
          data: originalRequest.data,
        });
        
        // Show user-friendly message
        console.log('💾 Request saved locally. Will sync when connection is restored.');
        
        // Return a resolved promise so the UI doesn't show an error
        return Promise.resolve({ data: { queued: true, message: 'Saved locally for sync' } });
      }
    }
    
    // Log other errors for debugging
    if (error.response) {
      console.error(`❌ API Error ${error.response.status}:`, error.response.data);
    } else if (error.request) {
      console.error('❌ Backend server not responding. Is it running on port 8000?');
    }
    
    return Promise.reject(error);
  }
);

export default api;

// Auth API
export const authAPI = {
  login: async (username: string, password: string) => {
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);
    
    const response = await api.post('/token', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });
    return response.data;
  },
  
  register: async (email: string, password: string, fullName: string, role: string) => {
    const response = await api.post('/users', {
      email,
      password,
      full_name: fullName,
      role,
    });
    return response.data;
  },
  
  getCurrentUser: async () => {
    const response = await api.get('/users/me');
    return response.data;
  },
};

// Assessment API
export const assessmentAPI = {
  list: async () => {
    const response = await api.get('/assessments');
    return response.data;
  },
  
  create: async (data: {
    client_name: string;
    site_name: string;
    assessment_date: string;
  }) => {
    const response = await api.post('/assessments', data);
    return response.data;
  },
  
  getById: async (id: number) => {
    const response = await api.get(`/assessments/${id}`);
    return response.data;
  },
  
  update: async (id: number, data: any) => {
    const response = await api.put(`/assessments/${id}`, data);
    return response.data;
  },
  
  delete: async (id: number) => {
    const response = await api.delete(`/assessments/${id}`);
    return response.data;
  },
  
  generateReport: async (id: number) => {
    const response = await api.post(`/assessments/${id}/generate-report`);
    return response.data;
  },
  
  downloadReport: async (id: number) => {
    const response = await api.get(`/assessments/${id}/report/download`, {
      responseType: 'blob',
    });
    return response.data;
  },
};

// Question API
export const questionAPI = {
  listAll: async () => {
    const response = await api.get('/questions');
    return response.data;
  },
  
  getByAssessment: async (assessmentId: number) => {
    const response = await api.get(`/assessments/${assessmentId}/questions`);
    return response.data;
  },
  
  getResponses: async (assessmentId: number) => {
    const response = await api.get(`/assessments/${assessmentId}/responses`);
    return response.data;
  },
  
  submitResponse: async (assessmentId: number, questionId: number, data: {
    answer_text?: string;
    score?: number;
    has_evidence: boolean;
    notes?: string;
    is_draft?: boolean;  // New: Draft state
    is_na?: boolean;     // New: Not Applicable flag
  }) => {
    const payload: any = {
      question_id: questionId,
      response_value: data.is_na ? 'N/A' : (data.answer_text || (data.score !== null && data.score !== undefined ? data.score.toString() : '')),
      numeric_score: data.score,  // CRITICAL: Send the numeric score separately!
      is_draft: data.is_draft ?? false,
      is_na: data.is_na ?? false,
    };
    if (data.notes) {
      payload.evidence_notes = data.notes;
    }
    const response = await api.post(`/assessments/${assessmentId}/responses`, payload);
    return response.data;
  },
  
  // Sync pending requests when dashboard loads
  syncOfflineData: syncPendingRequests,
};

// Observation API
export const observationAPI = {
  list: async (assessmentId: number) => {
    const response = await api.get(`/assessments/${assessmentId}/observations`);
    return response.data;
  },
  
  create: async (assessmentId: number, data: {
    category: string;
    description: string;
    compliance_status: string;
    severity?: string;
    location?: string;
  }) => {
    const response = await api.post(`/assessments/${assessmentId}/observations`, data);
    return response.data;
  },
  
  createBatch: async (assessmentId: number, observations: any[]) => {
    const response = await api.post(`/assessments/${assessmentId}/observations/batch`, observations);
    return response.data;
  },
  
  uploadEvidence: async (observationId: number, file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post(`/observations/${observationId}/evidence`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },
};

// CMMS Data API
export const cmmsAPI = {
  upload: async (assessmentId: number, file: File, columnMapping?: any) => {
    const formData = new FormData();
    formData.append('file', file);
    if (columnMapping) {
      formData.append('column_mapping', JSON.stringify(columnMapping));
    }
    const response = await api.post(`/assessments/${assessmentId}/analyze-work-orders`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },
  
  getAnalysis: async (assessmentId: number) => {
    const response = await api.get(`/assessments/${assessmentId}/data-analyses`);
    return response.data;
  },
};

// ISO 14224 API
export const iso14224API = {
  validate: async (assessmentId: number) => {
    const response = await api.post(`/assessments/${assessmentId}/iso14224/validate`);
    return response.data;
  },
  
  getResults: async (assessmentId: number) => {
    const response = await api.get(`/assessments/${assessmentId}/iso14224/results`);
    return response.data;
  },
};

// Scoring API
export const scoringAPI = {
  calculate: async (assessmentId: number) => {
    const response = await api.post(`/assessments/${assessmentId}/calculate-scores`);
    return response.data;
  },
  
  getScores: async (assessmentId: number) => {
    const response = await api.get(`/assessments/${assessmentId}/scores`);
    return response.data;
  },
};
