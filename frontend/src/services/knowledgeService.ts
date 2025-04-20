import { supabase } from '../lib/supabase';
import { 
  KnowledgeFile, 
  KnowledgeFileWithContent, 
  KnowledgeCategory, 
  KnowledgeTag, 
  KnowledgeSearchResult 
} from '../types';

// Simple cache implementation
const cache = {
  files: new Map<string, {data: any, timestamp: number}>(),
  categories: null as {data: KnowledgeCategory[], timestamp: number} | null,
  tags: null as {data: KnowledgeTag[], timestamp: number} | null,
  searches: {} as Record<string, {data: KnowledgeSearchResult[], timestamp: number}>,
  
  // Cache expiration in milliseconds (5 minutes)
  EXPIRATION: 5 * 60 * 1000,
  
  // Check if cache entry is valid
  isValid: function(timestamp: number) {
    return (Date.now() - timestamp) < this.EXPIRATION;
  },
  
  // Clear all cache
  clear: function() {
    this.files.clear();
    this.categories = null;
    this.tags = null;
    this.searches = {};
  }
};

/**
 * Fetch all knowledge files - Use API only, no Supabase fallback due to schema cache issues
 * With caching for improved performance
 */
export const getKnowledgeFiles = async (limit = 20, offset = 0, forceRefresh = false): Promise<{ files: KnowledgeFile[], total: number }> => {
  try {
    // Check cache first (unless force refresh is requested)
    const cacheKey = `files-${limit}-${offset}`;
    const cachedData = cache.files.get(cacheKey);
    
    if (!forceRefresh && cachedData && cache.isValid(cachedData.timestamp)) {
      console.log('Using cached knowledge files data');
      return cachedData.data;
    }
    
    console.log('Fetching fresh knowledge files data');
    const { data: { session } } = await supabase.auth.getSession();
    if (!session) throw new Error('Not authenticated');

    // Add timestamp to URL to prevent browser caching
    const timestamp = Date.now();
    
    // Use the API endpoint only - no Supabase fallback
    const response = await fetch(`/api/knowledge/files?limit=${limit}&offset=${offset}&_t=${timestamp}`, {
      headers: {
        'Authorization': `Bearer ${session.access_token}`
      }
    });
    
    if (!response.ok) {
      throw new Error(`API request failed with status: ${response.status}`);
    }
    
    const data = await response.json();
    
    // Normalize file data to ensure consistent field names
    if (data.files && Array.isArray(data.files)) {
      data.files = data.files.map(file => ({
        ...file,
        // Ensure we have file_name (some endpoints return filename instead)
        file_name: file.file_name || file.filename || 'Unnamed file'
      }));
    }
    
    // Cache the results
    cache.files.set(cacheKey, {
      data,
      timestamp: Date.now()
    });
    
    return data;
  } catch (error) {
    console.error('Error fetching knowledge files:', error);
    // Return empty results instead of throwing - better UX
    return { files: [], total: 0 };
  }
};

/**
 * Get file details including content - Use API only, no Supabase fallback due to schema cache issues
 */
export const getKnowledgeFile = async (fileId: string): Promise<KnowledgeFileWithContent> => {
  try {
    const { data: { session } } = await supabase.auth.getSession();
    if (!session) throw new Error('Not authenticated');

    // Use the API endpoint
    const response = await fetch(`/api/knowledge/files/${fileId}`, {
      headers: {
        'Authorization': `Bearer ${session.access_token}`
      }
    });
    
    if (!response.ok) {
      throw new Error(`API request failed with status: ${response.status}`);
    }
    
    const data = await response.json();
    
    // Ensure the file has the required fields
    if (!data.file) {
      throw new Error('No file data returned from API');
    }
    
    // Create a normalized version of the file that always has the expected field names
    const normalizedFile: KnowledgeFileWithContent = {
      ...data.file,
      // Ensure we have file_name (some endpoints return filename instead)
      file_name: data.file.file_name || data.file.filename || 'Unnamed file',
      // Ensure proper text content
      content: data.file.content || data.file.binary_data || '',
      // Parse tags if needed
      tags: data.file.tags
    };
    
    return normalizedFile;
  } catch (error) {
    console.error('Error fetching knowledge file:', error);
    throw error;
  }
};

/**
 * Upload a file to the knowledge base
 * Modified to use multiple upload endpoints with fallbacks and progress tracking
 */
