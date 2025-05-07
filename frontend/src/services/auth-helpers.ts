/**
 * Auth helper utilities to standardize auth token access
 */

import { supabase } from './api';

/**
 * Gets the current authentication token
 * @returns Promise that resolves to the auth token or null if not authenticated
 */
export const getAuthToken = async (): Promise<string | null> => {
  try {
    // Get the current session
    const { data: { session } } = await supabase.auth.getSession();
    
    if (!session) {
      console.warn('No active session found');
      return null;
    }
    
    return session.access_token;
  } catch (error) {
    console.error('Error getting auth token:', error);
    return null;
  }
};