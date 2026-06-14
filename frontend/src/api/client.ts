/**
 * Shared API client: axios instance + offline queue + auth/user-management.
 * Assessment, scoring, report, and CMMS calls live in clientV2.ts.
 */
import axios from 'axios';
import { supabase } from './supabase';

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

api.interceptors.request.use(async (config) => {
  // Attach the current Supabase access token (auto-refreshed by the client).
  const { data } = await supabase.auth.getSession();
  const token = data.session?.access_token;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      void supabase.auth.signOut();
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
  // Auth itself is handled by Supabase (see api/supabase.ts + api/store.ts).
  // This just resolves the app profile/role for the signed-in Supabase user.
  getCurrentUser: async () => {
    const r = await api.get('/users/me');
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
