import { supabase } from '../lib/supabase';
import { 
  KnowledgeFile, 
  KnowledgeFileWithContent, 
  KnowledgeCategory, 
  KnowledgeTag, 
  KnowledgeSearchResult 
} from '../types';

/**
 * Fetch all knowledge files - Use API only, no Supabase fallback due to schema cache issues
 */
export const getKnowledgeFiles = async (limit = 20, offset = 0): Promise<{ files: KnowledgeFile[], total: number }> => {
  try {
    const { data: { session } } = await supabase.auth.getSession();
    if (!session) throw new Error('Not authenticated');

    // Use the API endpoint only - no Supabase fallback
    const response = await fetch(`/api/knowledge/files?limit=${limit}&offset=${offset}`, {
      headers: {
        'Authorization': `Bearer ${session.access_token}`
      }
    });
    
    if (!response.ok) {
      throw new Error(`API request failed with status: ${response.status}`);
    }
    
    const data = await response.json();
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
    return data.file;
  } catch (error) {
    console.error('Error fetching knowledge file:', error);
    throw error;
  }
};

/**
 * Upload a file to the knowledge base
 * Modified to use the binary upload endpoint as fallback
 */
export const uploadKnowledgeFile = async (
  file: File, 
  category?: string, 
  tags?: string[]
): Promise<KnowledgeFile> => {
  try {
    const { data: { session } } = await supabase.auth.getSession();
    if (!session) throw new Error('Not authenticated');

    // Use direct form upload to binary endpoint first
    const formData = new FormData();
    formData.append('file', file);
    
    if (category) formData.append('category', category);
    if (tags && tags.length > 0) formData.append('tags', JSON.stringify(tags));

    try {
      // Try binary upload first - this should support multipart/form-data
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
      
      // If binary endpoint failed, try base64 approach as fallback
      console.warn('Binary upload failed, falling back to standard upload...');
      
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

    // Use API endpoint
    const response = await fetch(`/api/knowledge/files/${fileId}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${session.access_token}`
      }
    });
    
    if (!response.ok) {
      throw new Error(`API request failed with status: ${response.status}`);
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
 * Get list of categories
 */
export const getCategories = async (): Promise<KnowledgeCategory[]> => {
  try {
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
    return data.categories;
  } catch (error) {
    console.error('Error fetching categories:', error);
    return [];
  }
};

/**
 * Get list of tags
 */
export const getTags = async (): Promise<KnowledgeTag[]> => {
  try {
    const { data: { session } } = await supabase.auth.getSession();
    if (!session) throw new Error('Not authenticated');

    // Use API endpoint
    const response = await fetch(`/api/knowledge/tags`, {
      headers: {
        'Authorization': `Bearer ${session.access_token}`
      }
    });
    
    if (!response.ok) {
      throw new Error(`API request failed with status: ${response.status}`);
    }
    
    const data = await response.json();
    return data.tags;
  } catch (error) {
    console.error('Error fetching tags:', error);
    return [];
  }
};

/**
 * Search the knowledge base
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
    return data.results;
  } catch (error) {
    console.error('Error searching knowledge base:', error);
    return [];
  }
};