export const uploadKnowledgeFile = async (
  file: File, 
  category?: string, 
  tags?: string[],
  onProgress?: (progress: number) => void
): Promise<KnowledgeFile> => {
  try {
    const { data: { session } } = await supabase.auth.getSession();
    if (!session) throw new Error('Not authenticated');

    // Clear the knowledge files cache before uploading
    // This ensures that getKnowledgeFiles will fetch fresh data after upload
    cache.files.clear();
    console.log('Cleared knowledge files cache before upload');

    // Start progress immediately
    onProgress?.(5);

    // Prepare form data for all attempts
    const formData = new FormData();
    formData.append('file', file);
    
    if (category) formData.append('category', category);
    if (tags && tags.length > 0) formData.append('tags', JSON.stringify(tags));

    // Update progress to indicate request preparation
    onProgress?.(10);

    // Check if file is a PDF to use the PDF-specific endpoint
    if (file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf')) {
      console.log('Using PDF-specific upload endpoint');
      try {
        // Signal progress as request is sent
        onProgress?.(25);
        
        // Try PDF-specific endpoint first
        const pdfResponse = await fetch('/api/knowledge/pdf-upload', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${session.access_token}`
          },
          body: formData
        });
        
        // Signal progress as response is received
        onProgress?.(75);
        
        if (pdfResponse.ok) {
          // Signal progress nearly complete
          onProgress?.(90);
          const result = await pdfResponse.json();
          console.log('PDF upload successful', result);
          onProgress?.(100);
          
          // Map the response to match the expected structure in KnowledgeFile
          // Backend returns "filename" but frontend expects "file_name"
          if (result.file && result.file.filename) {
            return {
              ...result.file,
              file_name: result.file.filename, // Map to the correct property name
            };
          }
          
          return result.file;
        }
        
        console.warn('PDF upload failed, trying other methods...');
        onProgress?.(30); // Reset progress for next attempt
      } catch (pdfError) {
        console.error('PDF upload error:', pdfError);
        onProgress?.(30); // Reset progress for next attempt
        // Continue to other methods
      }
    }

    try {
      // Try binary upload endpoint
      const response = await fetch('/api/knowledge/files/binary', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${session.access_token}`
        },
        body: formData
      });
      
      // If binary upload worked, return the result
      if (response.ok) {
        const result = await response.json();
        console.log('Binary upload successful', result);
        // The binary endpoint might return different response structure
        return result.file || result;
      }
      
      // Try direct-upload endpoint next
      const directResponse = await fetch('/api/knowledge/direct-upload', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${session.access_token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          filename: file.name,
          file_type: file.type || determineMimeType(file.name),
          file_size: file.size,
          content: await readFileAsBase64(file),
          category,
          tags: tags && tags.length > 0 ? tags : [],
          is_base64: true
        })
      });
      
      if (directResponse.ok) {
        const result = await directResponse.json();
        console.log('Direct upload successful', result);
        
        // Get the filename from the response
        const filename = result.file_info?.filename || file.name;
        
        // Format the response to match expected structure
        return {
          id: result.file_id,
          user_id: result.user_id,
          file_name: filename, // Use file_name to match the KnowledgeFile type
          file_size: result.file_info?.file_size || file.size,
          file_type: result.file_info?.file_type || file.type || determineMimeType(file.name),
          created_at: result.file_info?.created_at || new Date().toISOString(),
          updated_at: result.file_info?.created_at || new Date().toISOString()
        };
      }
      
      // If direct upload failed, try standard endpoint as last resort
      console.warn('Direct upload failed, falling back to standard upload...');
      
      // Convert file to base64
      const base64Content = await readFileAsBase64(file);
      
      // Prepare JSON payload
      const fileData = {
        file_name: file.name,
        file_size: file.size,
        file_type: file.type || determineMimeType(file.name),
        content: base64Content,
        category,
        tags: tags && tags.length > 0 ? JSON.stringify(tags) : undefined
      };
      
      // Try standard JSON upload
      const jsonResponse = await fetch('/api/knowledge/files', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session.access_token}`
        },
        body: JSON.stringify(fileData)
      });
      
      if (!jsonResponse.ok) {
        const errorText = await jsonResponse.text();
        throw new Error(`Upload failed: ${jsonResponse.status}, ${errorText}`);
      }
      
      const result = await jsonResponse.json();
      return result.file;
      
    } catch (error) {
      console.error('All upload methods failed:', error);
      throw error;
    }
  } catch (error) {
    console.error('Error uploading knowledge file:', error);
    throw error;
  }
};

/**
 * Helper function to read a file as base64
 */
const readFileAsBase64 = (file: File): Promise<string> => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    
    reader.onload = () => {
      if (reader.result) {
        // result is like "data:image/png;base64,iVBORw0KGg..."
        resolve(reader.result as string);
      } else {
        reject(new Error('Failed to read file'));
      }
    };
    
    reader.onerror = () => {
      reject(new Error('Failed to read file'));
    };
    
    reader.readAsDataURL(file);
  });
};

/**
 * Determine MIME type from file extension if not provided
 */
const determineMimeType = (filename: string): string => {
  const extension = filename.split('.').pop()?.toLowerCase();
  
  switch (extension) {
    case 'pdf':
      return 'application/pdf';
    case 'doc':
    case 'docx':
      return 'application/vnd.openxmlformats-officedocument.wordprocessingml.document';
    case 'txt':
      return 'text/plain';
    case 'md':
      return 'text/markdown';
    case 'csv':
      return 'text/csv';
    case 'json':
      return 'application/json';
    default:
      return 'application/octet-stream';
  }
};

/**
 * Delete a file from the knowledge base
 */
export const deleteKnowledgeFile = async (fileId: string): Promise<boolean> => {
  try {
    const { data: { session } } = await supabase.auth.getSession();
    if (!session) throw new Error('Not authenticated');

    // Clear the cache first to ensure getKnowledgeFiles retrieves fresh data
    cache.files.clear();
    console.log('Cleared knowledge files cache before delete');

    console.log(`Attempting to delete file with ID: ${fileId}`);
    
    // Use API endpoint with additional logging
    const response = await fetch(`/api/knowledge/files/${fileId}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${session.access_token}`,
        'Content-Type': 'application/json'
      }
    });
    
    // Log the response for debugging
    console.log(`Delete API response status: ${response.status}`);
    
    // Try to parse the response as JSON for better error messages
    let responseText = '';
    try {
      responseText = await response.text();
      console.log('Delete API response text:', responseText);
    } catch (e) {
      console.error('Error reading response text:', e);
    }
    
    if (!response.ok) {
      throw new Error(`API request failed with status: ${response.status}, message: ${responseText}`);
    }
    
    return true;
  } catch (error) {
    console.error('Error deleting knowledge file:', error);
    throw error;
  }
};

/**
 * Bulk delete multiple files
 */
export const bulkDeleteKnowledgeFiles = async (fileIds: string[]): Promise<boolean> => {
  try {
    const { data: { session } } = await supabase.auth.getSession();
    if (!session) throw new Error('Not authenticated');

    // Clear the cache first to ensure getKnowledgeFiles retrieves fresh data
    cache.files.clear();
    console.log('Cleared knowledge files cache before bulk delete');

    // Use API endpoint
    const response = await fetch(`/api/knowledge/files/bulk-delete`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${session.access_token}`
      },
      body: JSON.stringify({ file_ids: fileIds })
    });
    
    if (!response.ok) {
      throw new Error(`API request failed with status: ${response.status}`);
    }
    
    return true;
  } catch (error) {
    console.error('Error bulk deleting knowledge files:', error);
    throw error;
  }
};

