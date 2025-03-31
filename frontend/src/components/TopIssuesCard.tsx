import { motion } from 'framer-motion';
import { TrendingUp, TrendingDown, BarChart2 } from 'lucide-react';

interface TopIssue {
  id: string;
  name: string;
  count: number;
  trend: number;
  platform?: string;
}

interface TopIssuesCardProps {
  issues: TopIssue[];
}

export function TopIssuesCard({ issues }: TopIssuesCardProps) {
  if (!issues || issues.length === 0) {
    return (
      <div className="bg-white/90 backdrop-blur-sm rounded-xl p-6 shadow-lg border border-gray-100/50">
        <h3 className="text-lg font-bold text-gray-900 mb-3 flex items-center">
          <BarChart2 size={18} className="mr-2 text-amber-500" />
          Common Support Topics
        </h3>
        <div className="text-gray-500 text-sm py-6 text-center">
          No common support topics detected yet
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white/90 backdrop-blur-sm rounded-xl p-6 shadow-lg border border-gray-100/50">
      <h3 className="text-lg font-bold text-gray-900 mb-3 flex items-center">
        <BarChart2 size={18} className="mr-2 text-amber-500" />
        Common Support Topics
      </h3>
      <div className="space-y-3">
        {issues.map((issue) => (
          <motion.div
            key={issue.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            whileHover={{ scale: 1.02 }}
            className="bg-gray-50/80 backdrop-blur-sm p-3 rounded-lg hover:bg-gray-100/80 transition-all"
          >
            <div className="flex justify-between items-start">
              <h4 className="text-sm font-medium text-gray-900">{issue.name}</h4>
              <div className="flex items-center text-xs">
                <span className="bg-amber-100 text-amber-800 px-2 py-0.5 rounded-full">
                  {issue.count} mentions
                </span>
              </div>
            </div>
            
            {issue.platform && (
              <div className="text-xs text-gray-500 mt-1 flex items-center">
                <span className={`px-2 py-0.5 rounded-full mr-1 text-xs ${
                  issue.platform === 'facebook' ? 'bg-blue-100 text-blue-700' : 
                  issue.platform === 'instagram' ? 'bg-pink-100 text-pink-700' : 
                  issue.platform === 'whatsapp' ? 'bg-green-100 text-green-700' : 
                  issue.platform === 'slack' ? 'bg-purple-100 text-purple-700' :
                  issue.platform === 'email' ? 'bg-cyan-100 text-cyan-700' :
                  'bg-gray-100 text-gray-700'
                }`}>
                  {issue.platform}
                </span>
              </div>
            )}
            
            <div className="flex items-center justify-end mt-2">
              <div className={`flex items-center text-xs ${issue.trend > 0 ? 'text-red-500' : 'text-green-500'}`}>
                {issue.trend > 0 ? (
                  <TrendingUp size={12} className="mr-1" />
                ) : (
                  <TrendingDown size={12} className="mr-1" />
                )}
                <span>{Math.abs(issue.trend)}% {issue.trend > 0 ? 'increase' : 'decrease'}</span>
              </div>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
}