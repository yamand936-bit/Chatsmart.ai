import axios from 'axios';

// The baseURL is left empty or set to /api assuming Next.js rewrites or a relative path
// The previous code used absolute relative paths e.g., `/api/merchant/...`
const apiClient = axios.create({
  withCredentials: true,
  // We can add a timeout if needed: timeout: 15000,
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    // Check for 401 Unauthorized or 403 Forbidden globally
    if (error.response && (error.response.status === 401 || error.response.status === 403)) {
      if (typeof window !== 'undefined' && !window.location.pathname.includes('/login')) {
         window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export default apiClient;
