import { create } from 'zustand';
import { authAPI } from '../api/client';

interface User {
  id: number;
  email: string;
  full_name: string;
  role: string;
  is_active: boolean;
}

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  fetchCurrentUser: () => Promise<void>;
  clearError: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: localStorage.getItem('access_token'),
  isAuthenticated: !!localStorage.getItem('access_token'),
  isLoading: false,
  error: null,
  
  login: async (username: string, password: string) => {
    set({ isLoading: true, error: null });
    try {
      const data = await authAPI.login(username, password);
      localStorage.setItem('access_token', data.access_token);
      set({ token: data.access_token, isAuthenticated: true, isLoading: false });
      
      // Fetch user data
      const user = await authAPI.getCurrentUser();
      set({ user });
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || 'Login failed';
      set({ error: errorMessage, isLoading: false, isAuthenticated: false });
      throw error;
    }
  },
  
  logout: () => {
    localStorage.removeItem('access_token');
    set({ user: null, token: null, isAuthenticated: false, error: null });
  },
  
  fetchCurrentUser: async () => {
    if (!localStorage.getItem('access_token')) return;
    
    set({ isLoading: true });
    try {
      const user = await authAPI.getCurrentUser();
      set({ user, isLoading: false });
    } catch (error) {
      set({ isLoading: false });
      localStorage.removeItem('access_token');
      set({ isAuthenticated: false, user: null });
    }
  },
  
  clearError: () => set({ error: null }),
}));
