import { useState, useEffect } from 'react';
import { getAuthToken } from '../utils/auth';

interface TokenLimits {
  limit: number;
  used: number;
  remaining: number;
  exceeded: boolean;
  unlimited: boolean;
}

interface ModelUsage {
  model: string;
  total_tokens: number;
  prompt_tokens: number;
  completion_tokens: number;
  request_count: number;
  first_request: string;
  last_request: string;
}

interface TokenUsage {
  user_id: string;
  period: {
    start: string;
    end: string;
    days: number;
  };
  totals: {
    total_tokens: number;
    prompt_tokens: number;
    completion_tokens: number;
    request_count: number;
  };
  models: ModelUsage[];
  limits: TokenLimits;
}

export const useUsageStats = (userId: string) => {
  const [stats, setStats] = useState<TokenUsage | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchUsageStats = async () => {
      try {
        setLoading(true);
        setError(null);

        // Get the authentication token
        const token = getAuthToken();
        if (!token) {
          throw new Error('No authentication token available');
        }

        // Fetch usage statistics from the API
        const response = await fetch(`/api/usage/stats?user_id=${userId}`, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        });

        if (!response.ok) {
          // Try to get detailed error message from response
          let errorMessage = 'Failed to fetch token usage statistics';
          try {
            const errorData = await response.json();
            errorMessage = errorData.message || errorData.error || errorMessage;
          } catch {
            // If we can't parse the JSON, use the status text
            errorMessage = `${errorMessage}: ${response.status} ${response.statusText}`;
          }
          throw new Error(errorMessage);
        }

        const data = await response.json();
        setStats(data);
      } catch (err) {
        console.error('Error fetching token usage stats:', err);
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setLoading(false);
      }
    };

    if (userId) {
      fetchUsageStats();
    } else {
      setLoading(false);
      setError('User ID is required');
    }
  }, [userId]);

  return { stats, loading, error };
};

export default useUsageStats;