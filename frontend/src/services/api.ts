import { createClient, SupabaseClient } from '@supabase/supabase-js';
import { z } from 'zod';

// Environment variable validation
const envSchema = z.object({
  VITE_SUPABASE_URL: z.string().url(),
  VITE_SUPABASE_ANON_KEY: z.string().min(1),
});

const env = envSchema.safeParse({
  VITE_SUPABASE_URL: import.meta.env.VITE_SUPABASE_URL,
  VITE_SUPABASE_ANON_KEY: import.meta.env.VITE_SUPABASE_ANON_KEY,
});

if (!env.success) {
  throw new Error(`Environment validation failed: ${env.error.message}`);
}

// Singleton pattern for Supabase client to prevent multiple instances
// This fixes the "Multiple GoTrueClient instances detected" warning
let _supabaseClient: SupabaseClient | null = null;

const createSupabaseClient = (): SupabaseClient => {
  if (_supabaseClient) {
    return _supabaseClient;
  }
  
  console.log('Creating new Supabase client instance');
  
  _supabaseClient = createClient(
    env.data.VITE_SUPABASE_URL,
    env.data.VITE_SUPABASE_ANON_KEY,
    {
      auth: {
        persistSession: true,
        autoRefreshToken: true,
        detectSessionInUrl: true,
        storageKey: 'dana-ai.auth.token', // Consistent storage key
      },
      global: {
        headers: { 'x-application-name': 'dana-ai' },
      },
    }
  );
  
  return _supabaseClient;
};

// Export a singleton instance of the Supabase client
export const supabase = createSupabaseClient();

// Helper function to get the Supabase URL from environment variables
export const getSupabaseUrl = (): string => {
  if (env.success) {
    return env.data.VITE_SUPABASE_URL;
  }
  // Fallback
  return import.meta.env.VITE_SUPABASE_URL || '';
};

// Helper function to generate the correct storage key based on Supabase URL
export const getSupabaseStorageKey = (): string => {
  const supabaseUrl = getSupabaseUrl();
  // Extract the domain without 'https://' and other parts
  const urlDomain = supabaseUrl.replace(/^https?:\/\//, '').split('.')[0];
  
  // Common patterns for Supabase storage keys
  return `sb-${urlDomain}-auth-token`;
};

// Helper function to get an authentication token from multiple possible sources
export const getAuthToken = async (): Promise<string | null> => {
  // Try to get from Supabase auth session first (recommended approach)
  try {
    const { data: session } = await supabase.auth.getSession();
    const token = session?.session?.access_token;
    if (token) {
      console.log("Found token in auth session");
      return token;
    }
  } catch (err) {
    console.warn("Failed to get session from Supabase auth:", err);
  }
  
  // Try to refresh and get new token
  try {
    const { data, error } = await supabase.auth.refreshSession();
    if (!error && data?.session?.access_token) {
      console.log("Found token after refreshing session");
      return data.session.access_token;
    }
  } catch (err) {
    console.warn("Failed to refresh token:", err);
  }
  
  // Fall back to localStorage as a last resort
  try {
    // Check multiple possible storage keys
    const storageKeys = [
      'dana-ai.auth.token',
      'supabase.auth.token',
      getSupabaseStorageKey(),
      // Try any keys that start with sb- (Supabase pattern)
      ...Object.keys(localStorage).filter(key => key.startsWith('sb-'))
    ];
    console.log("Checking localStorage keys:", storageKeys);
    
    // Log all localStorage keys for debugging
    console.log("All localStorage keys:");
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      console.log(`- ${key}`);
    }
    
    // Try each possible storage key
    for (const key of storageKeys) {
      console.log(`Checking localStorage key: ${key}`);
      const storedData = localStorage.getItem(key);
      if (storedData) {
        console.log(`Found data in key: ${key}`);
        try {
          const parsedData = JSON.parse(storedData);
          if (parsedData?.access_token) {
            console.log(`Found access_token in key: ${key}`);
            return parsedData.access_token;
          } else if (parsedData?.data?.session?.access_token) {
            console.log(`Found nested access_token in key: ${key}`);
            return parsedData.data.session.access_token;
          }
        } catch (parseErr) {
          console.error(`Error parsing data from key ${key}:`, parseErr);
        }
      }
    }
  } catch (e) {
    console.error("Error accessing localStorage:", e);
  }
  
  // No token found
  console.error("No authentication token found in any source");
  return null;
};

// Input validation schemas
export const profileSchema = z.object({
  id: z.string().uuid(),
  email: z.string().email(),
  company: z.string().optional(),
  subscription_tier_id: z.string().uuid().optional(),
});

