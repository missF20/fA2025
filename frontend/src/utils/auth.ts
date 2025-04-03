/**
 * Authentication utilities for the frontend
 */

// Name of the authentication token in localStorage
const TOKEN_KEY = 'dana_auth_token';

/**
 * Get the authentication token from localStorage
 * 
 * @returns The authentication token or null if not found
 */
export const getAuthToken = (): string | null => {
  return localStorage.getItem(TOKEN_KEY);
};

/**
 * Set the authentication token in localStorage
 * 
 * @param token The authentication token to store
 */
export const setAuthToken = (token: string): void => {
  localStorage.setItem(TOKEN_KEY, token);
};

/**
 * Remove the authentication token from localStorage
 */
export const removeAuthToken = (): void => {
  localStorage.removeItem(TOKEN_KEY);
};

/**
 * Check if the user is authenticated (has a token)
 * 
 * @returns True if authenticated, false otherwise
 */
export const isAuthenticated = (): boolean => {
  return getAuthToken() !== null;
};

/**
 * Parse the JWT token to get the payload
 * 
 * @param token The JWT token to parse
 * @returns The decoded payload or null if invalid
 */
export const parseToken = (token: string): any | null => {
  try {
    const base64Url = token.split('.')[1];
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split('')
        .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
        .join('')
    );
    return JSON.parse(jsonPayload);
  } catch (error) {
    console.error('Error parsing token:', error);
    return null;
  }
};

/**
 * Get the current user info from the stored token
 * 
 * @returns User info object or null if not authenticated
 */
export const getCurrentUser = (): any | null => {
  const token = getAuthToken();
  if (!token) return null;
  return parseToken(token);
};

/**
 * Get the user ID from the stored token
 * 
 * @returns User ID string or null if not authenticated
 */
export const getUserId = (): string | null => {
  const user = getCurrentUser();
  return user ? user.sub || user.user_id : null;
};