import React from 'react';
import { useUsageStats } from '../hooks/useUsageStats';
import { AlertTriangle, Zap, Activity } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

interface TokenUsageCardProps {
  userId?: string;
  compact?: boolean;
}

export const TokenUsageCard: React.FC<TokenUsageCardProps> = ({ userId, compact = false }) => {
  const { user } = useAuth();
  const effectiveUserId = userId || (user ? user.id : undefined);
  const { stats, loading, error } = useUsageStats(effectiveUserId);

  if (loading) {
    return (
      <div className={`bg-white rounded-lg shadow p-${compact ? '3' : '4'} animate-pulse`}>
        <div className="h-4 bg-gray-200 rounded w-1/4 mb-2"></div>
        <div className="h-8 bg-gray-200 rounded w-3/4 mb-2"></div>
        <div className="h-4 bg-gray-200 rounded w-1/2"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`bg-white rounded-lg shadow p-${compact ? '3' : '4'} border border-red-100`}>
        <div className="flex items-center text-red-500 mb-2">
          <AlertTriangle size={16} className="mr-2" />
          <p className="text-sm font-medium">Error loading usage data</p>
        </div>
        <p className="text-xs text-gray-500">{error}</p>
      </div>
    );
  }

  if (!stats) {
    return (
      <div className={`bg-white rounded-lg shadow p-${compact ? '3' : '4'} border border-gray-100`}>
        <p className="text-sm text-gray-500">No usage data available</p>
      </div>
    );
  }

  const { totals, limits, period } = stats;
  const usagePercentage = limits.unlimited 
    ? 0 
    : Math.min(100, Math.round((limits.used / limits.limit) * 100));
  
  // Create a usage color based on the percentage used
  let usageColor = 'bg-green-500';
  let usageTextColor = 'text-green-600';
  
  if (usagePercentage > 90) {
    usageColor = 'bg-red-500';
    usageTextColor = 'text-red-600';
  } else if (usagePercentage > 75) {
    usageColor = 'bg-orange-500';
    usageTextColor = 'text-orange-600';
  } else if (usagePercentage > 50) {
    usageColor = 'bg-yellow-500';
    usageTextColor = 'text-yellow-600';
  }

  // Calculate dates and usage rates
  const startDate = new Date(period.start);
  const endDate = new Date(period.end);
  const currentDate = new Date();
  const daysUsed = Math.max(1, Math.floor((currentDate.getTime() - startDate.getTime()) / (1000 * 60 * 60 * 24)));
  const daysRemaining = Math.max(0, Math.floor((endDate.getTime() - currentDate.getTime()) / (1000 * 60 * 60 * 24)));
  const dailyUsage = Math.round(totals.total_tokens / daysUsed);
  const projectedUsage = dailyUsage * (daysUsed + daysRemaining);
  
  if (compact) {
    return (
      <div className="bg-white rounded-lg shadow p-3 border border-gray-100">
        <div className="flex justify-between items-center mb-2">
          <div className="flex items-center">
            <Zap size={16} className="text-blue-500 mr-2" />
            <h3 className="text-sm font-medium text-gray-900">Token Usage</h3>
          </div>
          <span className={`text-xs font-medium ${limits.exceeded ? 'text-red-600' : usageTextColor}`}>
            {limits.unlimited ? 'Unlimited' : `${usagePercentage}%`}
          </span>
        </div>
        
        <div className="w-full bg-gray-200 rounded-full h-2 mb-2">
          <div 
            className={`${usageColor} h-2 rounded-full`} 
            style={{ width: `${limits.unlimited ? 100 : usagePercentage}%` }}
          ></div>
        </div>
        
        <div className="flex justify-between items-center text-xs text-gray-500">
          <span>{limits.unlimited ? 'Unlimited' : `${totals.total_tokens.toLocaleString()} / ${limits.limit.toLocaleString()}`}</span>
          <span>{daysRemaining} days left</span>
        </div>
      </div>
    );
  }
  
  return (
    <div className="bg-white rounded-lg shadow p-4 border border-gray-100">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-medium text-gray-900">Token Usage</h3>
        <div className="flex items-center">
          {limits.exceeded ? (
            <span className="px-2 py-1 text-xs font-medium bg-red-100 text-red-700 rounded-full">Limit Exceeded</span>
          ) : limits.unlimited ? (
            <span className="px-2 py-1 text-xs font-medium bg-purple-100 text-purple-700 rounded-full">Unlimited</span>
          ) : (
            <span className={`px-2 py-1 text-xs font-medium bg-${usageColor.replace('bg-', '')}-100 ${usageTextColor} rounded-full`}>
              {usagePercentage}% Used
            </span>
          )}
        </div>
      </div>
      
      <div className="w-full bg-gray-200 rounded-full h-2.5 mb-4">
        <div 
          className={`${usageColor} h-2.5 rounded-full transition-all duration-500`} 
          style={{ width: `${limits.unlimited ? 100 : usagePercentage}%` }}
        ></div>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
        <div>
          <p className="text-sm text-gray-500 mb-1">Current Usage</p>
          <p className="text-xl font-semibold">{totals.total_tokens.toLocaleString()} tokens</p>
          <p className="text-xs text-gray-500 mt-1">{totals.request_count.toLocaleString()} requests</p>
        </div>
        
        <div>
          <p className="text-sm text-gray-500 mb-1">Limit</p>
          <p className="text-xl font-semibold">
            {limits.unlimited 
              ? 'Unlimited' 
              : `${limits.limit.toLocaleString()} tokens`
            }
          </p>
          <p className="text-xs text-gray-500 mt-1">
            {limits.unlimited 
              ? 'No token restrictions' 
              : `${limits.remaining.toLocaleString()} tokens remaining`
            }
          </p>
        </div>
      </div>
      
      <div className="border-t border-gray-100 pt-4">
        <div className="flex items-center mb-3">
          <Activity size={16} className="text-blue-500 mr-2" />
          <h4 className="text-sm font-medium text-gray-900">Usage Analysis</h4>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
          <div className="bg-gray-50 p-2 rounded">
            <p className="text-gray-500 mb-1">Daily Average</p>
            <p className="font-medium">{dailyUsage.toLocaleString()} tokens/day</p>
          </div>
          
          <div className="bg-gray-50 p-2 rounded">
            <p className="text-gray-500 mb-1">Period</p>
            <p className="font-medium">{daysUsed} days used / {daysRemaining} remaining</p>
          </div>
          
          <div className="bg-gray-50 p-2 rounded">
            <p className="text-gray-500 mb-1">Projected Usage</p>
            <p className={`font-medium ${projectedUsage > limits.limit && !limits.unlimited ? 'text-red-600' : ''}`}>
              {projectedUsage.toLocaleString()} tokens
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};