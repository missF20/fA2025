import React, { useEffect, useState } from 'react';
import { fetchWithAuth } from '../utils/fetch';
import { Alert, Card, Col, Container, ProgressBar, Row, Table } from 'react-bootstrap';

interface TokenUsage {
  request_tokens: number;
  response_tokens: number;
  total_tokens: number;
  request_count: number;
}

interface UsageStats {
  usage: TokenUsage;
  tier: string;
  limit: number;
  remaining: number;
  percentage_used: number;
  period: string;
}

interface RateLimit {
  current_rate: number;
  limit: number;
  remaining: number;
  tier: string;
}

interface TokenLimit {
  current_usage: number;
  limit: number;
  remaining: number;
  percentage_used: number;
  tier: string;
}

interface UsageLimits {
  token_usage: TokenLimit;
  rate_limit: RateLimit;
}

interface TierLimits {
  token_limits: Record<string, number>;
  rate_limits: Record<string, number>;
}

const UsageStats: React.FC = () => {
  const [usageStats, setUsageStats] = useState<UsageStats | null>(null);
  const [usageLimits, setUsageLimits] = useState<UsageLimits | null>(null);
  const [tierLimits, setTierLimits] = useState<TierLimits | null>(null);
  const [period, setPeriod] = useState<string>('month');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  const fetchUsageStats = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await fetchWithAuth(`/api/usage/tokens?period=${period}`);
      if (!response.ok) {
        throw new Error(`Failed to fetch usage stats: ${response.statusText}`);
      }
      
      const data = await response.json();
      setUsageStats(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
      console.error('Error fetching usage stats:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchUsageLimits = async () => {
    try {
      const response = await fetchWithAuth('/api/usage/limits');
      if (!response.ok) {
        throw new Error(`Failed to fetch usage limits: ${response.statusText}`);
      }
      
      const data = await response.json();
      setUsageLimits(data);
    } catch (err) {
      console.error('Error fetching usage limits:', err);
    }
  };

  const fetchTierLimits = async () => {
    try {
      const response = await fetchWithAuth('/api/usage/tiers');
      if (!response.ok) {
        throw new Error(`Failed to fetch tier limits: ${response.statusText}`);
      }
      
      const data = await response.json();
      setTierLimits(data);
    } catch (err) {
      console.error('Error fetching tier limits:', err);
    }
  };

  useEffect(() => {
    fetchUsageStats();
    fetchUsageLimits();
    fetchTierLimits();
  }, [period]);

  const formatNumber = (num: number): string => {
    return new Intl.NumberFormat().format(num);
  };

  const getProgressVariant = (percentage: number): string => {
    if (percentage < 50) return 'success';
    if (percentage < 80) return 'warning';
    return 'danger';
  };

  const getTierName = (tier: string): string => {
    switch (tier) {
      case 'free':
        return 'Free Tier';
      case 'basic':
        return 'Basic Tier';
      case 'professional':
        return 'Professional Tier';
      case 'enterprise':
        return 'Enterprise Tier';
      default:
        return tier.charAt(0).toUpperCase() + tier.slice(1);
    }
  };

  const periodOptions = [
    { value: 'day', label: 'Today' },
    { value: 'week', label: 'This Week' },
    { value: 'month', label: 'This Month' },
    { value: 'year', label: 'This Year' },
  ];

  return (
    <Container>
      <h2 className="my-4">Usage Statistics</h2>
      
      <Row className="mb-4">
        <Col>
          <div className="d-flex align-items-center">
            <label htmlFor="period-select" className="me-2">View period:</label>
            <select
              id="period-select"
              className="form-select w-auto"
              value={period}
              onChange={(e) => setPeriod(e.target.value)}
            >
              {periodOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
            <button
              className="btn btn-outline-secondary ms-2"
              onClick={fetchUsageStats}
              disabled={loading}
            >
              {loading ? 'Loading...' : 'Refresh'}
            </button>
          </div>
        </Col>
      </Row>

      {error && (
        <Alert variant="danger" className="mb-4">
          {error}
        </Alert>
      )}

      {usageStats && (
        <Row>
          <Col md={6} className="mb-4">
            <Card>
              <Card.Header><strong>Token Usage Summary ({periodOptions.find(op => op.value === period)?.label})</strong></Card.Header>
              <Card.Body>
                <div className="mb-3">
                  <div className="d-flex justify-content-between align-items-center mb-1">
                    <span>Total Usage:</span>
                    <strong>{formatNumber(usageStats.usage.total_tokens)} / {formatNumber(usageStats.limit)} tokens</strong>
                  </div>
                  <ProgressBar
                    variant={getProgressVariant(usageStats.percentage_used)}
                    now={usageStats.percentage_used}
                    label={`${Math.round(usageStats.percentage_used)}%`}
                    className="mb-2"
                  />
                  <div className="small text-muted text-end">
                    {formatNumber(usageStats.remaining)} tokens remaining
                  </div>
                </div>
                
                <div className="mb-3">
                  <strong>Current Plan: {getTierName(usageStats.tier)}</strong>
                </div>
                
                <Table striped bordered hover size="sm">
                  <tbody>
                    <tr>
                      <td>Request Tokens:</td>
                      <td className="text-end">{formatNumber(usageStats.usage.request_tokens)}</td>
                    </tr>
                    <tr>
                      <td>Response Tokens:</td>
                      <td className="text-end">{formatNumber(usageStats.usage.response_tokens)}</td>
                    </tr>
                    <tr>
                      <td>Total Tokens:</td>
                      <td className="text-end">{formatNumber(usageStats.usage.total_tokens)}</td>
                    </tr>
                    <tr>
                      <td>API Requests:</td>
                      <td className="text-end">{formatNumber(usageStats.usage.request_count)}</td>
                    </tr>
                  </tbody>
                </Table>
              </Card.Body>
            </Card>
          </Col>

          {usageLimits && (
            <Col md={6} className="mb-4">
              <Card>
                <Card.Header><strong>Current Limits</strong></Card.Header>
                <Card.Body>
                  <h5>Token Limit</h5>
                  <div className="mb-3">
                    <div className="d-flex justify-content-between align-items-center mb-1">
                      <span>Monthly Usage:</span>
                      <strong>{formatNumber(usageLimits.token_usage.current_usage)} / {formatNumber(usageLimits.token_usage.limit)} tokens</strong>
                    </div>
                    <ProgressBar
                      variant={getProgressVariant(usageLimits.token_usage.percentage_used)}
                      now={usageLimits.token_usage.percentage_used}
                      label={`${Math.round(usageLimits.token_usage.percentage_used)}%`}
                      className="mb-2"
                    />
                  </div>
                  
                  <h5 className="mt-4">Rate Limit</h5>
                  <div className="mb-3">
                    <div className="d-flex justify-content-between align-items-center mb-1">
                      <span>Current Rate:</span>
                      <strong>{usageLimits.rate_limit.current_rate} / {usageLimits.rate_limit.limit} requests per minute</strong>
                    </div>
                    <ProgressBar
                      variant={getProgressVariant((usageLimits.rate_limit.current_rate / usageLimits.rate_limit.limit) * 100)}
                      now={(usageLimits.rate_limit.current_rate / usageLimits.rate_limit.limit) * 100}
                      className="mb-2"
                    />
                  </div>
                </Card.Body>
              </Card>
            </Col>
          )}
        </Row>
      )}

      {tierLimits && (
        <Row className="mb-4">
          <Col>
            <Card>
              <Card.Header><strong>Plan Comparison</strong></Card.Header>
              <Card.Body>
                <Table striped bordered responsive>
                  <thead>
                    <tr>
                      <th>Plan</th>
                      <th className="text-center">Monthly Token Limit</th>
                      <th className="text-center">Requests per Minute</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(tierLimits.token_limits).map(([tier, limit]) => (
                      <tr key={tier}>
                        <td><strong>{getTierName(tier)}</strong></td>
                        <td className="text-center">{formatNumber(limit)}</td>
                        <td className="text-center">{tierLimits.rate_limits[tier]}</td>
                      </tr>
                    ))}
                  </tbody>
                </Table>
                
                <div className="mt-3 text-center">
                  <a href="/subscription" className="btn btn-primary">
                    Upgrade Plan
                  </a>
                </div>
              </Card.Body>
            </Card>
          </Col>
        </Row>
      )}
    </Container>
  );
};

export default UsageStats;