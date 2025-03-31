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

    // Use API only
    const response = await fetch(`/api/knowledge/files/${fileId}`, {
      headers: {
        'Authorization': `Bearer ${session.access_token}`
      }
    });
    
    if (!response.ok) {
      throw new Error(`API request failed with status: ${response.status}`);
    }
    
    const data = await response.json();
    const file = data.file || data; // Handle both formats
    
    // Parse metadata if it's a string
    let parsedMetadata = file.metadata;
    if (typeof file.metadata === 'string') {
      try {
        parsedMetadata = JSON.parse(file.metadata);
      } catch (e) {
        console.warn('Failed to parse metadata JSON', e);
      }
    }

    // Parse tags if it's a string
    let parsedTags = file.tags;
    if (typeof file.tags === 'string') {
      try {
        parsedTags = JSON.parse(file.tags);
      } catch (e) {
        console.warn('Failed to parse tags JSON', e);
      }
    }

    return {
      ...file,
      metadata: parsedMetadata,
      tags: parsedTags,
    } as KnowledgeFileWithContent;
  } catch (error) {
    console.error('Error fetching knowledge file details:', error);
    throw error;
  }
};

/**
 * Upload a new knowledge file - Use API only, no Supabase fallback due to schema cache issues
 */
export const uploadKnowledgeFile = async (
  file: File, 
  category?: string, 
  tags?: string[]
): Promise<KnowledgeFile> => {
  try {
    const { data: { session } } = await supabase.auth.getSession();
    const { data: { user } } = await supabase.auth.getUser();
    
    if (!session || !user) throw new Error('Not authenticated');

    // Convert file to base64 instead of using ArrayBuffer
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      
      reader.onload = async (event) => {
        try {
          if (!event.target || !event.target.result) {
            throw new Error('Failed to read file');
          }
          
          // Get base64 data
          const base64Content = event.target.result as string;
          
          // Prepare tags as string if they exist
          const tagString = tags && tags.length > 0 ? JSON.stringify(tags) : undefined;
          
          // Use API only
          const fileData = {
            user_id: user.id,
            file_name: file.name,
            file_size: file.size,
            file_type: file.type,
            content: base64Content,
            category,
            tags: tagString
          };
          
          console.log(`Uploading file ${file.name} (${file.size} bytes, type: ${file.type})`);
          
          const response = await fetch('/api/knowledge/files', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${session.access_token}`
            },
            body: JSON.stringify(fileData)
          });
          
          if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`API upload failed with status: ${response.status}, ${errorText}`);
          }
          
          const data = await response.json();
          resolve(data.file);
        } catch (err) {
          console.error('Upload processing error:', err);
          reject(err);
        }
      };
      
      reader.onerror = () => {
        reject(new Error('Failed to read file'));
      };
      
      // Read file as data URL (base64)
      reader.readAsDataURL(file);
    });
  } catch (error) {
    console.error('Error uploading knowledge file:', error);
    throw error;
  }
};

/**
 * Delete a knowledge file - Use API only, no Supabase fallback due to schema cache issues
 */
export const deleteKnowledgeFile = async (fileId: string): Promise<void> => {
  try {
    const { data: { session } } = await supabase.auth.getSession();
    if (!session) throw new Error('Not authenticated');

    // Use API only
    const response = await fetch(`/api/knowledge/files/${fileId}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${session.access_token}`
      }
    });
    
    if (!response.ok) {
      throw new Error(`API delete failed with status: ${response.status}`);
    }
  } catch (error) {
    console.error('Error deleting knowledge file:', error);
    throw error;
  }
};

/**
 * Update a knowledge file (metadata only, not content) - Use API only, no Supabase fallback due to schema cache issues
 */
export const updateKnowledgeFile = async (
  fileId: string, 
  updates: { 
    file_name?: string; 
    category?: string; 
    tags?: string[] 
  }
): Promise<KnowledgeFile> => {
  try {
    const { data: { session } } = await supabase.auth.getSession();
    if (!session) throw new Error('Not authenticated');

    const updateData = {
      ...updates,
      tags: updates.tags ? JSON.stringify(updates.tags) : undefined,
      updated_at: new Date().toISOString()
    };

    // Use API only
    const response = await fetch(`/api/knowledge/files/${fileId}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${session.access_token}`
      },
      body: JSON.stringify(updateData)
    });
    
    if (!response.ok) {
      throw new Error(`API update failed with status: ${response.status}`);
    }
    
    const data = await response.json();
    return data.file;
  } catch (error) {
    console.error('Error updating knowledge file:', error);
    throw error;
  }
};

/**
 * Get all categories in the knowledge base - Use API only, no Supabase fallback due to schema cache issues
 */
export const getCategories = async (): Promise<KnowledgeCategory[]> => {
  try {
    const { data: { session } } = await supabase.auth.getSession();
    if (!session) throw new Error('Not authenticated');

    // Use API only
    const response = await fetch('/api/knowledge/files/categories', {
      headers: {
        'Authorization': `Bearer ${session.access_token}`
      }
    });
    
    if (!response.ok) {
      throw new Error(`API request failed with status: ${response.status}`);
    }
    
    const data = await response.json();
    return data.categories.map((name: string) => ({ name }));
  } catch (error) {
    console.error('Error fetching categories:', error);
    // Return empty array for better UX
    return [];
  }
};

/**
 * Get all tags in the knowledge base - Use API only, no Supabase fallback due to schema cache issues
 */
export const getTags = async (): Promise<KnowledgeTag[]> => {
  try {
    const { data: { session } } = await supabase.auth.getSession();
    if (!session) throw new Error('Not authenticated');

    // Use API only
    const response = await fetch('/api/knowledge/files/tags', {
      headers: {
        'Authorization': `Bearer ${session.access_token}`
      }
    });
    
    if (!response.ok) {
      throw new Error(`API request failed with status: ${response.status}`);
    }
    
    const data = await response.json();
    return data.tags.map((name: string) => ({ name }));
  } catch (error) {
    console.error('Error fetching tags:', error);
    // Return empty array for better UX
    return [];
  }
};

/**
 * Search in the knowledge base
 */
export const searchKnowledgeBase = async (
  query: string,
  options: {
    category?: string;
    fileType?: string;
    tags?: string[];
    includeSnippets?: boolean;
    limit?: number;
  } = {}
): Promise<KnowledgeSearchResult[]> => {
  try {
    const { data: { session } } = await supabase.auth.getSession();
    if (!session) throw new Error('Not authenticated');

    const { category, fileType, tags, includeSnippets = true, limit = 20 } = options;

    // Build query parameters
    const params = new URLSearchParams({ query });
    if (category) params.append('category', category);
    if (fileType) params.append('file_type', fileType);
    if (tags && tags.length > 0) params.append('tags', tags.join(','));
    if (includeSnippets) params.append('include_snippets', 'true');
    if (limit) params.append('limit', limit.toString());

    // API request (no fallback for search - requires backend processing)
    const response = await fetch(`/api/knowledge/search?${params.toString()}`, {
      headers: {
        'Authorization': `Bearer ${session.access_token}`
      }
    });
    
    if (!response.ok) {
      throw new Error(`Search failed: ${response.statusText}`);
    }
    
    const data = await response.json();
    return data.results || [];
  } catch (error) {
    console.error('Error searching knowledge base:', error);
    throw error;
  }
};

/**
 * Bulk delete knowledge files - Disable direct Supabase access due to schema cache issues
 * This now deletes files one by one using the API endpoint
 */
export const bulkDeleteKnowledgeFiles = async (fileIds: string[]): Promise<void> => {
  try {
    const { data: { session } } = await supabase.auth.getSession();
    if (!session) throw new Error('Not authenticated');

    // Delete files one by one using the API
    for (const fileId of fileIds) {
      await deleteKnowledgeFile(fileId);
    }
  } catch (error) {
    console.error('Error bulk deleting knowledge files:', error);
    throw error;
  }
};

/**
 * Bulk update knowledge files (e.g., change category or add tags) - Disable direct Supabase access due to schema cache issues
 * This now updates files one by one using the API endpoint
 */
export const bulkUpdateKnowledgeFiles = async (
  fileIds: string[],
  updates: {
    category?: string;
    tags?: string[];
    addTags?: string[]; // Tags to add to existing tags
  }
): Promise<void> => {
  try {
    const { data: { session } } = await supabase.auth.getSession();
    if (!session) throw new Error('Not authenticated');
    
    // Use the API endpoint to get and update files one by one
    for (const fileId of fileIds) {
      try {
        // If we need to add tags rather than replace them, first get the current file
        if (updates.addTags && updates.addTags.length > 0) {
          const file = await getKnowledgeFile(fileId);
          
          let currentTags = file.tags || [];
          if (typeof currentTags === 'string') {
            try {
              currentTags = JSON.parse(currentTags);
            } catch (e) {
              currentTags = [];
            }
          }
          
          // Combine current tags with new ones
          const newTags = [...new Set([...currentTags, ...updates.addTags])];
          
          // Update the file with the combined tags
          await updateKnowledgeFile(fileId, {
            ...updates,
            tags: newTags,
          });
        } else {
          // Simple update without tag merging
          await updateKnowledgeFile(fileId, updates);
        }
      } catch (err) {
        console.error(`Error updating file ${fileId}:`, err);
        // Continue with other files even if one fails
      }
    }
  } catch (error) {
    console.error('Error bulk updating knowledge files:', error);
    throw error;
  }
};