// API service layer
export const api = {
  profiles: {
    async get(userId: string) {
      const { data, error } = await supabase
        .from('profiles')
        .select('*')
        .eq('id', userId)
        .single();

      if (error) throw error;
      return profileSchema.parse(data);
    },

    async update(userId: string, profile: Partial<z.infer<typeof profileSchema>>) {
      const { data, error } = await supabase
        .from('profiles')
        .update(profile)
        .eq('id', userId)
        .select()
        .single();

      if (error) throw error;
      return profileSchema.parse(data);
    },
  },

  subscriptions: {
    async getTiers() {
      const { data, error } = await supabase
        .from('subscription_tiers')
        .select('*')
        .order('price');

      if (error) throw error;
      return data;
    },

    async getUserSubscription(userId: string) {
      const { data, error } = await supabase
        .from('user_subscriptions')
        .select('*, subscription_tiers(*)')
        .eq('user_id', userId)
        .single();

      if (error) throw error;
      return data;
    },
  },

  integrations: {
    async getStatus() {
      // Get authentication token using our centralized helper function
      const token = await getAuthToken();
      
      if (!token) {
        console.warn("No authentication token found");
        return [];
      }

      try {
        const response = await fetch('/api/toggle/integrations/status', {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        });
        
        console.log(`Response status for integrations status: ${response.status}, ${response.statusText}`);

        if (!response.ok) {
          const text = await response.text();
          console.error(`Error response body: ${text}`);
          
          // Handle auth error
          if (response.status === 401) {
            console.error("Authentication failed. Please sign in again.");
            return [];
          }
          
          try {
            // Try to parse as JSON
            const errorData = JSON.parse(text);
            throw new Error(errorData.message || `Failed to fetch integrations: ${response.statusText}`);
          } catch (e) {
            // If it's not valid JSON, return the text
            throw new Error(`Failed to fetch integrations: ${text.substring(0, 100)}`);
          }
        }

        const data = await response.json();
        console.log('Integrations status response:', data);
        // Log each integration status for debugging
        if (data.integrations && Array.isArray(data.integrations)) {
          data.integrations.forEach(integration => {
            console.log(`Integration ${integration.id} status: ${integration.status}`);
          });
        }
        return data.integrations;
      } catch (error) {
        console.error("Error fetching integrations:", error);
        // Return empty array instead of throwing to avoid breaking the UI
        return [];
      }
    },

    // Fetch a CSRF token for secure form submissions
    async getCsrfToken(): Promise<string | null> {
      try {
        const response = await fetch('/api/csrf/token', {
          method: 'GET',
          credentials: 'include'  // Important for cookies
        });
        
        if (!response.ok) {
          console.error(`Failed to get CSRF token: ${response.status} ${response.statusText}`);
          return null;
        }
        
        const data = await response.json();
        return data.csrf_token;
      } catch (error) {
        console.error('Error fetching CSRF token:', error);
        return null;
      }
    },
    
    // Helper method to connect with a provided token
    async _connectWithToken(integrationType: string, config: any, token: string) {
      // Handle special cases for integrations
      let endpoint;
      
      if (integrationType === 'email') {
        endpoint = `/api/v2/integrations/email/connect`;
      } else if (integrationType === 'google_analytics') {
        // Use the direct endpoint for Google Analytics
        endpoint = `/api/integrations/connect/google_analytics`;
      } else {
        // Default endpoint pattern for other integrations
        endpoint = `/api/integrations/connect/${integrationType}`;
      }
      
      console.log(`Connecting to ${integrationType} using endpoint: ${endpoint} with provided token`);
      
      // Prepare the request body based on integration type
      let requestBody: any;
      
      // Get CSRF token for email integration which requires it
      let headers: Record<string, string> = {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      };
      
      // For email integration, we need to add CSRF token
      if (integrationType === 'email') {
        console.log('Email integration config:', config);
        
        // Try to get a CSRF token
        try {
          const csrfToken = await this.getCsrfToken();
          if (csrfToken) {
            // Add token to both headers and as a separate parameter in the body
            headers['X-CSRF-Token'] = csrfToken;
            
            // Create email config with CSRF token as a top-level property
            const emailConfigWithToken = {
              ...config,
              csrf_token: csrfToken
            };
            
            requestBody = JSON.stringify(emailConfigWithToken);
            console.log('Added CSRF token to request:', csrfToken.substring(0, 5) + '...');
          } else {
            // No CSRF token available, proceed without it
            requestBody = JSON.stringify(config);
            console.warn('No CSRF token available for email integration');
          }
        } catch (error) {
          // Fallback if CSRF token fetch fails
          requestBody = JSON.stringify(config);
          console.error('Failed to get CSRF token:', error);
        }
      } else {
        // For other integrations, the backend expects config nested
        requestBody = JSON.stringify({ config });
      }
      
      try {
        const response = await fetch(endpoint, {
          method: 'POST',
          headers,
          body: requestBody,
          credentials: 'include'  // Include cookies for CSRF validation
        });

        console.log(`Response status: ${response.status}, ${response.statusText}`);
        
        if (!response.ok) {
          const errorText = await response.text();
          console.error(`Error response body: ${errorText}`);
          throw new Error(`Failed to connect ${integrationType}: ${response.status} ${response.statusText}`);
        }

        return await response.json();
      } catch (error) {
        console.error(`Error connecting to ${integrationType}:`, error);
        throw error;
      }
    },
    
    async connect(integrationType: string, config: any) {
      // Get authentication token using our centralized helper function
      const token = await getAuthToken();
      
      // If token found, use it to connect
      if (token) {
        return this._connectWithToken(integrationType, config, token);
      }
      
      // No token found after trying all sources
      throw new Error("Authentication required. Please sign in again.");
    },

    // Helper method to disconnect with a provided token
    async _disconnectWithToken(integrationId: string, token: string) {
      // Handle special cases for integrations
      let endpoint;
      
      if (integrationId === 'email') {
        endpoint = `/api/v2/integrations/email/disconnect`;
      } else if (integrationId === 'google_analytics') {
        // Use the direct endpoint for Google Analytics
        endpoint = `/api/integrations/disconnect/google_analytics`;
      } else {
        // Default endpoint pattern for other integrations
        endpoint = `/api/integrations/disconnect/${integrationId}`;
      }
      
      console.log(`Disconnecting from ${integrationId} using endpoint: ${endpoint} with provided token`);

      // Prepare headers and request body
      let headers: Record<string, string> = {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      };
      
      let requestBody: any = {};
      
      // For email integration, we need to add CSRF token
      if (integrationId === 'email') {
        // Try to get a CSRF token
        try {
          const csrfToken = await this.getCsrfToken();
          if (csrfToken) {
            // Add token to both headers and request body
            headers['X-CSRF-Token'] = csrfToken;
            requestBody = { csrf_token: csrfToken };
            console.log('Added CSRF token to disconnect request:', csrfToken.substring(0, 5) + '...');
          }
        } catch (error) {
          console.error('Failed to get CSRF token for disconnect:', error);
        }
      }
      
      try {
        // Add debugging information
        console.log(`Authorization token: Bearer ${token.substring(0, 10)}...`);
        
        const response = await fetch(endpoint, {
          method: 'POST',
          headers,
          // Add empty body to ensure proper request format
          body: JSON.stringify(requestBody),
          credentials: 'include'  // Include cookies for CSRF validation
        });

        console.log(`Response status: ${response.status}, ${response.statusText}`);
        
        if (!response.ok) {
          const errorText = await response.text();
          console.error(`Error response body: ${errorText}`);
          
          if (response.status === 404) {
            // Special handling for 404 errors - the API is working but no integration found
            console.warn(`Integration ${integrationId} not found, but proceeding as if disconnected`);
            return {
              success: true,
              message: `${integrationId} integration disconnected successfully (not found)`
            };
          }
          
          throw new Error(`Failed to disconnect ${integrationId}: ${response.status} ${response.statusText}`);
        }

        return await response.json();
      } catch (error) {
        console.error(`Error disconnecting from ${integrationId}:`, error);
        throw error;
      }
    },
    
    async disconnect(integrationId: string) {
      // Get authentication token using our centralized helper function
      const token = await getAuthToken();
      
      // If token found, use it to disconnect
      if (token) {
        return this._disconnectWithToken(integrationId, token);
      }
      
      // No token found after trying all sources
      throw new Error("Authentication required. Please sign in again.");
    },

    // Helper method to sync with a provided token
    async _syncWithToken(integrationId: string, token: string) {
      // Handle special cases for integrations
      let endpoint;
      
      if (integrationId === 'email') {
        endpoint = `/api/v2/integrations/email/sync`;
      } else if (integrationId === 'google_analytics') {
        // Use the direct endpoint for Google Analytics
        endpoint = `/api/integrations/sync/google_analytics`;
      } else {
        // Default endpoint pattern for other integrations
        endpoint = `/api/integrations/sync/${integrationId}`;
      }
      
      console.log(`Syncing ${integrationId} using endpoint: ${endpoint} with provided token`);

      // Prepare headers and request body
      let headers: Record<string, string> = {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      };
      
      let requestBody: any = {};
      
      // For email integration, we need to add CSRF token
      if (integrationId === 'email') {
        // Try to get a CSRF token
        try {
          const csrfToken = await this.getCsrfToken();
          if (csrfToken) {
            // Add token to both headers and request body
            headers['X-CSRF-Token'] = csrfToken;
            requestBody = { csrf_token: csrfToken };
            console.log('Added CSRF token to sync request:', csrfToken.substring(0, 5) + '...');
          }
        } catch (error) {
          console.error('Failed to get CSRF token for sync:', error);
        }
      }

      try {
        const response = await fetch(endpoint, {
          method: 'POST',
          headers,
          body: JSON.stringify(requestBody),
          credentials: 'include'  // Include cookies for CSRF validation
        });

        console.log(`Response status: ${response.status}, ${response.statusText}`);
        
        if (!response.ok) {
          const errorText = await response.text();
          console.error(`Error response body: ${errorText}`);
          throw new Error(`Failed to sync ${integrationId}: ${response.status} ${response.statusText}`);
        }

        return await response.json();
      } catch (error) {
        console.error(`Error syncing ${integrationId}:`, error);
        throw error;
      }
    },
    
    async sync(integrationId: string) {
      // Get authentication token using our centralized helper function
      const token = await getAuthToken();
      
      // If token found, use it to sync
      if (token) {
        return this._syncWithToken(integrationId, token);
      }
      
      // No token found after trying all sources
      throw new Error("Authentication required. Please sign in again.");
    }
  }
};