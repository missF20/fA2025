import { supabase } from '../lib/supabase';
import { 
  KnowledgeFile, 
  KnowledgeFileWithContent, 
  KnowledgeCategory, 
  KnowledgeTag, 
  KnowledgeSearchResult 
} from '../types';

/**
 * Fetch all knowledge files
 */
export const getKnowledgeFiles = async (limit = 20, offset = 0): Promise<{ files: KnowledgeFile[], total: number }> => {
  try {
    const { data: { session } } = await supabase.auth.getSession();
    if (!session) throw new Error('Not authenticated');

    // First try the API
    try {
      const response = await fetch(`/api/knowledge/files?limit=${limit}&offset=${offset}`, {
        headers: {
          'Authorization': `Bearer ${session.access_token}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        return data;
      }
    } catch (error) {
      console.warn('API request failed, falling back to direct Supabase', error);
    }

    // Fallback to direct Supabase
    const { data: files, error } = await supabase
      .from('knowledge_files')
      .select('id, user_id, file_name, file_size, file_type, category, tags, metadata, created_at, updated_at')
      .order('created_at', { ascending: false })
      .range(offset, offset + limit - 1);

    if (error) throw error;

    // Get total count
    const { count, error: countError } = await supabase
      .from('knowledge_files')
      .select('id', { count: 'exact', head: true });

    if (countError) throw countError;

    return { 
      files: files || [], 
      total: count || 0 
    };
  } catch (error) {
    console.error('Error fetching knowledge files:', error);
    throw error;
  }
};

/**
 * Get file details including content
 */
export const getKnowledgeFile = async (fileId: string): Promise<KnowledgeFileWithContent> => {
  try {
    const { data: { session } } = await supabase.auth.getSession();
    if (!session) throw new Error('Not authenticated');

    // Try API first
    try {
      const response = await fetch(`/api/knowledge/files/${fileId}`, {
        headers: {
          'Authorization': `Bearer ${session.access_token}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        return data.file;
      }
    } catch (error) {
      console.warn('API request failed, falling back to direct Supabase', error);
    }

    // Fallback to direct Supabase
    const { data, error } = await supabase
      .from('knowledge_files')
      .select('*')
      .eq('id', fileId)
      .single();

    if (error) throw error;
    
    // Parse metadata if it's a string
    let parsedMetadata = data.metadata;
    if (typeof data.metadata === 'string') {
      try {
        parsedMetadata = JSON.parse(data.metadata);
      } catch (e) {
        console.warn('Failed to parse metadata JSON', e);
      }
    }

    // Parse tags if it's a string
    let parsedTags = data.tags;
    if (typeof data.tags === 'string') {
      try {
        parsedTags = JSON.parse(data.tags);
      } catch (e) {
        console.warn('Failed to parse tags JSON', e);
      }
    }

    return {
      ...data,
      metadata: parsedMetadata,
      tags: parsedTags,
    } as KnowledgeFileWithContent;
  } catch (error) {
    console.error('Error fetching knowledge file details:', error);
    throw error;
  }
};

/**
 * Upload a new knowledge file
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

    // Read file as binary data
    const fileBuffer = await file.arrayBuffer();
    
    // First try API upload
    try {
      const fileData = {
        user_id: user.id,
        file_name: file.name,
        file_size: file.size,
        file_type: file.type,
        content: fileBuffer,
        category,
        tags
      };

      const response = await fetch('/api/knowledge/files/binary', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session.access_token}`
        },
        body: JSON.stringify(fileData)
      });

      if (response.ok) {
        const data = await response.json();
        return data.file;
      }
    } catch (error) {
      console.warn('API upload failed, falling back to direct Supabase', error);
    }

    // Fallback to direct Supabase
    const fileData = {
      user_id: user.id,
      file_name: file.name,
      file_size: file.size,
      file_type: file.type,
      content: fileBuffer,
      category,
      tags: tags ? JSON.stringify(tags) : null
    };

    const { data, error } = await supabase
      .from('knowledge_files')
      .insert(fileData)
      .select()
      .single();

    if (error) throw error;
    return data;
  } catch (error) {
    console.error('Error uploading knowledge file:', error);
    throw error;
  }
};

/**
 * Delete a knowledge file
 */
export const deleteKnowledgeFile = async (fileId: string): Promise<void> => {
  try {
    const { data: { session } } = await supabase.auth.getSession();
    if (!session) throw new Error('Not authenticated');

    // Try API first
    try {
      const response = await fetch(`/api/knowledge/files/${fileId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${session.access_token}`
        }
      });
      
      if (response.ok) {
        return;
      }
    } catch (error) {
      console.warn('API request failed, falling back to direct Supabase', error);
    }

    // Fallback to direct Supabase
    const { error } = await supabase
      .from('knowledge_files')
      .delete()
      .eq('id', fileId);

    if (error) throw error;
  } catch (error) {
    console.error('Error deleting knowledge file:', error);
    throw error;
  }
};

