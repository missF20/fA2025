import * as Sentry from '@sentry/react';
import { log } from './utils/logger';

// Initialize monitoring
export function initializeMonitoring() {
  if (import.meta.env.VITE_SENTRY_DSN) {
    Sentry.init({
      dsn: import.meta.env.VITE_SENTRY_DSN,
      environment: import.meta.env.VITE_SENTRY_ENVIRONMENT || 'development',
      integrations: [
        new Sentry.BrowserTracing({
          tracePropagationTargets: [
            "localhost",
            /^https:\/\/[^/]*\.supabase\.co/,
          ],
        }),
      ],
      tracesSampleRate: import.meta.env.PROD ? 0.1 : 1.0,
      beforeSend(event) {
        // Log to local logger as well
        log.error('Error captured by Sentry', new Error(event.message || 'Unknown error'));
        return event;
      },
    });
  }

  // Report web vitals
  if ('reportWebVitals' in window) {
    // @ts-ignore
    window.reportWebVitals(metric => {
      log.info('Web Vital', { 
        name: metric.name,
        value: metric.value,
        rating: metric.rating,
      });
    });
  }
}

// Error boundary fallback
export function ErrorFallback({ error }: { error: Error }) {
  // Log error
  log.error('Error boundary caught error', error);
  
  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg shadow-lg p-8 max-w-lg w-full">
        <h2 className="text-2xl font-bold text-red-600 mb-4">Something went wrong</h2>
        <p className="text-gray-600 mb-4">
          We apologize for the inconvenience. Our team has been notified and is working to fix the issue.
        </p>
        <button
          onClick={() => window.location.reload()}
          className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 transition-colors"
        >
          Reload Page
        </button>
      </div>
    </div>
  );
}