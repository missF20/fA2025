import React, { useState, useEffect } from 'react';
import { Folder, Check, X, Plus, Loader2 } from 'lucide-react';
import { KnowledgeCategory, KnowledgeFile } from '../types';
import { getCategories, updateKnowledgeFile } from '../services/knowledgeService';

interface KnowledgeCategorySelectorProps {
  file: KnowledgeFile;
  onUpdate: (updatedFile: KnowledgeFile) => void;
}

export function KnowledgeCategorySelector({ file, onUpdate }: KnowledgeCategorySelectorProps) {
  const [categories, setCategories] = useState<KnowledgeCategory[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string>(file.category || '');
  const [newCategory, setNewCategory] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [isAddingNew, setIsAddingNew] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  // Load available categories
  useEffect(() => {
    const loadCategories = async () => {
      try {
        setIsLoading(true);
        const categoriesData = await getCategories();
        setCategories(categoriesData);
      } catch (err) {
        console.error('Error loading categories:', err);
      } finally {
        setIsLoading(false);
      }
    };

    loadCategories();
  }, []);

  // Save category changes
  const saveCategory = async () => {
    try {
      setIsSaving(true);
      
      // Determine which category to save
      const categoryToSave = isAddingNew ? newCategory.trim() : selectedCategory;
      
      // Skip if empty category and we're not explicitly trying to remove a category
      if (!categoryToSave && !(!isAddingNew && selectedCategory !== file.category)) {
        setIsEditing(false);
        setIsAddingNew(false);
        return;
      }
      
      const updatedFile = await updateKnowledgeFile(file.id, {
        category: categoryToSave || null
      });
      
      onUpdate(updatedFile);
      setIsEditing(false);
      setIsAddingNew(false);
      setNewCategory('');
    } catch (err) {
      console.error('Error saving category:', err);
    } finally {
      setIsSaving(false);
    }
  };

  // Cancel editing
  const cancelEditing = () => {
    setSelectedCategory(file.category || '');
    setIsEditing(false);
    setIsAddingNew(false);
    setNewCategory('');
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-4">
        <Loader2 size={20} className="animate-spin text-blue-500 mr-2" />
        <span className="text-sm text-gray-600">Loading categories...</span>
      </div>
    );
  }

  // Display mode
  if (!isEditing) {
    return (
      <div className="space-y-2">
        <div className="flex justify-between items-center">
          <h3 className="text-sm font-medium text-gray-700 flex items-center">
            <Folder size={16} className="mr-1 text-blue-500" /> Category
          </h3>
          <button
            onClick={() => setIsEditing(true)}
            className="text-xs text-blue-600 hover:text-blue-800"
          >
            Change
          </button>
        </div>
        
        {file.category ? (
          <div className="bg-blue-50 text-blue-700 text-sm px-3 py-1 rounded inline-flex items-center">
            <Folder size={14} className="mr-1" />
            {file.category}
          </div>
        ) : (
          <span className="text-sm text-gray-500 italic">No category</span>
        )}
      </div>
    );
  }

  // Adding new category mode
  if (isAddingNew) {
    return (
      <div className="space-y-3 p-3 border border-gray-200 rounded-lg bg-gray-50">
        <div className="flex justify-between items-center">
          <h3 className="text-sm font-medium text-gray-700 flex items-center">
            <Folder size={16} className="mr-1 text-blue-500" /> Add New Category
          </h3>
        </div>

        <div className="flex items-center">
          <input
            type="text"
            value={newCategory}
            onChange={e => setNewCategory(e.target.value)}
            placeholder="Enter category name..."
            className="flex-grow px-3 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            autoFocus
          />
        </div>

        <div className="flex justify-end space-x-2">
          <button
            onClick={() => {
              setIsAddingNew(false);
              setNewCategory('');
            }}
            disabled={isSaving}
            className="px-3 py-1 text-sm text-gray-700 bg-gray-200 rounded hover:bg-gray-300 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            onClick={saveCategory}
            disabled={isSaving || !newCategory.trim()}
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

  // Edit mode (selecting from existing categories)
  return (
    <div className="space-y-3 p-3 border border-gray-200 rounded-lg bg-gray-50">
      <div className="flex justify-between items-center">
        <h3 className="text-sm font-medium text-gray-700 flex items-center">
          <Folder size={16} className="mr-1 text-blue-500" /> Select Category
        </h3>
      </div>

      <div className="flex flex-wrap gap-2">
        {/* No category option */}
        <button
          onClick={() => setSelectedCategory('')}
          className={`text-xs px-3 py-1 rounded-full flex items-center ${
            selectedCategory === ''
              ? 'bg-blue-100 text-blue-800 font-medium'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          {selectedCategory === '' && <Check size={12} className="mr-1" />}
          No Category
        </button>
        
        {/* Existing categories */}
        {categories.map(category => (
          <button
            key={category.name}
            onClick={() => setSelectedCategory(category.name)}
            className={`text-xs px-3 py-1 rounded-full flex items-center ${
              selectedCategory === category.name
                ? 'bg-blue-100 text-blue-800 font-medium'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            {selectedCategory === category.name && <Check size={12} className="mr-1" />}
            {category.name}
            {category.count && <span className="ml-1 text-gray-500">({category.count})</span>}
          </button>
        ))}
        
        {/* Add new category button */}
        <button
          onClick={() => setIsAddingNew(true)}
          className="bg-green-50 text-green-700 hover:bg-green-100 text-xs px-3 py-1 rounded-full flex items-center"
        >
          <Plus size={12} className="mr-1" />
          Add New
        </button>
      </div>

      <div className="flex justify-end space-x-2">
        <button
          onClick={cancelEditing}
          disabled={isSaving}
          className="px-3 py-1 text-sm text-gray-700 bg-gray-200 rounded hover:bg-gray-300 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 disabled:opacity-50"
        >
          Cancel
        </button>
        <button
          onClick={saveCategory}
          disabled={isSaving || selectedCategory === file.category}
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