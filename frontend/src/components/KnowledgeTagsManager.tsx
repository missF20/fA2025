import React, { useState, useEffect } from 'react';
import { Tag, X, Plus, Check, Loader2 } from 'lucide-react';
import { KnowledgeFile, KnowledgeTag } from '../types';
import { getTags, updateKnowledgeFile } from '../services/knowledgeService';

interface KnowledgeTagsManagerProps {
  file: KnowledgeFile;
  onUpdate: (updatedFile: KnowledgeFile) => void;
}

export function KnowledgeTagsManager({ file, onUpdate }: KnowledgeTagsManagerProps) {
  const [availableTags, setAvailableTags] = useState<KnowledgeTag[]>([]);
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [newTag, setNewTag] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  // Initialize selected tags from file
  useEffect(() => {
    const initTags = () => {
      if (!file.tags) {
        setSelectedTags([]);
        return;
      }

      let tags: string[] = [];
      if (typeof file.tags === 'string') {
        try {
          tags = JSON.parse(file.tags);
        } catch (e) {
          tags = [file.tags];
        }
      } else if (Array.isArray(file.tags)) {
        tags = file.tags;
      }

      setSelectedTags(tags);
    };

    initTags();
  }, [file.tags]);

  // Load available tags
  useEffect(() => {
    const loadTags = async () => {
      try {
        setIsLoading(true);
        const tagsData = await getTags();
        setAvailableTags(tagsData);
      } catch (err) {
        console.error('Error loading tags:', err);
      } finally {
        setIsLoading(false);
      }
    };

    loadTags();
  }, []);

  // Toggle tag selection
  const toggleTag = (tag: string) => {
    if (selectedTags.includes(tag)) {
      setSelectedTags(selectedTags.filter(t => t !== tag));
    } else {
      setSelectedTags([...selectedTags, tag]);
    }
  };

  // Add a new tag
  const addNewTag = () => {
    if (!newTag.trim()) return;
    
    // Check if tag already exists
    if (selectedTags.includes(newTag.trim())) {
      setNewTag('');
      return;
    }
    
    setSelectedTags([...selectedTags, newTag.trim()]);
    setNewTag('');
  };

  // Save changes
  const saveChanges = async () => {
    try {
      setIsSaving(true);
      const updatedFile = await updateKnowledgeFile(file.id, {
        tags: selectedTags
      });
      onUpdate(updatedFile);
      setIsEditing(false);
    } catch (err) {
      console.error('Error saving tags:', err);
    } finally {
      setIsSaving(false);
    }
  };

  // Cancel editing
  const cancelEditing = () => {
    // Reset to original tags
    const originalTags = typeof file.tags === 'string'
      ? JSON.parse(file.tags || '[]')
      : file.tags || [];
      
    setSelectedTags(Array.isArray(originalTags) ? originalTags : []);
    setIsEditing(false);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-4">
        <Loader2 size={20} className="animate-spin text-blue-500 mr-2" />
        <span className="text-sm text-gray-600">Loading tags...</span>
      </div>
    );
  }

  // Display mode
  if (!isEditing) {
    return (
      <div className="space-y-2">
        <div className="flex justify-between items-center">
          <h3 className="text-sm font-medium text-gray-700 flex items-center">
            <Tag size={16} className="mr-1 text-blue-500" /> Tags
          </h3>
          <button
            onClick={() => setIsEditing(true)}
            className="text-xs text-blue-600 hover:text-blue-800"
          >
            Edit Tags
          </button>
        </div>
        
        <div className="flex flex-wrap gap-2">
          {selectedTags.length === 0 ? (
            <span className="text-sm text-gray-500 italic">No tags</span>
          ) : (
            selectedTags.map((tag, index) => (
              <span
                key={index}
                className="bg-blue-50 text-blue-700 text-xs px-2 py-1 rounded-full flex items-center"
              >
                {tag}
              </span>
            ))
          )}
        </div>
      </div>
    );
  }

  // Edit mode
  return (
    <div className="space-y-3 p-3 border border-gray-200 rounded-lg bg-gray-50">
      <div className="flex justify-between items-center">
        <h3 className="text-sm font-medium text-gray-700 flex items-center">
          <Tag size={16} className="mr-1 text-blue-500" /> Edit Tags
        </h3>
      </div>

      {/* Selected tags */}
      <div className="flex flex-wrap gap-2">
        {selectedTags.length === 0 ? (
          <span className="text-sm text-gray-500 italic">No tags selected</span>
        ) : (
          selectedTags.map((tag, index) => (
            <span
              key={index}
              className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded-full flex items-center"
            >
              {tag}
              <button
                onClick={() => toggleTag(tag)}
                className="ml-1 text-blue-600 hover:text-blue-800"
              >
                <X size={12} />
              </button>
            </span>
          ))
        )}
      </div>

      {/* Add new tag */}
      <div className="flex items-center">
        <input
          type="text"
          value={newTag}
          onChange={e => setNewTag(e.target.value)}
          onKeyDown={e => {
            if (e.key === 'Enter') {
              e.preventDefault();
              addNewTag();
            }
          }}
          placeholder="Add a new tag..."
          className="flex-grow px-3 py-1 text-sm border border-gray-300 rounded-l focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        />
        <button
          onClick={addNewTag}
          disabled={!newTag.trim()}
          className="px-3 py-1 text-sm bg-blue-600 text-white rounded-r hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:bg-blue-300"
        >
          <Plus size={16} />
        </button>
      </div>

      {/* Available tags */}
      <div>
        <h4 className="text-xs font-medium text-gray-600 mb-1">Available Tags</h4>
        <div className="flex flex-wrap gap-2 max-h-32 overflow-y-auto p-2 bg-white rounded border border-gray-200">
          {availableTags.length === 0 ? (
            <span className="text-sm text-gray-500 italic">No tags available</span>
          ) : (
            availableTags
              .filter(tag => !selectedTags.includes(tag.name))
              .map(tag => (
                <button
                  key={tag.name}
                  onClick={() => toggleTag(tag.name)}
                  className="bg-gray-100 text-gray-700 hover:bg-blue-50 hover:text-blue-700 text-xs px-2 py-1 rounded-full flex items-center"
                >
                  {tag.name}
                  {tag.count && <span className="ml-1 text-gray-500">({tag.count})</span>}
                </button>
              ))
          )}
        </div>
      </div>

      {/* Action buttons */}
      <div className="flex justify-end space-x-2">
        <button
          onClick={cancelEditing}
          disabled={isSaving}
          className="px-3 py-1 text-sm text-gray-700 bg-gray-200 rounded hover:bg-gray-300 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 disabled:opacity-50"
        >
          Cancel
        </button>
        <button
          onClick={saveChanges}
          disabled={isSaving}
          className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 flex items-center"
        >
          {isSaving ? (
            <>
              <Loader2 size={12} className="animate-spin mr-1" />
              Saving...
            </>
          ) : (
            <>
              <Check size={12} className="mr-1" />
              Save
            </>
          )}
        </button>
      </div>
    </div>
  );
}