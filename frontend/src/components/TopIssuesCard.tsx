import { useContext } from 'react';
import { Card, Table, Badge } from 'react-bootstrap';
import { TopIssue } from '../types';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { getPlatformColor, getPlatformDisplayName } from '../utils/platformUtils';
import { ThemeContext } from '../context/ThemeContext';

interface TopIssuesCardProps {
  issues: TopIssue[];
}

export const TopIssuesCard = ({ issues }: TopIssuesCardProps) => {
  const { isDarkMode } = useContext(ThemeContext);

  const getTrendIcon = (trend: 'up' | 'down' | 'stable') => {
    switch (trend) {
      case 'up':
        return <TrendingUp size={16} color="#dc3545" />;
      case 'down':
        return <TrendingDown size={16} color="#28a745" />;
      case 'stable':
        return <Minus size={16} color="#ffc107" />;
    }
  };

  return (
    <Card className="h-100">
      <Card.Header>
        <h5 className="mb-0">Top Issues</h5>
      </Card.Header>
      <Card.Body className="p-0">
        <Table responsive className="mb-0">
          <thead>
            <tr>
              <th>Topic</th>
              <th>Count</th>
              <th>Trend</th>
              <th>Platforms</th>
            </tr>
          </thead>
          <tbody>
            {issues.length === 0 ? (
              <tr>
                <td colSpan={4} className="text-center">No issues data available</td>
              </tr>
            ) : (
              issues.map((issue, index) => (
                <tr key={index}>
                  <td>{issue.topic}</td>
                  <td>{issue.count}</td>
                  <td>
                    <span className="d-flex align-items-center">
                      {getTrendIcon(issue.trend)}
                    </span>
                  </td>
                  <td>
                    <div className="d-flex gap-1">
                      {issue.platforms.map((platform, i) => (
                        <Badge
                          key={i}
                          bg="secondary"
                          style={{ backgroundColor: getPlatformColor(platform, isDarkMode) }}
                          className="text-white"
                        >
                          {getPlatformDisplayName(platform)}
                        </Badge>
                      ))}
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </Table>
      </Card.Body>
    </Card>
  );
};