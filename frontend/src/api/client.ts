/**
 * Shared API client: axios instance + offline queue + auth/user-management.
 * Assessment, scoring, report, and CMMS calls live in clientV2.ts.
 */
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
  timeout: 30000,
});

// ────────────────────────────────────────────────────────────────
// Offline queue (kept lightweight; capped retries + size)
// ────────────────────────────────────────────────────────────────
interface QueuedRequest {
  id: string;
  url: string;
  method: string;
  data: unknown;
  timestamp: number;
  attempts: number;
}

const QUEUE_KEY = 'pending_api_requests';
const MAX_QUEUE = 50;
const MAX_ATTEMPTS = 3;

const getQueue = (): QueuedRequest[] => {
  try {
    const raw = localStorage.getItem(QUEUE_KEY);
    return raw ? (JSON.parse(raw) as QueuedRequest[]) : [];
  } catch {
    return [];
  }
};

const writeQueue = (q: QueuedRequest[]) => {
  localStorage.setItem(QUEUE_KEY, JSON.stringify(q.slice(-MAX_QUEUE)));
};

const enqueue = (req: Omit<QueuedRequest, 'id' | 'timestamp' | 'attempts'>) => {
  const q = getQueue();
  q.push({ ...req, id: `${Date.now()}-${Math.random()}`, timestamp: Date.now(), attempts: 0 });
  writeQueue(q);
};

export const syncPendingRequests = async () => {
  const q = getQueue();
  const remaining: QueuedRequest[] = [];
  for (const req of q) {
    try {
      await api.request({ url: req.url, method: req.method, data: req.data });
    } catch {
      req.attempts += 1;
      if (req.attempts < MAX_ATTEMPTS) remaining.push(req);
    }
  }
  writeQueue(remaining);
};

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token');
      // Avoid redirect loops on the login page itself
      if (!window.location.pathname.startsWith('/login')) {
        window.location.href = '/login';
      }
      return Promise.reject(error);
    }

    if (!error.response && error.request && error.code === 'ERR_NETWORK') {
      const original = error.config || {};
      const method = (original.method || '').toLowerCase();
      if (['post', 'put', 'patch'].includes(method)) {
        enqueue({ url: original.url || '', method, data: original.data });
        return Promise.resolve({ data: { queued: true } });
      }
    }

    return Promise.reject(error);
  },
);

export default api;

// ────────────────────────────────────────────────────────────────
// Auth + password reset
// ────────────────────────────────────────────────────────────────

export const authAPI = {
  login: async (username: string, password: string) => {
    const body = new URLSearchParams();
    body.append('username', username);
    body.append('password', password);
    const r = await api.post('/token', body, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });
    return r.data;
  },

  getCurrentUser: async () => {
    const r = await api.get('/users/me');
    return r.data;
  },

  requestPasswordReset: async (email: string) => {
    const r = await api.post('/password-reset/request', { email });
    return r.data as { ok: boolean; debug_token?: string };
  },

  confirmPasswordReset: async (token: string, newPassword: string) => {
    const r = await api.post('/password-reset/confirm', {
      token,
      new_password: newPassword,
    });
    return r.data;
  },
};

// ────────────────────────────────────────────────────────────────
// User management (admin only)
// ────────────────────────────────────────────────────────────────

export interface UserRecord {
  id: number;
  email: string;
  full_name: string;
  role: string;
  is_active: boolean;
}

export const userAPI = {
  list: async (): Promise<UserRecord[]> => (await api.get('/users')).data,
  create: async (data: { email: string; password: string; full_name: string; role: string }) =>
    (await api.post('/register', data)).data,
  update: async (id: number, updates: Partial<UserRecord>) =>
    (await api.patch(`/users/${id}`, updates)).data,
};

// Assessment finalize, report generate/download, and CMMS upload all live in
// clientV2.ts (v2 is the only product surface).
