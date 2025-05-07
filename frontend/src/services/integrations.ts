/**
 * Dana AI Platform - Standardized Integration API Service
 * 
 * This module provides standardized API calls for integration endpoints.
 * All frontend components should use these methods for integration operations.
 */

import { getCsrfToken } from './csrf';
import { getAuthToken } from './auth-helpers';

/**
 * Base URL for API endpoints
 */
const API_BASE_URL = '/api/v2/integrations';

/**
 * Integration configuration interface
 */
export interface IntegrationConfig {
  [key: string]: any;
}

/**
 * Integration status response interface
 */
export interface IntegrationStatus {
  status: string;
  configured: boolean;
  [key: string]: any;
}

/**
 * Function to check if API integration is available
 * @param {string} integrationType - Type of integration
 * @returns {Promise<boolean>} - True if integration is available
 */
export const checkIntegrationAvailable = async (integrationType: string): Promise<boolean> => {
  try {
    const response = await fetch(`${API_BASE_URL}/${integrationType}/test`);
    const data = await response.json();
    return data.success === true;
  } catch (error) {
    console.error(`Error checking ${integrationType} integration:`, error);
    return false;
  }
};

/**
 * Function to connect an integration
 * @param {string} integrationType - Type of integration
 * @param {IntegrationConfig} config - Integration configuration
 * @returns {Promise<any>} - Response data
 */
export const connectIntegration = async (
  integrationType: string, 
  config: IntegrationConfig
): Promise<any> => {
  try {
    // Get CSRF token for non-GET requests
    const csrfToken = await getCsrfToken();
    
    // Get authentication token
    const authToken = await getAuthToken();
    if (!authToken) {
      throw new Error('Authentication required');
    }
    
    // Add CSRF token to config
    const configWithToken = {
      ...config,
      csrf_token: csrfToken
    };
    
    // Make API request
    const response = await fetch(`${API_BASE_URL}/${integrationType}/connect`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${authToken}`
      },
      body: JSON.stringify(configWithToken)
    });
    
    const data = await response.json();
    
    if (!data.success) {
      throw new Error(data.error || `Error connecting ${integrationType}`);
    }
    
    return data;
  } catch (error) {
    console.error(`Error connecting ${integrationType} integration:`, error);
    throw error;
  }
};

/**
 * Function to disconnect an integration
 * @param {string} integrationType - Type of integration
 * @returns {Promise<any>} - Response data
 */
export const disconnectIntegration = async (integrationType: string): Promise<any> => {
  try {
    // Get CSRF token for non-GET requests
    const csrfToken = await getCsrfToken();
    
    // Get authentication token
    const authToken = await getAuthToken();
    if (!authToken) {
      throw new Error('Authentication required');
    }
    
    // Make API request
    const response = await fetch(`${API_BASE_URL}/${integrationType}/disconnect`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${authToken}`
      },
      body: JSON.stringify({ csrf_token: csrfToken })
    });
    
    const data = await response.json();
    
    if (!data.success) {
      throw new Error(data.error || `Error disconnecting ${integrationType}`);
    }
    
    return data;
  } catch (error) {
    console.error(`Error disconnecting ${integrationType} integration:`, error);
    throw error;
  }
};

/**
 * Function to get integration status
 * @param {string} integrationType - Type of integration
 * @returns {Promise<IntegrationStatus>} - Integration status
 */
export const getIntegrationStatus = async (integrationType: string): Promise<IntegrationStatus> => {
  try {
    // Get authentication token
    const authToken = await getAuthToken();
    if (!authToken) {
      throw new Error('Authentication required');
    }
    
    // Make API request
    const response = await fetch(`${API_BASE_URL}/${integrationType}/status`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${authToken}`
      }
    });
    
    const data = await response.json();
    
    if (!data.success) {
      throw new Error(data.error || `Error getting ${integrationType} status`);
    }
    
    return data as IntegrationStatus;
  } catch (error) {
    console.error(`Error getting ${integrationType} integration status:`, error);
    throw error;
  }
};

/**
 * Function to get all integrations status
 * @returns {Promise<Record<string, IntegrationStatus>>} - All integrations status
 */
export const getAllIntegrationsStatus = async (): Promise<Record<string, IntegrationStatus>> => {
  try {
    // Get authentication token
    const authToken = await getAuthToken();
    if (!authToken) {
      throw new Error('Authentication required');
    }
    
    // Make API request
    const response = await fetch(`${API_BASE_URL}/status`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${authToken}`
      }
    });
    
    const data = await response.json();
    
    if (!data.success) {
      throw new Error(data.error || 'Error getting integrations status');
    }
    
    return data.integrations || {};
  } catch (error) {
    console.error('Error getting all integrations status:', error);
    throw error;
  }
};

/**
 * Function to create integration configuration component
 * This is a utility method to help decouple the UI components from the API
 * 
 * @param {string} integrationType - Type of integration
 * @param {IntegrationConfig} defaultConfig - Default configuration
 * @returns {Object} - Integration configuration handlers
 */
export const createIntegrationHandler = (
  integrationType: string,
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  defaultConfig: IntegrationConfig = {}
) => {
  return {
    // Connect the integration
    connect: async (config: IntegrationConfig) => {
      return await connectIntegration(integrationType, config);
    },
    
    // Disconnect the integration
    disconnect: async () => {
      return await disconnectIntegration(integrationType);
    },
    
    // Get the integration status
    getStatus: async () => {
      return await getIntegrationStatus(integrationType);
    },
    
    // Check if the integration is available
    checkAvailable: async () => {
      return await checkIntegrationAvailable(integrationType);
    },
    
    // The integration type
    integrationType
  };
};

// Export predefined handlers for common integrations
export const EMAIL_INTEGRATION = createIntegrationHandler('email', {
  email: '',
  password: '',
  smtp_server: '',
  smtp_port: ''
});

export const GOOGLE_ANALYTICS_INTEGRATION = createIntegrationHandler('google_analytics', {
  view_id: '',
  client_email: '',
  private_key: ''
});

export const SLACK_INTEGRATION = createIntegrationHandler('slack', {
  access_token: '',
  channel_id: ''
});

export const HUBSPOT_INTEGRATION = createIntegrationHandler('hubspot', {
  api_key: ''
});

export const SALESFORCE_INTEGRATION = createIntegrationHandler('salesforce', {
  client_id: '',
  client_secret: '',
  username: '',
  password: ''
});

export const ZENDESK_INTEGRATION = createIntegrationHandler('zendesk', {
  subdomain: '',
  email: '',
  api_token: ''
});

export const SHOPIFY_INTEGRATION = createIntegrationHandler('shopify', {
  shop_url: '',
  api_key: '',
  api_secret: ''
});