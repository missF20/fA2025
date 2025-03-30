// This file provides a shim for the process.env object
// since it's not natively available in the browser

// Define the process interface to avoid TypeScript errors
interface ProcessEnv {
  [key: string]: string | undefined;
}

interface Process {
  env: ProcessEnv;
}

declare global {
  interface Window {
    process: Process;
  }
}

// Create the process object with environment variables
window.process = {
  env: {
    NODE_ENV: import.meta.env.MODE || 'development',
    VITE_SUPABASE_URL: import.meta.env.VITE_SUPABASE_URL as string || '',
    VITE_SUPABASE_KEY: import.meta.env.VITE_SUPABASE_KEY as string || '',
  },
};

export {};