import { createClient } from '@supabase/supabase-js';
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

// Supabase client with retry and error handling
export const supabase = createClient(
  env.data.VITE_SUPABASE_URL,
  env.data.VITE_SUPABASE_ANON_KEY,
  {
    auth: {
      persistSession: true,
      autoRefreshToken: true,
      detectSessionInUrl: true,
    },
    global: {
      headers: { 'x-application-name': 'dana-ai' },
    },
  }
);

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
};