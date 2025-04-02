import axios from 'axios';

// Custom fetch function with authentication
export const fetchWithAuth = async (url: string, token: string, options: any = {}) => {
  try {
    const method = options.method || 'GET';
    const headers = {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
      ...options.headers
    };
    
    let response;
    
    if (method === 'GET') {
      response = await axios.get(url, { headers });
    } else {
      response = await axios({
        method,
        url,
        headers,
        data: options.body
      });
    }
    
    return response.data;
  } catch (error: any) {
    console.error(`Error fetching ${url}:`, error);
    throw new Error(error.response?.data?.error || error.message || 'Failed to fetch data');
  }
};