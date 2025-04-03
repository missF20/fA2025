import React, { useEffect, useState } from 'react';
import { Card, ProgressBar, Spinner } from 'react-bootstrap';
import { useUsageStats } from '../hooks/useUsageStats';

type TokenUsageWidgetProps = {
  userId: string;
  showDetailed?: boolean;
};

export const TokenUsageWidget: React.FC<TokenUsageWidgetProps> = ({
  userId,
  showDetailed = false,
}) => {
  const { stats, loading, error } = useUsageStats(userId);

  if (loading) {
    return (
      <Card className="mb-3 shadow-sm">
        <Card.Body className="d-flex justify-content-center align-items-center py-3">
          <Spinner animation="border" role="status" variant="primary" />
          <span className="ms-2">Loading token usage...</span>
        </Card.Body>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="mb-3 shadow-sm border-warning">
        <Card.Body>
          <Card.Title>Token Usage</Card.Title>
          <p className="text-danger">Error loading token usage: {error}</p>
        </Card.Body>
      </Card>
    );
  }

  if (!stats) {
    return (
      <Card className="mb-3 shadow-sm">
        <Card.Body>
          <Card.Title>Token Usage</Card.Title>
          <p>No token usage data available.</p>
        </Card.Body>
      </Card>
    );
  }

  const { limits, totals, models } = stats;
  const { used, limit, remaining, unlimited, exceeded } = limits;
  
  // Calculate percentage used (avoid division by zero)
  const percentageUsed = limit > 0 ? Math.min(100, (used / limit) * 100) : 0;
  
  // Determine progress bar variant based on usage
  let variant = 'success';
  if (percentageUsed > 90) variant = 'danger';
  else if (percentageUsed > 70) variant = 'warning';
  
  return (
    <Card className="mb-3 shadow-sm">
      <Card.Body>
        <Card.Title>Token Usage</Card.Title>
        
        {unlimited ? (
          <div className="mb-3">
            <p className="text-success mb-2">
              <i className="bi bi-infinity me-2"></i>
              Unlimited tokens available
            </p>
            <p className="text-muted small mb-0">
              Used: {totals.total_tokens.toLocaleString()} tokens this month
            </p>
          </div>
        ) : (
          <>
            <div className="d-flex justify-content-between mb-1">
              <span>Monthly Usage</span>
              <span>
                {used.toLocaleString()} / {limit.toLocaleString()} tokens
                ({percentageUsed.toFixed(1)}%)
              </span>
            </div>
            
            <ProgressBar 
              now={percentageUsed} 
              variant={variant} 
              className="mb-2" 
            />
            
            {exceeded ? (
              <p className="text-danger mb-2 small">
                <i className="bi bi-exclamation-triangle-fill me-1"></i>
                Token limit exceeded. Contact support to increase your limit.
              </p>
            ) : (
              <p className="text-muted mb-2 small">
                {remaining.toLocaleString()} tokens remaining this month
              </p>
            )}
          </>
        )}
        
        {showDetailed && models.length > 0 && (
          <div className="mt-3">
            <h6>Model Usage</h6>
            <div className="small">
              {models.map((model, index) => (
                <div key={index} className="mb-2">
                  <div className="d-flex justify-content-between text-muted">
                    <span>{model.model}</span>
                    <span>{model.total_tokens.toLocaleString()} tokens</span>
                  </div>
                  <div className="d-flex justify-content-between text-muted small">
                    <span>Prompt: {model.prompt_tokens.toLocaleString()}</span>
                    <span>Completion: {model.completion_tokens.toLocaleString()}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </Card.Body>
    </Card>
  );
};

export default TokenUsageWidget;