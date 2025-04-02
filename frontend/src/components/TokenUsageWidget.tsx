import React, { useState, useEffect } from 'react';
import { Card, Button, ProgressBar, Modal, Form, OverlayTrigger, Tooltip } from 'react-bootstrap';
import { FaCog, FaInfoCircle } from 'react-icons/fa';
import { useAuth } from '../contexts/AuthContext';
import axios from 'axios';

interface TokenUsageData {
  limit: number;
  used: number;
  remaining: number;
  percentage: number;
}

interface TokenLimits {
  responseLimit: number;
  dailyLimit: number;
  monthlyLimit: number;
}

const DEFAULT_TOKEN_USAGE: TokenUsageData = {
  limit: 50000,
  used: 0,
  remaining: 50000,
  percentage: 0
};

const DEFAULT_TOKEN_LIMITS: TokenLimits = {
  responseLimit: 1000,
  dailyLimit: 10000,
  monthlyLimit: 50000
};

/**
 * Token Usage Widget Component
 * 
 * Displays the current token usage with a progress bar and settings modal
 */
const TokenUsageWidget: React.FC = () => {
  const { user, token } = useAuth();
  const [tokenUsage, setTokenUsage] = useState<TokenUsageData>(DEFAULT_TOKEN_USAGE);
  const [tokenLimits, setTokenLimits] = useState<TokenLimits>(DEFAULT_TOKEN_LIMITS);
  const [showSettings, setShowSettings] = useState(false);
  const [responseLimit, setResponseLimit] = useState(1000);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  useEffect(() => {
    if (user && token) {
      fetchUsageData();
    }
  }, [user, token]);
  
  const fetchUsageData = async () => {
    if (!token) return;
    
    setLoading(true);
    setError(null);
    
    try {
      // Fetch token usage
      const response = await axios.get('/api/usage/tokens?period=month', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      setTokenUsage({
        limit: response.data.limit || DEFAULT_TOKEN_USAGE.limit,
        used: response.data.usage?.total_tokens || 0,
        remaining: response.data.remaining || DEFAULT_TOKEN_USAGE.limit,
        percentage: response.data.percentage_used || 0
      });
      
      // Fetch token limits
      const limitsResponse = await axios.get('/api/usage/limits', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      setTokenLimits({
        responseLimit: limitsResponse.data.response_token_limit || DEFAULT_TOKEN_LIMITS.responseLimit,
        dailyLimit: limitsResponse.data.daily_token_limit || DEFAULT_TOKEN_LIMITS.dailyLimit,
        monthlyLimit: limitsResponse.data.monthly_token_limit || DEFAULT_TOKEN_LIMITS.monthlyLimit
      });
      
      setResponseLimit(limitsResponse.data.response_token_limit || DEFAULT_TOKEN_LIMITS.responseLimit);
      
    } catch (err) {
      console.error('Error fetching token usage data:', err);
      setError('Failed to load token usage data');
    } finally {
      setLoading(false);
    }
  };
  
  const updateResponseLimit = async () => {
    if (!token) return;
    
    try {
      await axios.post('/api/usage/limits/response', 
        { limit: responseLimit },
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }
      );
      
      setTokenLimits(prev => ({
        ...prev,
        responseLimit
      }));
      
      setShowSettings(false);
      
      // Save to local storage as well for persistence
      localStorage.setItem('responseTokenLimit', responseLimit.toString());
      
    } catch (err) {
      console.error('Error updating response token limit:', err);
      setError('Failed to update response token limit');
    }
  };
  
  // Determine progress bar variant based on usage
  const getProgressVariant = (percentage: number) => {
    if (percentage > 90) return 'danger';
    if (percentage > 70) return 'warning';
    return 'success';
  };
  
  // Format large numbers with commas
  const formatNumber = (num: number) => {
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
  };
  
  return (
    <div className="token-usage-widget">
      <Card className="shadow-sm">
        <Card.Body>
          <div className="d-flex justify-content-between align-items-center mb-2">
            <h6 className="mb-0">Token Usage</h6>
            <Button 
              variant="link" 
              size="sm" 
              className="p-0 text-muted" 
              onClick={() => setShowSettings(true)}
              aria-label="Token settings"
            >
              <FaCog />
            </Button>
          </div>
          
          <div className="mb-2">
            <div className="d-flex justify-content-between mb-1">
              <div>
                <small>{formatNumber(tokenUsage.used)} / {formatNumber(tokenUsage.limit)}</small>
              </div>
              <div>
                <small>{tokenUsage.percentage.toFixed(1)}%</small>
              </div>
            </div>
            <ProgressBar 
              variant={getProgressVariant(tokenUsage.percentage)}
              now={tokenUsage.percentage} 
              min={0}
              max={100}
              style={{ height: '0.5rem' }}
            />
          </div>
          
          <div className="d-flex justify-content-between align-items-center">
            <small>
              Remaining: {formatNumber(tokenUsage.remaining)}
            </small>
            <OverlayTrigger
              placement="left"
              overlay={
                <Tooltip id="token-usage-tooltip">
                  Response Limit: {formatNumber(tokenLimits.responseLimit)} tokens
                </Tooltip>
              }
            >
              <small className="text-muted">
                <FaInfoCircle />
              </small>
            </OverlayTrigger>
          </div>
        </Card.Body>
      </Card>
      
      {/* Settings Modal */}
      <Modal show={showSettings} onHide={() => setShowSettings(false)}>
        <Modal.Header closeButton>
          <Modal.Title>Token Settings</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <p>Adjust your token usage settings to optimize AI responses.</p>
          
          <Form>
            <Form.Group className="mb-3">
              <Form.Label>Response Token Limit</Form.Label>
              <Form.Select 
                value={responseLimit}
                onChange={(e) => setResponseLimit(parseInt(e.target.value))}
              >
                <option value="500">500 tokens - Very concise responses</option>
                <option value="1000">1000 tokens - Standard responses</option>
                <option value="2000">2000 tokens - Detailed responses</option>
                <option value="4000">4000 tokens - Comprehensive responses</option>
                <option value="8000">8000 tokens - Maximum detail (high token usage)</option>
              </Form.Select>
              <Form.Text className="text-muted">
                Controls the maximum size of AI responses. Higher limits allow for more detailed 
                responses but consume more tokens from your quota.
              </Form.Text>
            </Form.Group>
            
            <div className="mb-3">
              <h6>Current Limits</h6>
              <ul>
                <li>Response Limit: {formatNumber(tokenLimits.responseLimit)} tokens</li>
                <li>Daily Limit: {formatNumber(tokenLimits.dailyLimit)} tokens</li>
                <li>Monthly Limit: {formatNumber(tokenLimits.monthlyLimit)} tokens</li>
              </ul>
              <small className="text-muted">
                To increase your monthly token limits, please upgrade your subscription.
              </small>
            </div>
          </Form>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowSettings(false)}>
            Cancel
          </Button>
          <Button variant="primary" onClick={updateResponseLimit}>
            Save Changes
          </Button>
        </Modal.Footer>
      </Modal>
    </div>
  );
};

export default TokenUsageWidget;