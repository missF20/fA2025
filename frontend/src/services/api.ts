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
      // Ensure we have a fresh token by refreshing the session
      try {
        await supabase.auth.refreshSession();
      } catch (err) {
        console.warn("Failed to refresh token:", err);
      }
      
      const { data: session } = await supabase.auth.getSession();
      const token = session.session?.access_token;
      
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
            // Try to sign in again if possible
            const refreshResult = await supabase.auth.refreshSession();
            if (refreshResult.error) {
              console.error("Authentication failed. Please sign in again.");
              return [];
            }
            // Retry with new token
            return this.getStatus();
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

    // Helper method to connect with a provided token
    async _connectWithToken(integrationType: string, config: any, token: string) {
      // Handle special case for email integration
      const endpoint = integrationType === 'email' 
        ? `/api/integrations/email/connect`
        : `/api/integrations/connect/${integrationType}`;
      
      console.log(`Connecting to ${integrationType} using endpoint: ${endpoint} with provided token`);
      
      // Prepare the request body based on integration type
      let requestBody;
      
      // For email, the backend expects direct parameters, not nested in config
      if (integrationType === 'email') {
        console.log('Email integration config:', config);
        requestBody = JSON.stringify(config);
      } else {
        // For other integrations, the backend expects config nested
        requestBody = JSON.stringify({ config });
      }
      
      try {
        const response = await fetch(endpoint, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: requestBody
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
      // Ensure we have a fresh token by refreshing the session
      try {
        const { data, error } = await supabase.auth.refreshSession();
        if (error) {
          console.error("Failed to refresh token:", error);
        }
      } catch (err) {
        console.warn("Failed to refresh token:", err);
      }
      
      const { data: session } = await supabase.auth.getSession();
      const token = session?.session?.access_token;
      
      console.log("Authentication token available:", !!token);
      
      if (!token) {
        // Try to get the session directly from localStorage as a fallback
        try {
          const storedSession = localStorage.getItem('dana-ai.auth.token');
          if (storedSession) {
            const parsedSession = JSON.parse(storedSession);
            if (parsedSession?.access_token) {
              console.log("Using token from localStorage");
              return this._connectWithToken(integrationType, config, parsedSession.access_token);
            }
          }
        } catch (e) {
          console.error("Error parsing stored session:", e);
        }
        
        throw new Error("Authentication required. Please sign in again.");
      }

      // Handle special case for email integration
      const endpoint = integrationType === 'email' 
        ? `/api/integrations/email/connect`
        : `/api/integrations/connect/${integrationType}`;
      
      console.log(`Connecting to ${integrationType} using endpoint: ${endpoint}`);
      
      // Prepare the request body based on integration type
      let requestBody;
      
      // For email, the backend expects direct parameters, not nested in config
      if (integrationType === 'email') {
        // Log the config for debugging
        console.log('Email integration config:', config);
        
        requestBody = JSON.stringify(config);
      } else {
        // For other integrations, the backend expects config nested
        requestBody = JSON.stringify({ config });
      }
      
      try {
        const response = await fetch(endpoint, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: requestBody
        });

        console.log(`Response status: ${response.status}, ${response.statusText}`);
        
        if (!response.ok) {
          const errorText = await response.text();
          console.error(`Error response body: ${errorText}`);
          
          // Handle auth error
          if (response.status === 401) {
            // Try to sign in again if possible
            const refreshResult = await supabase.auth.refreshSession();
            if (refreshResult.error) {
              throw new Error("Authentication failed. Please sign in again.");
            }
            // Retry with new token
            return this.connect(integrationType, config);
          }
          
          throw new Error(`Failed to connect ${integrationType}: ${response.status} ${response.statusText}`);
        }

        return await response.json();
      } catch (error) {
        console.error(`Error connecting to ${integrationType}:`, error);
        throw error;
      }
    },

    // Helper method to disconnect with a provided token
    async _disconnectWithToken(integrationId: string, token: string) {
      // Handle special case for email integration
      const endpoint = integrationId === 'email' 
        ? `/api/integrations/email/disconnect`  // Use standard endpoint
        : `/api/integrations/disconnect/${integrationId}`;
      
      console.log(`Disconnecting from ${integrationId} using endpoint: ${endpoint} with provided token`);

      try {
        // Add debugging information
        console.log(`Authorization token: Bearer ${token.substring(0, 10)}...`);
        
        const response = await fetch(endpoint, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          // Add empty body to ensure proper request format
          body: JSON.stringify({})
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
      // Ensure we have a fresh token by refreshing the session
      try {
        const { data, error } = await supabase.auth.refreshSession();
        if (error) {
          console.error("Failed to refresh token:", error);
        }
      } catch (err) {
        console.warn("Failed to refresh token:", err);
      }
      
      const { data: session } = await supabase.auth.getSession();
      const token = session?.session?.access_token;
      
      console.log("Authentication token available:", !!token);
      
      if (!token) {
        // Try to get the session directly from localStorage as a fallback
        try {
          const storedSession = localStorage.getItem('dana-ai.auth.token');
          if (storedSession) {
            const parsedSession = JSON.parse(storedSession);
            if (parsedSession?.access_token) {
              console.log("Using token from localStorage");
              return this._disconnectWithToken(integrationId, parsedSession.access_token);
            }
          }
        } catch (e) {
          console.error("Error parsing stored session:", e);
        }
        
        throw new Error("Authentication required. Please sign in again.");
      }

      // Handle special case for email integration
      const endpoint = integrationId === 'email' 
        ? `/api/integrations/email/disconnect`  // Use standard endpoint
        : `/api/integrations/disconnect/${integrationId}`;
      
      console.log(`Disconnecting from ${integrationId} using endpoint: ${endpoint}`);

      try {
        // Add debugging information
        console.log(`Authorization token: Bearer ${token.substring(0, 10)}...`);
        
        const response = await fetch(endpoint, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          // Add empty body to ensure proper request format
          body: JSON.stringify({})
        });

        console.log(`Response status: ${response.status}, ${response.statusText}`);
        
        if (!response.ok) {
          const errorText = await response.text();
          console.error(`Error response body: ${errorText}`);
          
          // Handle auth error
          if (response.status === 401) {
            // Try to sign in again if possible
            const refreshResult = await supabase.auth.refreshSession();
            if (refreshResult.error) {
              throw new Error("Authentication failed. Please sign in again.");
            }
            // Retry with new token
            return this.disconnect(integrationId);
          }
          
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

    // Helper method to sync with a provided token
    async _syncWithToken(integrationId: string, token: string) {
      // Handle special case for email integration
      const endpoint = integrationId === 'email' 
        ? `/api/integrations/email/sync`
        : `/api/integrations/sync/${integrationId}`;
      
      console.log(`Syncing ${integrationId} using endpoint: ${endpoint} with provided token`);

      try {
        const response = await fetch(endpoint, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
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
      // Ensure we have a fresh token by refreshing the session
      try {
        const { data, error } = await supabase.auth.refreshSession();
        if (error) {
          console.error("Failed to refresh token:", error);
        }
      } catch (err) {
        console.warn("Failed to refresh token:", err);
      }
      
      const { data: session } = await supabase.auth.getSession();
      const token = session?.session?.access_token;
      
      console.log("Authentication token available:", !!token);
      
      if (!token) {
        // Try to get the session directly from localStorage as a fallback
        try {
          const storedSession = localStorage.getItem('dana-ai.auth.token');
          if (storedSession) {
            const parsedSession = JSON.parse(storedSession);
            if (parsedSession?.access_token) {
              console.log("Using token from localStorage");
              return this._syncWithToken(integrationId, parsedSession.access_token);
            }
          }
        } catch (e) {
          console.error("Error parsing stored session:", e);
        }
        
        throw new Error("Authentication required. Please sign in again.");
      }

      // Handle special case for email integration
      const endpoint = integrationId === 'email' 
        ? `/api/integrations/email/sync`
        : `/api/integrations/sync/${integrationId}`;
      
      console.log(`Syncing ${integrationId} using endpoint: ${endpoint}`);

      try {
        const response = await fetch(endpoint, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        });

        console.log(`Response status: ${response.status}, ${response.statusText}`);
        
        if (!response.ok) {
          const errorText = await response.text();
          console.error(`Error response body: ${errorText}`);
          
          // Handle auth error
          if (response.status === 401) {
            // Try to sign in again if possible
            const refreshResult = await supabase.auth.refreshSession();
            if (refreshResult.error) {
              throw new Error("Authentication failed. Please sign in again.");
            }
            // Retry with new token
            return this.sync(integrationId);
          }
          
          throw new Error(`Failed to sync ${integrationId}: ${response.status} ${response.statusText}`);
        }

        return await response.json();
      } catch (error) {
        console.error(`Error syncing ${integrationId}:`, error);
        throw error;
      }
    }
  }
};