import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add JWT token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle 401 errors (unauthorized)
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token');
      window.location.href = '/login';
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
    const response = await api.post('/users/', {
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
    const response = await api.get('/assessments/');
    return response.data;
  },
  
  create: async (data: {
    client_name: string;
    site_location: string;
    start_date: string;
    end_date?: string;
  }) => {
    const response = await api.post('/assessments/', data);
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
    const response = await api.get('/questions/');
    return response.data;
  },
  
  getByAssessment: async (assessmentId: number) => {
    const response = await api.get(`/assessments/${assessmentId}/questions`);
    return response.data;
  },
  
  submitResponse: async (assessmentId: number, questionId: number, data: {
    answer_text?: string;
    score?: number;
    has_evidence: boolean;
    notes?: string;
  }) => {
    const response = await api.post(`/assessments/${assessmentId}/questions/${questionId}/response`, data);
    return response.data;
  },
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
    const response = await api.post(`/assessments/${assessmentId}/cmms/upload`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },
  
  getAnalysis: async (assessmentId: number) => {
    const response = await api.get(`/assessments/${assessmentId}/cmms/analysis`);
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
