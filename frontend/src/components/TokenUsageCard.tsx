import React from 'react';
import { Card, ProgressBar, Button } from 'react-bootstrap';
import { Link } from 'react-router-dom';
import { useUsageStats } from '../hooks/useUsageStats';
import { getUserId } from '../utils/auth';

/**
 * TokenUsageCard component displays the user's token usage in a card format
 * This is a simplified version of TokenUsageWidget for dashboard display
 */
export const TokenUsageCard: React.FC = () => {
  const userId = getUserId() || '';
  const { stats, loading, error } = useUsageStats(userId);

  // Loading state
  if (loading || !userId) {
    return (
      <Card className="h-100 shadow-sm">
        <Card.Body className="d-flex align-items-center justify-content-center">
          <div className="text-center p-4">
            <div className="spinner-border text-primary mb-3" role="status">
              <span className="visually-hidden">Loading...</span>
            </div>
            <p className="mb-0">Loading token usage...</p>
          </div>
        </Card.Body>
      </Card>
    );
  }

  // Error state
  if (error) {
    return (
      <Card className="h-100 shadow-sm">
        <Card.Body>
          <Card.Title>Token Usage</Card.Title>
          <p className="text-danger mb-4">
            <i className="bi bi-exclamation-circle me-2"></i>
            Unable to load token usage information
          </p>
          <Button variant="outline-secondary" size="sm" as={Link} to="/usage">
            Retry Loading
          </Button>
        </Card.Body>
      </Card>
    );
  }

  // No data state
  if (!stats) {
    return (
      <Card className="h-100 shadow-sm">
        <Card.Body>
          <Card.Title>Token Usage</Card.Title>
          <p className="mb-4">No token usage data available.</p>
          <Button variant="outline-primary" size="sm" as={Link} to="/usage">
            View Details
          </Button>
        </Card.Body>
      </Card>
    );
  }

  const { limits, totals } = stats;
  const { used, limit, remaining, unlimited, exceeded } = limits;
  
  // Calculate percentage used (avoid division by zero)
  const percentageUsed = limit > 0 ? Math.min(100, (used / limit) * 100) : 0;
  
  // Determine progress bar variant based on usage
  let variant = 'success';
  if (percentageUsed > 90) variant = 'danger';
  else if (percentageUsed > 70) variant = 'warning';
  
  return (
    <Card className="h-100 shadow-sm">
      <Card.Body>
        <Card.Title className="d-flex justify-content-between align-items-center mb-3">
          <span>Token Usage</span>
          <Button 
            variant="link" 
            className="p-0 text-decoration-none" 
            as={Link} 
            to="/usage"
          >
            View Details
          </Button>
        </Card.Title>
        
        {unlimited ? (
          <div className="mb-3">
            <div className="d-flex align-items-center mb-2">
              <i className="bi bi-infinity me-2 text-success fs-4"></i>
              <span className="text-success fw-bold">Unlimited Plan</span>
            </div>
            <p className="text-muted small mb-0">
              Used: {totals.total_tokens.toLocaleString()} tokens this month
            </p>
          </div>
        ) : (
          <>
            <div className="d-flex justify-content-between mb-1">
              <span>Monthly Usage</span>
              <span className={exceeded ? 'text-danger' : ''}>
                {used.toLocaleString()} / {limit.toLocaleString()}
              </span>
            </div>
            
            <ProgressBar 
              now={percentageUsed} 
              variant={variant} 
              className="mb-2" 
            />
            
            <div className="d-flex justify-content-between small text-muted mb-3">
              <span>{percentageUsed.toFixed(1)}% used</span>
              <span>{remaining.toLocaleString()} remaining</span>
            </div>
            
            {exceeded && (
              <div className="alert alert-danger py-2 small">
                <i className="bi bi-exclamation-triangle-fill me-1"></i>
                Token limit exceeded. Contact support to increase your limit.
              </div>
            )}
          </>
        )}
        
        <div className="d-flex justify-content-between mt-2 border-top pt-2 small text-muted">
          <span>Conversation tokens:</span>
          <span>{totals.total_tokens.toLocaleString()}</span>
        </div>
        <div className="d-flex justify-content-between small text-muted">
          <span>AI requests:</span>
          <span>{totals.request_count.toLocaleString()}</span>
        </div>
      </Card.Body>
    </Card>
  );
};

export default TokenUsageCard;