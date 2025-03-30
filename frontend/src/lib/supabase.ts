import { createClient } from '@supabase/supabase-js';

// Initialize the Supabase client
let client;

// Fetch config from the backend API
async function initializeSupabase() {
  try {
    // First try to load from env variables
    let supabaseUrl = import.meta.env.VITE_SUPABASE_URL as string || '';
    let supabaseKey = import.meta.env.VITE_SUPABASE_KEY as string || '';
    
    // If env variables aren't available, fetch from backend
    if (!supabaseUrl || !supabaseKey || supabaseUrl === 'https://example.supabase.co') {
      console.log('Fetching Supabase credentials from backend API...');
      const response = await fetch('/api/config');
      if (!response.ok) {
        throw new Error(`Failed to fetch config: ${response.status}`);
      }
      const config = await response.json();
      supabaseUrl = config.supabase_url;
      supabaseKey = config.supabase_key;
    }
    
    // Create the client with valid credentials
    if (supabaseUrl && supabaseKey) {
      return createClient(supabaseUrl, supabaseKey);
    } else {
      throw new Error('Missing Supabase credentials from both frontend and backend');
    }
  } catch (error) {
    console.error('Error initializing Supabase client:', error);
    // Use demo client as fallback
    return createClient(
      'https://example.supabase.co',
      'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.demo'
    );
  }
}

// Create an initial client with demo values (will be replaced)
client = createClient(
  'https://example.supabase.co',
  'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.demo'
);

// Replace client asynchronously
initializeSupabase().then(initializedClient => {
  client = initializedClient;
  console.log('Supabase client initialized successfully');
}).catch(error => {
  console.error('Failed to initialize Supabase client:', error);
});

export const supabase = client;