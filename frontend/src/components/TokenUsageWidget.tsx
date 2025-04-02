import React, { useState, useEffect } from 'react';
import { Card, Button, ProgressBar, OverlayTrigger, Tooltip, Modal, Form } from 'react-bootstrap';
import { FaCog, FaInfoCircle } from 'react-icons/fa';

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
  
  // Fetch token usage data from API
  useEffect(() => {
    const fetchTokenUsage = async () => {
      try {
        const response = await fetch('/api/usage/tokens');
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
      
      const response = await fetch('/api/usage/configure', {
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
      }
    } catch (error) {
      console.error('Error saving token limit:', error);
    }
  };
  
  // Helper function to determine progress bar variant based on percentage
  const getProgressVariant = (percentage: number) => {
    if (percentage >= 90) return 'danger';
    if (percentage >= 70) return 'warning';
    return 'success';
  };
  
  return (
    <div className="token-usage-widget">
      <div className="d-flex justify-content-between align-items-center mb-3">
        <div>
          <h5 className="mb-0">Token Usage</h5>
          <p className="text-muted small">Current billing period</p>
        </div>
        <Button 
          variant="outline-secondary" 
          size="sm" 
          onClick={() => {
            setSelectedModel('total');
            setNewLimit(totalUsage.limit.toString());
            setShowConfigModal(true);
          }}
        >
          <FaCog className="me-1" /> Configure
        </Button>
      </div>
      
      <div className="mb-4">
        <div className="d-flex justify-content-between mb-1">
          <span>Total Usage</span>
          <span>
            {totalUsage.used.toLocaleString()} / {totalUsage.limit.toLocaleString()} tokens
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
          </span>
        </div>
        <ProgressBar 
          now={totalUsage.percentage} 
          variant={getProgressVariant(totalUsage.percentage)}
          style={{ height: '8px' }}
        />
      </div>
      
      {Object.keys(modelUsage).map(model => (
        <div className="mb-3" key={model}>
          <div className="d-flex justify-content-between mb-1">
            <span>{model}</span>
            <span>
              {modelUsage[model].used.toLocaleString()} / {modelUsage[model].limit.toLocaleString()} tokens
              <OverlayTrigger
                placement="top"
                overlay={
                  <Tooltip id={`tooltip-${model}`}>
                    {modelUsage[model].percentage.toFixed(1)}% of your {model} token allocation used
                  </Tooltip>
                }
              >
                <FaInfoCircle className="ms-2 text-muted" style={{ cursor: 'pointer' }} />
              </OverlayTrigger>
            </span>
          </div>
          <ProgressBar 
            now={modelUsage[model].percentage} 
            variant={getProgressVariant(modelUsage[model].percentage)}
            style={{ height: '6px' }}
          />
        </div>
      ))}
      
      <Modal show={showConfigModal} onHide={() => setShowConfigModal(false)}>
        <Modal.Header closeButton>
          <Modal.Title>Configure Token Limits</Modal.Title>
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
          </Form>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowConfigModal(false)}>
            Cancel
          </Button>
          <Button variant="primary" onClick={handleSaveLimit}>
            Save Changes
          </Button>
        </Modal.Footer>
      </Modal>
    </div>
  );
};

export default TokenUsageWidget;