/**
 * Update a knowledge file (metadata only, not content)
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

    // Try API first
    try {
      const response = await fetch(`/api/knowledge/files/${fileId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session.access_token}`
        },
        body: JSON.stringify(updateData)
      });
      
      if (response.ok) {
        const data = await response.json();
        return data.file;
      }
    } catch (error) {
      console.warn('API request failed, falling back to direct Supabase', error);
    }

    // Fallback to direct Supabase
    const { data, error } = await supabase
      .from('knowledge_files')
      .update(updateData)
      .eq('id', fileId)
      .select()
      .single();

    if (error) throw error;
    return data;
  } catch (error) {
    console.error('Error updating knowledge file:', error);
    throw error;
  }
};

/**
 * Get all categories in the knowledge base
 */
export const getCategories = async (): Promise<KnowledgeCategory[]> => {
  try {
    const { data: { session } } = await supabase.auth.getSession();
    if (!session) throw new Error('Not authenticated');

    // Try API first
    try {
      const response = await fetch('/api/knowledge/files/categories', {
        headers: {
          'Authorization': `Bearer ${session.access_token}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        return data.categories.map((name: string) => ({ name }));
      }
    } catch (error) {
      console.warn('API request failed, falling back to direct Supabase', error);
    }

    // Fallback to direct Supabase
    const { data, error } = await supabase
      .from('knowledge_files')
      .select('category');

    if (error) throw error;

    // Extract unique categories and count occurrences
    const categoryCounts: Record<string, number> = {};
    data.forEach(item => {
      if (item.category) {
        categoryCounts[item.category] = (categoryCounts[item.category] || 0) + 1;
      }
    });

    return Object.entries(categoryCounts)
      .map(([name, count]) => ({ name, count }))
      .sort((a, b) => a.name.localeCompare(b.name));
  } catch (error) {
    console.error('Error fetching categories:', error);
    return [];
  }
};

/**
 * Get all tags in the knowledge base
 */
export const getTags = async (): Promise<KnowledgeTag[]> => {
  try {
    const { data: { session } } = await supabase.auth.getSession();
    if (!session) throw new Error('Not authenticated');

    // Try API first
    try {
      const response = await fetch('/api/knowledge/files/tags', {
        headers: {
          'Authorization': `Bearer ${session.access_token}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        return data.tags.map((name: string) => ({ name }));
      }
    } catch (error) {
      console.warn('API request failed, falling back to direct Supabase', error);
    }

    // Fallback to direct Supabase
    const { data, error } = await supabase
      .from('knowledge_files')
      .select('tags');

    if (error) throw error;

    // Extract unique tags and count occurrences
    const tagCounts: Record<string, number> = {};
    data.forEach(item => {
      if (item.tags) {
        const tags = typeof item.tags === 'string' 
          ? JSON.parse(item.tags) 
          : item.tags;
        
        if (Array.isArray(tags)) {
          tags.forEach(tag => {
            tagCounts[tag] = (tagCounts[tag] || 0) + 1;
          });
        }
      }
    });

    return Object.entries(tagCounts)
      .map(([name, count]) => ({ name, count }))
      .sort((a, b) => a.name.localeCompare(b.name));
  } catch (error) {
    console.error('Error fetching tags:', error);
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
 * Bulk delete knowledge files
 */
export const bulkDeleteKnowledgeFiles = async (fileIds: string[]): Promise<void> => {
  try {
    const { data: { session } } = await supabase.auth.getSession();
    if (!session) throw new Error('Not authenticated');

    // Since there's no API for bulk deletion, use Supabase directly
    const { error } = await supabase
      .from('knowledge_files')
      .delete()
      .in('id', fileIds);

    if (error) throw error;
  } catch (error) {
    console.error('Error bulk deleting knowledge files:', error);
    throw error;
  }
};

/**
 * Bulk update knowledge files (e.g., change category or add tags)
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
    
    // If we need to add tags rather than replace them, we need to fetch files first
    if (updates.addTags && updates.addTags.length > 0) {
      // Get current files
      const { data: files, error: fetchError } = await supabase
        .from('knowledge_files')
        .select('id, tags')
        .in('id', fileIds);

      if (fetchError) throw fetchError;

      // Update each file individually to preserve existing tags
      for (const file of files) {
        const currentTags = typeof file.tags === 'string'
          ? JSON.parse(file.tags || '[]')
          : file.tags || [];
          
        const newTags = [...new Set([...currentTags, ...updates.addTags])];
        
        await supabase
          .from('knowledge_files')
          .update({ 
            tags: JSON.stringify(newTags),
            updated_at: new Date().toISOString()
          })
          .eq('id', file.id);
      }
      return;
    }
    
    // Simple bulk update without needing to merge tags
    const updateData = {
      ...(updates.category ? { category: updates.category } : {}),
      ...(updates.tags ? { tags: JSON.stringify(updates.tags) } : {}),
      updated_at: new Date().toISOString()
    };
    
    // Update all files
    const { error } = await supabase
      .from('knowledge_files')
      .update(updateData)
      .in('id', fileIds);

    if (error) throw error;
  } catch (error) {
    console.error('Error bulk updating knowledge files:', error);
    throw error;
  }
};