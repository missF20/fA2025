
import { useState, useEffect } from 'react';
import api from '../utils/api';

export const useAnalytics = () => {
  const [analyticsData, setAnalyticsData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchAnalytics = async (dateRange = '30d') => {
    try {
      setLoading(true);
      const response = await api.get(`/api/analytics/data?range=${dateRange}`);
      setAnalyticsData(response.data);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return { analyticsData, loading, error, fetchAnalytics };
};
