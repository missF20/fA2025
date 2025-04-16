import { useState, useEffect } from 'react';
import { getAuthToken } from '../utils/auth';
import { TokenUsageStats, UserTokenUsage } from '../types';

export const useUsageStats = (userId?: string, isAdmin: boolean = false) => {
  const [stats, setStats] = useState<TokenUsageStats | null>(null);
  const [allUserStats, setAllUserStats] = useState<UserTokenUsage[]>([]);
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

        if (isAdmin) {
          // Fetch usage statistics for all users (admin view)
          const response = await fetch('/api/admin/usage/stats', {
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
          setAllUserStats(data.users || []);
          
          // If a specific user ID is provided, extract that user's stats
          if (userId) {
            const userStats = data.users.find((user: UserTokenUsage) => user.userId === userId);
            if (userStats) {
              setStats(userStats.stats);
            } else {
              setError(`No usage data found for user ID: ${userId}`);
            }
          }
        } else if (userId) {
          // Fetch usage statistics for a specific user
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
        } else {
          setError('User ID is required for non-admin users');
        }
      } catch (err) {
        console.error('Error fetching token usage stats:', err);
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setLoading(false);
      }
    };

    // Only fetch if we're an admin or have a userId
    if (isAdmin || userId) {
      fetchUsageStats();
    } else {
      setLoading(false);
      setError('User ID is required for non-admin users');
    }
  }, [userId, isAdmin]);

  return { stats, allUserStats, loading, error };
};

export default useUsageStats;