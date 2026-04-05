import { create } from 'zustand';
import axios from 'axios';

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
  
  logout: () => {
    set({ user: null, isHydrated: true });
    (async () => {
      try {
        await axios.post(`${process.env.NEXT_PUBLIC_API_URL}/api/auth/logout`, {}, { withCredentials: true });
      } catch(err) {
        console.error("Logout failed", err);
      }
    })();
  },

  fetchMe: async () => {
    try {
      axios.defaults.withCredentials = true;
      const res = await axios.get(`${process.env.NEXT_PUBLIC_API_URL}/api/auth/me`);
      set({ user: res.data, isHydrated: true });
    } catch (err) {
      set({ user: null, isHydrated: true });
    }
  }
}));

// GLOBAL INTERCEPTORS
if (typeof window !== "undefined") {
  axios.interceptors.response.use(
    (response) => response,
    (error) => {
      if (error.response?.status === 401) {
        // Suppress 401 redirect loop if we're naturally fetching auth or already on login
        if (window.location.pathname !== '/login') {
          useAuthStore.getState().logout();
          window.location.href = '/login';
        }
      }
      if (error.response?.status >= 500) {
        alert("System error encountered. Our team has been notified.");
      }
      return Promise.reject(error);
    }
  );
}
