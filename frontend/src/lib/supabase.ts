import { createClient } from '@supabase/supabase-js';

// Initialize the Supabase client
// Using import.meta.env for Vite instead of process.env
const supabaseUrl = import.meta.env.VITE_SUPABASE_URL as string || '';
const supabaseKey = import.meta.env.VITE_SUPABASE_ANON_KEY as string || '';

// Use default demo values if environment variables are missing - FOR DEVELOPMENT ONLY
// This allows the UI to load without errors, though operations will be mocked
const demoUrl = 'https://example.supabase.co';
const demoKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.demo';

let client;

if (!supabaseUrl || !supabaseKey) {
  console.warn('Missing Supabase URL or API key. Authentication and direct database operations will not work.');
  client = createClient(demoUrl, demoKey);
} else {
  client = createClient(supabaseUrl, supabaseKey);
}

export const supabase = client;