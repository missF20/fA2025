/**
 * API fetch utility
 * 
 * This utility provides a consistent interface for making API requests
 * using the native fetch API with proper error handling and authentication.
 */

// Base API URL
const API_BASE_URL = 'http://localhost:5000';

// Default request timeout in milliseconds
const DEFAULT_TIMEOUT = 10000;

/**
 * Creates a Promise that rejects after a specified timeout
 */
const timeoutPromise = (ms: number) => {
  return new Promise((_, reject) => {
    setTimeout(() => {
      reject(new Error(`Request timed out after ${ms}ms`));
    }, ms);
  });
};

/**
 * Common headers used in all requests
 */
const getCommonHeaders = (): HeadersInit => {
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
  };

  // Add authorization token if available
  const token = localStorage.getItem('auth_token');
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  return headers;
};

/**
 * Handle API response
 */
const handleResponse = async <T>(response: Response): Promise<T> => {
  // Handle HTTP errors
  if (!response.ok) {
    // Special handling for 401 authentication errors
    if (response.status === 401) {
      localStorage.removeItem('auth_token');
      window.location.href = '/login';
    }
    
    // Try to get error details from response body
    let errorMessage: string;
    try {
      const errorData = await response.json();
      errorMessage = errorData.message || errorData.error || `HTTP error ${response.status}`;
    } catch {
      errorMessage = `HTTP error ${response.status}`;
    }
    
    throw new Error(errorMessage);
  }
  
  // For successful responses, return the parsed JSON or an empty object if no content
  if (response.status === 204) {
    return {} as T;
  }
  
  return await response.json() as T;
};

/**
 * API methods
 */
export const api = {
  /**
   * Perform a GET request
   */
  get: async <T>(endpoint: string, options: RequestInit = {}): Promise<T> => {
    const url = `${API_BASE_URL}${endpoint}`;
    
    try {
      // Setup request with timeout
      const fetchPromise = fetch(url, {
        method: 'GET',
        headers: getCommonHeaders(),
        ...options,
      });
      
      // Race between fetch and timeout
      const response = await Promise.race([
        fetchPromise,
        timeoutPromise(DEFAULT_TIMEOUT)
      ]) as Response;
      
      return await handleResponse<T>(response);
    } catch (error) {
      console.error(`API GET Error (${endpoint}):`, error);
      throw error;
    }
  },
  
  /**
   * Perform a POST request
   */
  post: async <T>(endpoint: string, data: any, options: RequestInit = {}): Promise<T> => {
    const url = `${API_BASE_URL}${endpoint}`;
    
    try {
      // Setup request with timeout
      const fetchPromise = fetch(url, {
        method: 'POST',
        headers: getCommonHeaders(),
        body: JSON.stringify(data),
        ...options,
      });
      
      // Race between fetch and timeout
      const response = await Promise.race([
        fetchPromise,
        timeoutPromise(DEFAULT_TIMEOUT)
      ]) as Response;
      
      return await handleResponse<T>(response);
    } catch (error) {
      console.error(`API POST Error (${endpoint}):`, error);
      throw error;
    }
  },
  
  /**
   * Perform a PUT request
   */
  put: async <T>(endpoint: string, data: any, options: RequestInit = {}): Promise<T> => {
    const url = `${API_BASE_URL}${endpoint}`;
    
    try {
      // Setup request with timeout
      const fetchPromise = fetch(url, {
        method: 'PUT',
        headers: getCommonHeaders(),
        body: JSON.stringify(data),
        ...options,
      });
      
      // Race between fetch and timeout
      const response = await Promise.race([
        fetchPromise,
        timeoutPromise(DEFAULT_TIMEOUT)
      ]) as Response;
      
      return await handleResponse<T>(response);
    } catch (error) {
      console.error(`API PUT Error (${endpoint}):`, error);
      throw error;
    }
  },
  
  /**
   * Perform a DELETE request
   */
  delete: async <T>(endpoint: string, options: RequestInit = {}): Promise<T> => {
    const url = `${API_BASE_URL}${endpoint}`;
    
    try {
      // Setup request with timeout
      const fetchPromise = fetch(url, {
        method: 'DELETE',
        headers: getCommonHeaders(),
        ...options,
      });
      
      // Race between fetch and timeout
      const response = await Promise.race([
        fetchPromise,
        timeoutPromise(DEFAULT_TIMEOUT)
      ]) as Response;
      
      return await handleResponse<T>(response);
    } catch (error) {
      console.error(`API DELETE Error (${endpoint}):`, error);
      throw error;
    }
  }
};