/**
 * Update a knowledge file (metadata only)
 */
export const updateKnowledgeFile = async (
  fileId: string, 
  data: Partial<KnowledgeFile>
): Promise<KnowledgeFile> => {
  try {
    const { data: { session } } = await supabase.auth.getSession();
    if (!session) throw new Error('Not authenticated');

    // Clear the cache first to ensure getKnowledgeFiles retrieves fresh data
    cache.files.clear();
    console.log('Cleared knowledge files cache before update');

    // Use API endpoint
    const response = await fetch(`/api/knowledge/files/${fileId}`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${session.access_token}`
      },
      body: JSON.stringify(data)
    });
    
    if (!response.ok) {
      throw new Error(`API request failed with status: ${response.status}`);
    }
    
    const result = await response.json();
    return result.file;
  } catch (error) {
    console.error('Error updating knowledge file:', error);
    throw error;
  }
};

/**
 * Bulk update multiple files
 */
export const bulkUpdateKnowledgeFiles = async (
  fileIds: string[], 
  data: Partial<KnowledgeFile>
): Promise<boolean> => {
  try {
    const { data: { session } } = await supabase.auth.getSession();
    if (!session) throw new Error('Not authenticated');

    // Clear the cache first to ensure getKnowledgeFiles retrieves fresh data
    cache.files.clear();
    console.log('Cleared knowledge files cache before bulk update');

    // Use API endpoint
    const response = await fetch(`/api/knowledge/files/bulk-update`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${session.access_token}`
      },
      body: JSON.stringify({ 
        file_ids: fileIds,
        update_data: data
      })
    });
    
    if (!response.ok) {
      throw new Error(`API request failed with status: ${response.status}`);
    }
    
    return true;
  } catch (error) {
    console.error('Error bulk updating knowledge files:', error);
    throw error;
  }
};

