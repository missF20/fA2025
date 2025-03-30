
import React, { useEffect } from 'react';
import { useAnalytics } from '../hooks/useAnalytics';

export const Analytics = () => {
  const { analyticsData, loading, error, fetchAnalytics } = useAnalytics();

  useEffect(() => {
    fetchAnalytics();
  }, []);

  if (loading) return <div>Loading analytics...</div>;
  if (error) return <div>Error loading analytics: {error}</div>;

  return (
    <div className="p-6">
      <h2 className="text-2xl font-bold mb-4">Analytics Dashboard</h2>
      
      {analyticsData && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div className="bg-white p-4 rounded-lg shadow">
            <h3 className="text-lg font-semibold">Users</h3>
            <div className="mt-2">
              <p>Total: {analyticsData.users?.total || 0}</p>
              <p>Active: {analyticsData.users?.active || 0}</p>
            </div>
          </div>
          
          <div className="bg-white p-4 rounded-lg shadow">
            <h3 className="text-lg font-semibold">Traffic</h3>
            <div className="mt-2">
              <p>Sessions: {analyticsData.traffic?.sessions || 0}</p>
              <p>Page Views: {analyticsData.traffic?.pageViews || 0}</p>
            </div>
          </div>

          <div className="bg-white p-4 rounded-lg shadow">
            <h3 className="text-lg font-semibold">Engagement</h3>
            <div className="mt-2">
              <p>Avg. Session Duration: {analyticsData.engagement?.avgSessionDuration || '0s'}</p>
              <p>Bounce Rate: {analyticsData.engagement?.bounceRate || '0%'}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
