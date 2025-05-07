/**
 * Dana AI Platform - Standardized Email Integration Component
 * 
 * This component provides a UI for the standardized email integration.
 * It uses the new standardized API endpoints via the integrations service.
 */

import React, { useState, useEffect } from 'react';
import { EMAIL_INTEGRATION, IntegrationStatus } from '../services/integrations';

interface EmailIntegrationProps {
  onSuccess?: () => void;
  onError?: (error: Error) => void;
}

const StandardEmailIntegration: React.FC<EmailIntegrationProps> = ({ onSuccess, onError }) => {
  // State for integration configuration
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [smtpServer, setSmtpServer] = useState('');
  const [smtpPort, setSmtpPort] = useState('');
  
  // State for API communication
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  
  // State for integration status
  const [status, setStatus] = useState<IntegrationStatus | null>(null);
  const [available, setAvailable] = useState<boolean>(false);

  // Fetch integration status and availability on component mount
  useEffect(() => {
    const checkStatus = async () => {
      try {
        // Check if integration is available
        const isAvailable = await EMAIL_INTEGRATION.checkAvailable();
        setAvailable(isAvailable);
        
        if (isAvailable) {
          try {
            // Get integration status if available
            const status = await EMAIL_INTEGRATION.getStatus();
            setStatus(status);
            
            if (status.configured) {
              setStatusMessage(`Email integration is ${status.status}`);
              setEmail(status.email || '');
            }
          } catch (statusError) {
            console.error('Error fetching email integration status:', statusError);
          }
        }
      } catch (error) {
        console.error('Error checking email integration availability:', error);
        setAvailable(false);
      }
    };
    
    checkStatus();
  }, []);

  // Handle form submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    
    try {
      // Connect email integration
      await EMAIL_INTEGRATION.connect({
        email,
        password,
        smtp_server: smtpServer,
        smtp_port: smtpPort
      });
      
      setStatusMessage('Email integration connected successfully');
      setLoading(false);
      
      // Refresh status
      const updatedStatus = await EMAIL_INTEGRATION.getStatus();
      setStatus(updatedStatus);
      
      // Call success callback if provided
      if (onSuccess) {
        onSuccess();
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error connecting email';
      setError(errorMessage);
      setLoading(false);
      
      // Call error callback if provided
      if (onError && error instanceof Error) {
        onError(error);
      }
    }
  };

  // Handle disconnect button
  const handleDisconnect = async () => {
    setLoading(true);
    setError(null);
    
    try {
      // Disconnect email integration
      await EMAIL_INTEGRATION.disconnect();
      
      setStatusMessage('Email integration disconnected successfully');
      setLoading(false);
      
      // Refresh status
      const updatedStatus = await EMAIL_INTEGRATION.getStatus();
      setStatus(updatedStatus);
      
      // Call success callback if provided
      if (onSuccess) {
        onSuccess();
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error disconnecting email';
      setError(errorMessage);
      setLoading(false);
      
      // Call error callback if provided
      if (onError && error instanceof Error) {
        onError(error);
      }
    }
  };

  // If integration is not available, show message
  if (!available) {
    return (
      <div className="alert alert-warning">
        Email integration API is not available. Please check server logs.
      </div>
    );
  }

  return (
    <div className="card">
      <div className="card-header">
        <h5>Email Integration</h5>
        {status?.configured && (
          <span className={`badge bg-${status.status === 'active' ? 'success' : 'warning'}`}>
            {status.status}
          </span>
        )}
      </div>
      <div className="card-body">
        {statusMessage && (
          <div className="alert alert-info">{statusMessage}</div>
        )}
        
        {error && (
          <div className="alert alert-danger">{error}</div>
        )}
        
        <form onSubmit={handleSubmit}>
          <div className="mb-3">
            <label htmlFor="email" className="form-label">Email</label>
            <input
              type="email"
              className="form-control"
              id="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>
          
          <div className="mb-3">
            <label htmlFor="password" className="form-label">Password</label>
            <input
              type="password"
              className="form-control"
              id="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
            <small className="form-text text-muted">
              For Gmail, you may need to use an App Password.
            </small>
          </div>
          
          <div className="mb-3">
            <label htmlFor="smtpServer" className="form-label">SMTP Server</label>
            <input
              type="text"
              className="form-control"
              id="smtpServer"
              value={smtpServer}
              onChange={(e) => setSmtpServer(e.target.value)}
              placeholder="e.g., smtp.gmail.com"
              required
            />
          </div>
          
          <div className="mb-3">
            <label htmlFor="smtpPort" className="form-label">SMTP Port</label>
            <input
              type="text"
              className="form-control"
              id="smtpPort"
              value={smtpPort}
              onChange={(e) => setSmtpPort(e.target.value)}
              placeholder="e.g., 587"
              required
            />
          </div>
          
          <div className="d-grid gap-2 d-md-flex justify-content-md-end">
            {status?.configured && status.status === 'active' ? (
              <button
                type="button"
                className="btn btn-danger"
                onClick={handleDisconnect}
                disabled={loading}
              >
                {loading ? 'Disconnecting...' : 'Disconnect'}
              </button>
            ) : (
              <button
                type="submit"
                className="btn btn-primary"
                disabled={loading}
              >
                {loading ? 'Connecting...' : 'Connect'}
              </button>
            )}
          </div>
        </form>
      </div>
    </div>
  );
};

export default StandardEmailIntegration;