/**
 * Get list of categories with caching for improved performance
 */
export const getCategories = async (): Promise<KnowledgeCategory[]> => {
  try {
    // Check cache first
    if (cache.categories && cache.isValid(cache.categories.timestamp)) {
      console.log('Using cached categories data');
      return cache.categories.data;
    }
    
    console.log('Fetching fresh categories data');
    const { data: { session } } = await supabase.auth.getSession();
    if (!session) throw new Error('Not authenticated');

    // Use API endpoint
    const response = await fetch(`/api/knowledge/categories`, {
      headers: {
        'Authorization': `Bearer ${session.access_token}`
      }
    });
    
    if (!response.ok) {
      throw new Error(`API request failed with status: ${response.status}`);
    }
    
    const data = await response.json();
    
    // Cache the results
    cache.categories = {
      data: data.categories,
      timestamp: Date.now()
    };
    
    return data.categories;
  } catch (error) {
    console.error('Error fetching categories:', error);
    return [];
  }
};

/**
 * Get list of tags with caching for improved performance
 */
export const getTags = async (): Promise<KnowledgeTag[]> => {
  try {
    // Check cache first
    if (cache.tags && cache.isValid(cache.tags.timestamp)) {
      console.log('Using cached tags data');
      return cache.tags.data;
    }
    
    console.log('Fetching fresh tags data');
    const { data: { session } } = await supabase.auth.getSession();
    if (!session) throw new Error('Not authenticated');

    // Use API endpoint
    const response = await fetch(`/api/knowledge/files/tags`, {
      headers: {
        'Authorization': `Bearer ${session.access_token}`
      }
    });
    
    if (!response.ok) {
      throw new Error(`API request failed with status: ${response.status}`);
    }
    
    const data = await response.json();
    
    // Cache the results
    cache.tags = {
      data: data.tags,
      timestamp: Date.now()
    };
    
    return data.tags;
  } catch (error) {
    console.error('Error fetching tags:', error);
    return [];
  }
};

/**
 * Search the knowledge base with caching for improved performance
 */
export const searchKnowledgeBase = async (
  query: string,
  filters?: {
    category?: string;
    tags?: string[];
    date_from?: string;
    date_to?: string;
  }
): Promise<KnowledgeSearchResult[]> => {
  try {
    // Generate a cache key based on query and filters
    const cacheKey = `search_${query}_${JSON.stringify(filters || {})}`;
    
    // Check cache first
    if (cache.searches && cache.searches[cacheKey] && cache.isValid(cache.searches[cacheKey].timestamp)) {
      console.log('Using cached search results');
      return cache.searches[cacheKey].data;
    }
    
    console.log('Performing fresh search');
    const { data: { session } } = await supabase.auth.getSession();
    if (!session) throw new Error('Not authenticated');

    // Build query parameters
    const params = new URLSearchParams({ query });
    
    if (filters) {
      if (filters.category) params.append('category', filters.category);
      if (filters.date_from) params.append('date_from', filters.date_from);
      if (filters.date_to) params.append('date_to', filters.date_to);
      if (filters.tags && filters.tags.length > 0) {
        filters.tags.forEach(tag => params.append('tag', tag));
      }
    }

    // Use API endpoint
    const response = await fetch(`/api/knowledge/search?${params.toString()}`, {
      headers: {
        'Authorization': `Bearer ${session.access_token}`
      }
    });
    
    if (!response.ok) {
      throw new Error(`API request failed with status: ${response.status}`);
    }
    
    const data = await response.json();
    
    // Normalize search results to ensure consistent field names
    let results = [];
    if (data.results && Array.isArray(data.results)) {
      results = data.results.map(result => ({
        ...result,
        // Ensure we have file_name (some endpoints return filename instead)
        file_name: result.file_name || result.filename || 'Unnamed file'
      }));
    } else {
      results = data.results || [];
    }
    
    // Cache the search results
    if (!cache.searches) cache.searches = {};
    cache.searches[cacheKey] = {
      data: results,
      timestamp: Date.now()
    };
    
    return results;
  } catch (error) {
    console.error('Error searching knowledge base:', error);
    return [];
  }
};