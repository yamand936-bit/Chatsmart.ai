import axios from 'axios';
import { useAuthStore } from '@/store/useAuthStore';
import toast from 'react-hot-toast';

const apiClient = axios.create({
  withCredentials: true,
  baseURL: process.env.NEXT_PUBLIC_API_URL || '',
});

let isRefreshing = false;
let refreshSubscribers: any[] = [];

const onRefreshed = () => {
  refreshSubscribers.map(cb => cb());
};

const subscribeTokenRefresh = (cb: any) => {
  refreshSubscribers.push(cb);
};

apiClient.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = sessionStorage.getItem('impersonate_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    if (error.response?.status === 401 && !originalRequest._retry) {
      if (typeof window !== 'undefined' && window.location.pathname !== '/login') {

          if (isRefreshing) {
            return new Promise(resolve => {
              subscribeTokenRefresh(() => {
                resolve(apiClient(originalRequest));
              });
            });
          }

          originalRequest._retry = true;
          isRefreshing = true;

          try {
            await axios.post(`/api/auth/refresh`, {}, { withCredentials: true, _retry: true } as any);
            isRefreshing = false;
            onRefreshed();
            refreshSubscribers = [];
            return apiClient(originalRequest);
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
    
    // Pass 403 through as it might be intentional
    if (error.response?.status >= 500) {
       toast.error("System error encountered. Our team has been notified.");
    }
    
    return Promise.reject(error);
  }
);

export default apiClient;
