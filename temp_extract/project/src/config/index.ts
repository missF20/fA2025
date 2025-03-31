import { z } from 'zod';

const envSchema = z.object({
  VITE_SUPABASE_URL: z.string().url(),
  VITE_SUPABASE_ANON_KEY: z.string().min(1),
  VITE_SENTRY_DSN: z.string().optional(),
  VITE_SENTRY_ENVIRONMENT: z.enum(['development', 'staging', 'production']).default('development'),
  VITE_API_URL: z.string().url().default('http://localhost:3001'),
  VITE_SOCKET_URL: z.string().url().default('http://localhost:3001'),
});

const env = envSchema.safeParse({
  VITE_SUPABASE_URL: import.meta.env.VITE_SUPABASE_URL,
  VITE_SUPABASE_ANON_KEY: import.meta.env.VITE_SUPABASE_ANON_KEY,
  VITE_SENTRY_DSN: import.meta.env.VITE_SENTRY_DSN,
  VITE_SENTRY_ENVIRONMENT: import.meta.env.VITE_SENTRY_ENVIRONMENT,
  VITE_API_URL: import.meta.env.VITE_API_URL,
  VITE_SOCKET_URL: import.meta.env.VITE_SOCKET_URL,
});

if (!env.success) {
  throw new Error(`Environment validation failed: ${env.error.message}`);
}

export const config = {
  supabase: {
    url: env.data.VITE_SUPABASE_URL,
    anonKey: env.data.VITE_SUPABASE_ANON_KEY,
  },
  sentry: {
    dsn: env.data.VITE_SENTRY_DSN,
    environment: env.data.VITE_SENTRY_ENVIRONMENT,
  },
  api: {
    url: env.data.VITE_API_URL,
    socketUrl: env.data.VITE_SOCKET_URL,
  },
  auth: {
    sessionKey: 'supabase.auth.token',
    refreshInterval: 5 * 60 * 1000, // 5 minutes
  },
  metrics: {
    updateInterval: 30 * 1000, // 30 seconds
  },
  rateLimit: {
    maxRequests: 100,
    windowMs: 15 * 60 * 1000, // 15 minutes
  },
} as const;