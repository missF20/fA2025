import axios from 'axios';

// Create a base axios instance for all API calls
const axiosInstance = axios.create({
  baseURL: 'http://localhost:5000', // Backend API URL
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  }
});

// Add response interceptor for common error handling
axiosInstance.interceptors.response.use(
  (response) => response,
  (error) => {
    // Log detailed error information
    console.error('API Error:', error.response?.data || error.message);
    
    // Handle authentication errors
    if (error.response?.status === 401) {
      // Clear token and redirect to login if authentication fails
      localStorage.removeItem('auth_token');
      window.location.href = '/login';
    }
    
    return Promise.reject(error);
  }
);

// Add request interceptor to automatically add auth token
axiosInstance.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

export default axiosInstance;