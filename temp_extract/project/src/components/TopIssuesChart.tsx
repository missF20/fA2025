import React from 'react';
import type { TopIssue } from '../types';

interface TopIssuesChartProps {
  issues: TopIssue[];
}

export function TopIssuesChart({ issues }: TopIssuesChartProps) {
  return (
    <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Top Issues</h3>
      <div className="space-y-4">
        {issues.map((issue) => (
          <div key={issue.issue}>
            <div className="flex justify-between text-sm mb-1">
              <span className="text-gray-600">{issue.issue}</span>
              <span className="text-gray-900 font-medium">{issue.count}</span>
            </div>
            <div className="w-full bg-gray-100 rounded-full h-2">
              <div
                className="bg-blue-500 h-2 rounded-full"
                style={{ width: `${issue.percentage}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}