import { create } from 'zustand';
import { supabase, isAllowedEmail, ALLOWED_DOMAIN } from './supabase';
import { authAPI } from './client';

interface User {
  id: number;
  email: string;
  full_name: string;
  role: string;
  is_active: boolean;
}

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  initialized: boolean;

  init: () => Promise<void>;
  login: (email: string, password: string) => Promise<void>;
  signup: (email: string, password: string) => Promise<{ needsConfirmation: boolean }>;
  requestPasswordReset: (email: string) => Promise<void>;
  updatePassword: (newPassword: string) => Promise<void>;
  logout: () => Promise<void>;
  fetchCurrentUser: () => Promise<void>;
  clearError: () => void;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  isAuthenticated: false,
  isLoading: false,
  error: null,
  initialized: false,

  // Called once on app mount: hydrate the Supabase session and keep it in sync.
  init: async () => {
    const { data } = await supabase.auth.getSession();
    set({ isAuthenticated: !!data.session, initialized: true });
    if (data.session) {
      try {
        await get().fetchCurrentUser();
      } catch {
        /* profile fetch can fail (e.g. wrong domain) — handled at call sites */
      }
    }
    supabase.auth.onAuthStateChange((_event, session) => {
      set({ isAuthenticated: !!session });
      if (!session) set({ user: null });
    });
  },

  login: async (email, password) => {
    set({ isLoading: true, error: null });
    const { error } = await supabase.auth.signInWithPassword({ email: email.trim(), password });
    if (error) {
      set({ isLoading: false, error: error.message });
      throw error;
    }
    set({ isAuthenticated: true, isLoading: false });
    await get().fetchCurrentUser();
  },

  signup: async (email, password) => {
    set({ isLoading: true, error: null });
    if (!isAllowedEmail(email)) {
      const msg = `Sign-up is restricted to @${ALLOWED_DOMAIN} email addresses.`;
      set({ isLoading: false, error: msg });
      throw new Error(msg);
    }
    const { data, error } = await supabase.auth.signUp({ email: email.trim(), password });
    if (error) {
      set({ isLoading: false, error: error.message });
      throw error;
    }
    set({ isLoading: false });
    if (data.session) {
      set({ isAuthenticated: true });
      await get().fetchCurrentUser();
      return { needsConfirmation: false };
    }
    return { needsConfirmation: true };
  },

  requestPasswordReset: async (email) => {
    const { error } = await supabase.auth.resetPasswordForEmail(email.trim(), {
      redirectTo: `${window.location.origin}/login`,
    });
    if (error) throw error;
  },

  updatePassword: async (newPassword) => {
    const { error } = await supabase.auth.updateUser({ password: newPassword });
    if (error) throw error;
  },

  logout: async () => {
    await supabase.auth.signOut();
    set({ user: null, isAuthenticated: false, error: null });
  },

  fetchCurrentUser: async () => {
    const user = await authAPI.getCurrentUser();
    set({ user });
  },

  clearError: () => set({ error: null }),
}));
