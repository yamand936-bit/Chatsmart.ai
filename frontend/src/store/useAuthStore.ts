import { create } from 'zustand';
import axios from 'axios';
import toast from 'react-hot-toast';

interface User {
  id: string;
  email: string;
  role: 'admin' | 'merchant';
  business_id: string | null;
}

interface AuthState {
  user: User | null;
  isHydrated: boolean;
  login: () => void;
  logout: () => void;
  fetchMe: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isHydrated: false,
  
  login: () => {
    // Cookie is set by backend implicitly
    axios.defaults.withCredentials = true;
  },
  
  logout: async () => {
    try {
      await axios.post(`/api/auth/logout`, {}, { withCredentials: true });
    } catch(err) {
      console.error("Logout failed", err);
    } finally {
      sessionStorage.removeItem('impersonate_token');
      set({ user: null, isHydrated: true });
    }
  },

  fetchMe: async () => {
    try {
      axios.defaults.withCredentials = true;
      const res = await axios.get(`/api/auth/me`, { withCredentials: true });
      set({ user: res.data, isHydrated: true });
    } catch (err) {
      set({ user: null, isHydrated: true });
    }
  }
}));

// GLOBAL INTERCEPTORS
if (typeof window !== "undefined") {
  // Capture impersonate token if present
  const params = new URLSearchParams(window.location.search);
  const impersonateToken = params.get('impersonate_token');
  if (impersonateToken) {
    sessionStorage.setItem('impersonate_token', impersonateToken);
    // Cleanup URL
    window.history.replaceState({}, document.title, window.location.pathname);
  }

  axios.interceptors.request.use((config) => {
    const token = sessionStorage.getItem('impersonate_token');
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || '';
    if (token && (config.url?.startsWith(apiUrl) || config.url?.startsWith('/api'))) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  });

  let isRefreshing = false;
  let refreshSubscribers: any[] = [];

  const onRefreshed = () => {
    refreshSubscribers.map(cb => cb());
  };

  const subscribeTokenRefresh = (cb: any) => {
    refreshSubscribers.push(cb);
  };

  axios.interceptors.response.use(
    (response) => response,
    async (error) => {
      const originalRequest = error.config;
      
      if (error.response?.status === 401 && !originalRequest._retry) {
        if (window.location.pathname !== '/login') {

            if (isRefreshing) {
              return new Promise(resolve => {
                subscribeTokenRefresh(() => {
                  resolve(axios(originalRequest));
                });
              });
            }

            originalRequest._retry = true;
            isRefreshing = true;

            try {
              // Attempt to refresh token silently. Add _retry: true to bypass the interceptor on failure.
              await axios.post(`/api/auth/refresh`, {}, { withCredentials: true, _retry: true } as any);
              isRefreshing = false;
              onRefreshed();
              refreshSubscribers = [];
              return axios(originalRequest);
            } catch (refreshError) {
              isRefreshing = false;
              refreshSubscribers = [];
              sessionStorage.removeItem('impersonate_token');
              useAuthStore.getState().logout();
              window.location.href = '/login';
              return Promise.reject(refreshError);
            }
        }
      }
      
      if (error.response?.status >= 500) {
        toast.error("System error encountered. Our team has been notified.");
      }
      return Promise.reject(error);
    }
  );
}
