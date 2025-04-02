import React, { useState, useEffect } from 'react';
import { fetchWithAuth } from '../utils/fetch';
import { Container, Row, Col, Card, ProgressBar, Alert, Table } from 'react-bootstrap';
import { useAuth } from '../contexts/AuthContext';

interface TokenUsageData {
  limit: number;
  usage: {
    total_tokens: number;
    prompt_tokens: number;
    completion_tokens: number;
  };
  remaining: number;
  percentage_used: number;
}

interface TokenLimitsData {
  response_token_limit: number;
  daily_token_limit: number;
  monthly_token_limit: number;
}

interface SubscriptionTier {
  id: string;
  name: string;
  description: string;
  price: number;
  token_limit: number;
  is_current: boolean;
}

const UsageStats: React.FC = () => {
  const { user, token } = useAuth();
  const [usageData, setUsageData] = useState<TokenUsageData | null>(null);
  const [limitsData, setLimitsData] = useState<TokenLimitsData | null>(null);
  const [subscriptionTiers, setSubscriptionTiers] = useState<SubscriptionTier[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch all necessary data
  useEffect(() => {
    if (!user || !token) return;
    
    setLoading(true);
    setError(null);
    
    // Fetch token usage
    const fetchUsageData = fetchWithAuth('/api/usage/tokens?period=month', token)
      .then(data => setUsageData(data))
      .catch(err => {
        console.error('Error fetching usage data:', err);
        return null;
      });
      
    // Fetch token limits
    const fetchLimitsData = fetchWithAuth('/api/usage/limits', token)
      .then(data => setLimitsData(data))
      .catch(err => {
        console.error('Error fetching limits data:', err);
        return null;
      });
      
    // Fetch subscription tiers
    const fetchTiersData = fetchWithAuth('/api/subscription/tiers', token)
      .then(data => setSubscriptionTiers(data))
      .catch(err => {
        console.error('Error fetching tier data:', err);
        return null;
      });
    
    // Wait for all requests to complete
    Promise.all([fetchUsageData, fetchLimitsData, fetchTiersData])
      .finally(() => setLoading(false));
      
  }, [user, token]);

  // Format numbers with commas
  const formatNumber = (num: number): string => {
    return new Intl.NumberFormat().format(num);
  };

  // Get color for progress bar
  const getProgressVariant = (percentage: number) => {
    if (percentage < 50) return 'success';
    if (percentage < 80) return 'warning';
    return 'danger';
  };

  // Render loading state
  if (loading) {
    return (
      <Container>
        <div className="text-center py-5">
          <div className="spinner-border" role="status">
            <span className="visually-hidden">Loading...</span>
          </div>
          <p className="mt-3">Loading your usage statistics...</p>
        </div>
      </Container>
    );
  }

  // If no data is available, show a message
  const noData = !usageData && !error;
  if (noData) {
    return (
      <Alert variant="info">
        <Alert.Heading>No Usage Data Available</Alert.Heading>
        <p>
          You don't have any AI token usage data yet. Start using the AI features to see your usage statistics here.
        </p>
      </Alert>
    );
  }

  return (
    <Container>
      <h1 className="mb-4">Token Usage Dashboard</h1>
      
      <Row className="mb-4">
        <Col md={6}>
          <Card>
            <Card.Header>Monthly Token Usage</Card.Header>
            <Card.Body>
              {usageData ? (
                <>
                  <h3 className="mb-2">
                    {formatNumber(usageData.usage.total_tokens)} / {formatNumber(usageData.limit)}
                  </h3>
                  
                  <ProgressBar 
                    variant={getProgressVariant(usageData.percentage_used)}
                    now={usageData.percentage_used} 
                    label={`${Math.round(usageData.percentage_used)}%`} 
                    className="mb-3"
                  />
                  
                  <div className="small text-muted mb-3">
                    {formatNumber(usageData.remaining)} tokens remaining this month
                  </div>
                  
                  <Table striped bordered hover size="sm">
                    <thead>
                      <tr>
                        <th>Usage Type</th>
                        <th>Tokens</th>
                        <th>Percentage</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr>
                        <td>Prompt Tokens</td>
                        <td>{formatNumber(usageData.usage.prompt_tokens)}</td>
                        <td>
                          {usageData.usage.total_tokens > 0 
                            ? Math.round((usageData.usage.prompt_tokens / usageData.usage.total_tokens) * 100)
                            : 0}%
                        </td>
                      </tr>
                      <tr>
                        <td>Completion Tokens</td>
                        <td>{formatNumber(usageData.usage.completion_tokens)}</td>
                        <td>
                          {usageData.usage.total_tokens > 0 
                            ? Math.round((usageData.usage.completion_tokens / usageData.usage.total_tokens) * 100)
                            : 0}%
                        </td>
                      </tr>
                    </tbody>
                  </Table>
                </>
              ) : (
                <div className="text-center py-3">
                  <p>No usage data available</p>
                </div>
              )}
            </Card.Body>
          </Card>
        </Col>
        
        <Col md={6}>
          <Card>
            <Card.Header>Current Token Limits</Card.Header>
            <Card.Body>
              {limitsData ? (
                <>
                  <h5>Response Token Limit</h5>
                  <ProgressBar 
                    variant="info"
                    now={limitsData.response_token_limit / 40} // Scaling for visualization
                    label={`${formatNumber(limitsData.response_token_limit)}`}
                    className="mb-3"
                  />
                  <div className="small text-muted mb-4">
                    Maximum tokens per AI response
                  </div>
                  
                  <h5>Daily Token Limit</h5>
                  <ProgressBar 
                    variant="info"
                    now={limitsData.daily_token_limit / 200} // Scaling for visualization
                    label={`${formatNumber(limitsData.daily_token_limit)}`}
                    className="mb-3"
                  />
                  <div className="small text-muted mb-4">
                    Maximum tokens per day
                  </div>
                </>
              ) : (
                <div className="text-center py-3">
                  <p>No limits data available</p>
                </div>
              )}
            </Card.Body>
          </Card>
        </Col>
      </Row>
      
      <Row>
        <Col>
          <Card>
            <Card.Header>Subscription Plan Comparison</Card.Header>
            <Card.Body>
              <Table responsive hover>
                <thead>
                  <tr>
                    <th>Plan</th>
                    <th>Monthly Tokens</th>
                    <th>Price</th>
                    <th>Features</th>
                  </tr>
                </thead>
                <tbody>
                  {subscriptionTiers.length > 0 ? (
                    subscriptionTiers.map(tier => (
                      <tr key={tier.id} className={tier.is_current ? 'table-primary' : ''}>
                        <td>
                          {tier.name}
                          {tier.is_current && <span className="ms-2 badge bg-primary">Current</span>}
                        </td>
                        <td>{formatNumber(tier.token_limit)}</td>
                        <td>${tier.price.toFixed(2)}/mo</td>
                        <td>{tier.description}</td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan={4} className="text-center">No subscription plans available</td>
                    </tr>
                  )}
                </tbody>
              </Table>
            </Card.Body>
          </Card>
        </Col>
      </Row>
    </Container>
  );
};

export default UsageStats;