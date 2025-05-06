// CSRF Token Management
// This module handles retrieving and managing CSRF tokens for secure form submissions

/**
 * Fetches a CSRF token from the server
 * @returns Promise that resolves to the CSRF token string
 */
export const getCsrfToken = async (): Promise<string> => {
  try {
    // Try the V2 endpoint first (more reliable)
    try {
      console.log('Fetching CSRF token from V2 endpoint');
      const response = await fetch('/api/v2/csrf-token', {
        method: 'GET',
        credentials: 'include',  // Important for sending cookies
      });
      
      if (response.ok) {
        const data = await response.json();
        console.log('Successfully retrieved CSRF token from V2 endpoint');
        return data.csrf_token;
      }
      
      console.log('V2 endpoint failed, falling back to legacy endpoint');
    } catch (v2Error) {
      console.warn('Error with V2 CSRF endpoint, falling back:', v2Error);
    }
    
    // Fallback to legacy endpoint
    const response = await fetch('/api/csrf/token', {
      method: 'GET',
      credentials: 'include',  // Important for sending cookies
    });
    
    if (!response.ok) {
      throw new Error(`Failed to get CSRF token: ${response.status} ${response.statusText}`);
    }
    
    const data = await response.json();
    console.log('Successfully retrieved CSRF token from legacy endpoint');
    return data.csrf_token;
  } catch (error) {
    console.error('Error fetching CSRF token from all endpoints:', error);
    
    // In development, return a fixed token as last resort to help with testing
    if (window.location.hostname === 'localhost' || 
        window.location.hostname.includes('replit') || 
        window.location.hostname.includes('127.0.0.1')) {
      console.warn('Returning development token as last resort');
      return 'development_csrf_token_for_testing';
    }
    
    throw error;
  }
};

/**
 * Gets a CSRF token from the cookie if available
 * @returns CSRF token from cookie or null if not found
 */
export const getCsrfTokenFromCookie = (): string | null => {
  const cookies = document.cookie.split(';');
  for (const cookie of cookies) {
    const [name, value] = cookie.trim().split('=');
    if (name === 'csrf_token') {
      return decodeURIComponent(value);
    }
  }
  return null;
};

/**
 * Gets a CSRF token using the most reliable method available
 * Will try cookie first, then API endpoint if needed
 * @returns Promise that resolves to the CSRF token string
 */
export const getOrFetchCsrfToken = async (): Promise<string> => {
  // Try to get from cookie first (faster)
  const cookieToken = getCsrfTokenFromCookie();
  if (cookieToken) {
    return cookieToken;
  }
  
  // Fall back to API request
  return getCsrfToken();
};