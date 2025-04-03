import React, { useState, useEffect } from 'react';
import { Card, Button, ProgressBar, OverlayTrigger, Tooltip, Modal, Form, Row, Col, Badge } from 'react-bootstrap';
import { FaCog, FaInfoCircle, FaChartLine, FaServer, FaExclamationTriangle } from 'react-icons/fa';

// Define interfaces for token usage data
interface TokenUsage {
  used: number;
  limit: number;
  percentage: number;
}

interface TokenUsageByModel {
  [key: string]: TokenUsage;
}

/**
 * TokenUsageWidget Component
 * 
 * A component that displays token usage statistics and allows
 * configuration of token limits.
 */
const TokenUsageWidget: React.FC = () => {
  const [totalUsage, setTotalUsage] = useState<TokenUsage>({
    used: 0,
    limit: 1000000,
    percentage: 0
  });
  
  const [modelUsage, setModelUsage] = useState<TokenUsageByModel>({
    'gpt-4': {
      used: 0,
      limit: 500000,
      percentage: 0
    },
    'gpt-3.5-turbo': {
      used: 0,
      limit: 500000,
      percentage: 0
    }
  });
  
  const [showConfigModal, setShowConfigModal] = useState(false);
  const [selectedModel, setSelectedModel] = useState('total');
  const [newLimit, setNewLimit] = useState('1000000');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Fetch token usage data from API
  useEffect(() => {
    const fetchTokenUsage = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await fetch('/api/usage/tokens');
        
        if (!response.ok) {
          throw new Error(`Error ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        
        if (data) {
          // Update total usage
          const total = {
            used: data.total_tokens_used || 0,
            limit: data.total_tokens_limit || 1000000,
            percentage: data.total_tokens_used 
              ? Math.min(100, (data.total_tokens_used / data.total_tokens_limit) * 100)
              : 0
          };
          setTotalUsage(total);
          
          // Update model-specific usage
          const models: TokenUsageByModel = {};
          if (data.models) {
            Object.keys(data.models).forEach(model => {
              const modelData = data.models[model];
              models[model] = {
                used: modelData.tokens_used || 0,
                limit: modelData.tokens_limit || 500000,
                percentage: modelData.tokens_used
                  ? Math.min(100, (modelData.tokens_used / modelData.tokens_limit) * 100)
                  : 0
              };
            });
            setModelUsage(models);
          }
        }
      } catch (error) {
        console.error('Error fetching token usage:', error);
        setError('Failed to load token usage data');
      } finally {
        setLoading(false);
      }
    };
    
    fetchTokenUsage();
    // Refresh every 5 minutes
    const interval = setInterval(fetchTokenUsage, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);
  
  const handleSaveLimit = async () => {
    try {
      const limitValue = parseInt(newLimit);
      if (isNaN(limitValue) || limitValue <= 0) {
        return;
      }
      
      setLoading(true);
      const response = await fetch('/api/usage/limits', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          model: selectedModel === 'total' ? null : selectedModel,
          token_limit: limitValue
        })
      });
      
      if (response.ok) {
        // Update the UI with new limit
        if (selectedModel === 'total') {
          setTotalUsage(prev => ({
            ...prev,
            limit: limitValue,
            percentage: (prev.used / limitValue) * 100
          }));
        } else {
          setModelUsage(prev => ({
            ...prev,
            [selectedModel]: {
              ...prev[selectedModel],
              limit: limitValue,
              percentage: (prev[selectedModel].used / limitValue) * 100
            }
          }));
        }
        setShowConfigModal(false);
      } else {
        throw new Error(`Error ${response.status}: ${response.statusText}`);
      }
    } catch (error) {
      console.error('Error saving token limit:', error);
      setError('Failed to update token limit');
    } finally {
      setLoading(false);
    }
  };
  
  // Helper function to determine progress bar variant based on percentage
  const getProgressVariant = (percentage: number) => {
    if (percentage >= 90) return 'danger';
    if (percentage >= 70) return 'warning';
    return 'success';
  };
  
  // Helper function to format large numbers
  const formatNumber = (num: number): string => {
    if (num >= 1000000) {
      return (num / 1000000).toFixed(1) + 'M';
    } else if (num >= 1000) {
      return (num / 1000).toFixed(1) + 'K';
    }
    return num.toString();
  };
  
  if (loading && Object.keys(modelUsage).length === 0) {
    return (
      <div className="text-center p-4">
        <div className="spinner-border text-primary" role="status">
          <span className="visually-hidden">Loading...</span>
        </div>
        <p className="text-muted mt-2">Loading token usage data...</p>
      </div>
    );
  }
  
  if (error && Object.keys(modelUsage).length === 0) {
    return (
      <div className="alert alert-danger">
        <FaExclamationTriangle className="me-2" />
        {error}
      </div>
    );
  }
  
  return (
    <div className="token-usage-widget">
      <Row>
        <Col xs={12} className="mb-4">
          <div className="d-flex justify-content-between align-items-center mb-3">
            <div>
              <div className="d-flex align-items-center">
                <FaChartLine className="me-2 text-primary" />
                <h5 className="mb-0">Token Usage</h5>
              </div>
              <p className="text-muted small mb-0">Current billing period</p>
            </div>
            <Button 
              variant="outline-primary" 
              size="sm" 
              onClick={() => {
                setSelectedModel('total');
                setNewLimit(totalUsage.limit.toString());
                setShowConfigModal(true);
              }}
              disabled={loading}
            >
              <FaCog className="me-1" /> Configure Limits
            </Button>
          </div>
          
          {/* Total Usage Card */}
          <Card className="mb-3 shadow-sm">
            <Card.Body>
              <div className="d-flex justify-content-between align-items-center mb-2">
                <h6 className="fw-bold mb-0">Total Usage</h6>
                <div>
                  <Badge 
                    bg={getProgressVariant(totalUsage.percentage)} 
                    className="me-2"
                  >
                    {Math.round(totalUsage.percentage)}%
                  </Badge>
                  <span className="fw-bold">
                    {formatNumber(totalUsage.used)} / {formatNumber(totalUsage.limit)}
                  </span>
                  <OverlayTrigger
                    placement="top"
                    overlay={
                      <Tooltip id="tooltip-total">
                        {totalUsage.percentage.toFixed(1)}% of your total token allocation used
                      </Tooltip>
                    }
                  >
                    <FaInfoCircle className="ms-2 text-muted" style={{ cursor: 'pointer' }} />
                  </OverlayTrigger>
                </div>
              </div>
              <ProgressBar 
                now={totalUsage.percentage} 
                variant={getProgressVariant(totalUsage.percentage)}
                style={{ height: '10px' }}
                animated={totalUsage.percentage > 90}
              />
              <div className="d-flex justify-content-between mt-2">
                <small className="text-muted">0</small>
                <small className="text-muted">{formatNumber(totalUsage.limit)} tokens</small>
              </div>
            </Card.Body>
          </Card>
        </Col>
      </Row>
      
      {/* Model-specific Usage Cards */}
      <Row>
        {Object.keys(modelUsage).map(model => (
          <Col xs={12} md={6} key={model} className="mb-3">
            <Card className="h-100 shadow-sm">
              <Card.Body>
                <div className="d-flex justify-content-between align-items-center mb-2">
                  <div className="d-flex align-items-center">
                    <FaServer className="me-2 text-secondary" />
                    <h6 className="fw-bold mb-0">{model}</h6>
                  </div>
                  <Badge 
                    bg={getProgressVariant(modelUsage[model].percentage)} 
                    className="me-2"
                  >
                    {Math.round(modelUsage[model].percentage)}%
                  </Badge>
                </div>
                
                <div className="d-flex justify-content-between mb-2">
                  <span>{formatNumber(modelUsage[model].used)} used</span>
                  <span>{formatNumber(modelUsage[model].limit)} limit</span>
                </div>
                
                <ProgressBar 
                  now={modelUsage[model].percentage} 
                  variant={getProgressVariant(modelUsage[model].percentage)}
                  style={{ height: '8px' }}
                  animated={modelUsage[model].percentage > 90}
                />
              </Card.Body>
            </Card>
          </Col>
        ))}
      </Row>
      
      {/* Configuration Modal */}
      <Modal 
        show={showConfigModal} 
        onHide={() => setShowConfigModal(false)}
        backdrop="static"
        centered
      >
        <Modal.Header closeButton>
          <Modal.Title>
            <FaCog className="me-2" />
            Configure Token Limits
          </Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Form>
            <Form.Group className="mb-3">
              <Form.Label>Select Model</Form.Label>
              <Form.Select 
                value={selectedModel}
                onChange={(e) => {
                  const model = e.target.value;
                  setSelectedModel(model);
                  if (model === 'total') {
                    setNewLimit(totalUsage.limit.toString());
                  } else {
                    setNewLimit(modelUsage[model]?.limit.toString() || '500000');
                  }
                }}
              >
                <option value="total">Total (All Models)</option>
                {Object.keys(modelUsage).map(model => (
                  <option key={model} value={model}>{model}</option>
                ))}
              </Form.Select>
              <Form.Text className="text-muted">
                Configure limits for specific models or set an overall total
              </Form.Text>
            </Form.Group>
            
            <Form.Group className="mb-3">
              <Form.Label>Token Limit</Form.Label>
              <Form.Control 
                type="number" 
                min="1000"
                value={newLimit}
                onChange={(e) => setNewLimit(e.target.value)}
              />
              <Form.Text className="text-muted">
                Set the maximum number of tokens that can be used
              </Form.Text>
            </Form.Group>
            
            {selectedModel === 'total' && (
              <div className="alert alert-info">
                <FaInfoCircle className="me-2" />
                Setting a total limit helps control overall usage across all AI models
              </div>
            )}
          </Form>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowConfigModal(false)} disabled={loading}>
            Cancel
          </Button>
          <Button variant="primary" onClick={handleSaveLimit} disabled={loading}>
            {loading ? (
              <>
                <span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                Saving...
              </>
            ) : 'Save Changes'}
          </Button>
        </Modal.Footer>
      </Modal>
    </div>
  );
};

export default TokenUsageWidget;