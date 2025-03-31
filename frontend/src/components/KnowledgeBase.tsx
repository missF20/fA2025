import React, { useState, useEffect, useRef } from 'react';
import { 
  FileText, Folder, Tag, Upload, Search, Trash2, Filter,
  PlusCircle, Loader2, AlertCircle, X, CheckCircle, 
  RefreshCw, Download, Edit
} from 'lucide-react';
import { 
  KnowledgeFile, 
  KnowledgeCategory, 
  KnowledgeTag
} from '../types';
import { 
  getKnowledgeFiles, 
  uploadKnowledgeFile, 
  deleteKnowledgeFile,
  bulkDeleteKnowledgeFiles,
  getCategories,
  getTags,
  bulkUpdateKnowledgeFiles
} from '../services/knowledgeService';
import { KnowledgeFilePreview } from './KnowledgeFilePreview';
import { KnowledgeSearch } from './KnowledgeSearch';
import { KnowledgeTagsManager } from './KnowledgeTagsManager';
import { KnowledgeCategorySelector } from './KnowledgeCategorySelector';

const PAGE_SIZE = 10;

export function KnowledgeBase() {
  // State for file listing
  const [files, setFiles] = useState<KnowledgeFile[]>([]);
  const [totalFiles, setTotalFiles] = useState(0);
  const [currentPage, setCurrentPage] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // State for file operations
  const [selectedFiles, setSelectedFiles] = useState<string[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadError, setUploadError] = useState<string | null>(null);
  
  // State for filters
  const [categories, setCategories] = useState<KnowledgeCategory[]>([]);
  const [tags, setTags] = useState<KnowledgeTag[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string | undefined>(undefined);
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [filterOpen, setFilterOpen] = useState(false);
  
  // State for file preview and search
  const [previewFileId, setPreviewFileId] = useState<string | null>(null);
  const [searchMode, setSearchMode] = useState(false);
  const [currentView, setCurrentView] = useState<'list' | 'grid'>('list');
  
  // State for bulk operations
  const [bulkActionOpen, setBulkActionOpen] = useState(false);
  const [bulkProcessing, setBulkProcessing] = useState(false);
  
  // Refs
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Load files, categories, and tags
  useEffect(() => {
    fetchFiles();
    fetchFilters();
  }, [currentPage, selectedCategory, selectedTags]);

  const fetchFiles = async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      const offset = currentPage * PAGE_SIZE;
      const { files: fetchedFiles, total } = await getKnowledgeFiles(PAGE_SIZE, offset);
      
      // Apply client-side filtering if needed
      let filteredFiles = fetchedFiles;
      
      // Filter by category
      if (selectedCategory) {
        filteredFiles = filteredFiles.filter(file => file.category === selectedCategory);
      }
      
      // Filter by tags
      if (selectedTags.length > 0) {
        filteredFiles = filteredFiles.filter(file => {
          const fileTags = typeof file.tags === 'string'
            ? JSON.parse(file.tags || '[]')
            : file.tags || [];
            
          return selectedTags.some(tag => 
            Array.isArray(fileTags) && fileTags.includes(tag)
          );
        });
      }
      
      setFiles(filteredFiles);
      setTotalFiles(total);
    } catch (err) {
      console.error('Error fetching files:', err);
      setError('Failed to load files. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const fetchFilters = async () => {
    try {
      const [categoriesData, tagsData] = await Promise.all([
        getCategories(),
        getTags()
      ]);
      
      setCategories(categoriesData);
      setTags(tagsData);
    } catch (err) {
      console.error('Error fetching filters:', err);
    }
  };

  // Handle file upload
  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (!files || files.length === 0) return;
    
    setIsUploading(true);
    setUploadProgress(0);
    setUploadError(null);
    
    try {
      // Process each file
      for (let i = 0; i < files.length; i++) {
        const file = files[i];
        await uploadKnowledgeFile(file, selectedCategory, selectedTags);
        
        // Update progress
        setUploadProgress(Math.round(((i + 1) / files.length) * 100));
      }
      
      // Refresh file list
      fetchFiles();
    } catch (err) {
      console.error('Upload error:', err);
      setUploadError('Failed to upload one or more files. Please try again.');
    } finally {
      setIsUploading(false);
      setUploadProgress(0);
      
      // Reset file input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  // Handle file deletion
  const handleDeleteFile = async (fileId: string) => {
    if (!confirm('Are you sure you want to delete this file?')) return;
    
    try {
      await deleteKnowledgeFile(fileId);
      setFiles(files.filter(file => file.id !== fileId));
      setTotalFiles(prev => prev - 1);
    } catch (err) {
      console.error('Error deleting file:', err);
      alert('Failed to delete the file. Please try again.');
    }
  };

  // Handle bulk file deletion
  const handleBulkDelete = async () => {
    if (selectedFiles.length === 0) return;
    
    if (!confirm(`Are you sure you want to delete ${selectedFiles.length} files?`)) {
      setBulkActionOpen(false);
      return;
    }
    
    try {
      setBulkProcessing(true);
      await bulkDeleteKnowledgeFiles(selectedFiles);
      
      // Refresh file list
      fetchFiles();
      setSelectedFiles([]);
    } catch (err) {
      console.error('Error bulk deleting files:', err);
      alert('Failed to delete some files. Please try again.');
    } finally {
      setBulkProcessing(false);
      setBulkActionOpen(false);
    }
  };

  // Handle bulk category update
  const handleBulkCategoryUpdate = async (category: string) => {
    if (selectedFiles.length === 0) return;
    
    try {
      setBulkProcessing(true);
      await bulkUpdateKnowledgeFiles(selectedFiles, { category });
      
      // Refresh file list
      fetchFiles();
      setSelectedFiles([]);
    } catch (err) {
      console.error('Error updating categories:', err);
      alert('Failed to update categories. Please try again.');
    } finally {
      setBulkProcessing(false);
      setBulkActionOpen(false);
    }
  };

  // Handle bulk tag addition
  const handleBulkAddTags = async (tagsToAdd: string[]) => {
    if (selectedFiles.length === 0 || tagsToAdd.length === 0) return;
    
    try {
      setBulkProcessing(true);
      await bulkUpdateKnowledgeFiles(selectedFiles, { addTags: tagsToAdd });
      
      // Refresh file list
      fetchFiles();
      setSelectedFiles([]);
    } catch (err) {
      console.error('Error adding tags:', err);
      alert('Failed to add tags. Please try again.');
    } finally {
      setBulkProcessing(false);
      setBulkActionOpen(false);
    }
  };

  // Toggle file selection
  const toggleFileSelection = (fileId: string) => {
    if (selectedFiles.includes(fileId)) {
      setSelectedFiles(selectedFiles.filter(id => id !== fileId));
    } else {
      setSelectedFiles([...selectedFiles, fileId]);
    }
  };

  // Toggle select all files
  const toggleSelectAll = () => {
    if (selectedFiles.length === files.length) {
      setSelectedFiles([]);
    } else {
      setSelectedFiles(files.map(file => file.id));
    }
  };

  // File type icon mapping
  const getFileIcon = (fileType: string) => {
    if (fileType.includes('pdf')) return '📄';
    if (fileType.includes('word') || fileType.includes('docx')) return '📝';
    if (fileType.includes('text/plain')) return '📃';
    if (fileType.includes('html')) return '🌐';
    return '📋';
  };

  // Format file size
  const formatFileSize = (sizeInBytes: number) => {
    if (sizeInBytes < 1024) return `${sizeInBytes} B`;
    if (sizeInBytes < 1024 * 1024) return `${(sizeInBytes / 1024).toFixed(1)} KB`;
    return `${(sizeInBytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  // Format date
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  // Get tags display
  const getFileTags = (file: KnowledgeFile) => {
    if (!file.tags) return [];
    
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
    
    return tags;
  };

  // Handle file update
  const handleFileUpdate = (updatedFile: KnowledgeFile) => {
    setFiles(files.map(file => 
      file.id === updatedFile.id ? updatedFile : file
    ));
  };

  // Render toolbar
  const renderToolbar = () => (
    <div className="flex flex-wrap justify-between items-center mb-4 gap-2">
      <div className="flex items-center space-x-2">
        <h2 className="text-lg font-bold text-gray-800">Knowledge Base</h2>
        {isLoading && <Loader2 size={18} className="animate-spin text-blue-500" />}
      </div>
      
      <div className="flex items-center space-x-2">
        <button
          onClick={() => setSearchMode(!searchMode)}
          className={`p-2 rounded-md ${
            searchMode ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
          title={searchMode ? 'Back to file list' : 'Search knowledge base'}
        >
          <Search size={18} />
        </button>
        
        <button
          onClick={() => setFilterOpen(!filterOpen)}
          className={`p-2 rounded-md ${
            filterOpen ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
          title="Filter files"
        >
          <Filter size={18} />
        </button>
        
        <button
          onClick={() => setCurrentView(currentView === 'list' ? 'grid' : 'list')}
          className="p-2 rounded-md bg-gray-100 text-gray-700 hover:bg-gray-200"
          title={`Switch to ${currentView === 'list' ? 'grid' : 'list'} view`}
        >
          {currentView === 'list' ? (
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <rect x="3" y="3" width="7" height="7" />
              <rect x="14" y="3" width="7" height="7" />
              <rect x="14" y="14" width="7" height="7" />
              <rect x="3" y="14" width="7" height="7" />
            </svg>
          ) : (
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="21" y1="6" x2="3" y2="6" />
              <line x1="21" y1="12" x2="3" y2="12" />
              <line x1="21" y1="18" x2="3" y2="18" />
            </svg>
          )}
        </button>
        
        <button
          onClick={() => fetchFiles()}
          className="p-2 rounded-md bg-gray-100 text-gray-700 hover:bg-gray-200"
          title="Refresh files"
          disabled={isLoading}
        >
          <RefreshCw size={18} className={isLoading ? 'animate-spin' : ''} />
        </button>
        
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileUpload}
          className="hidden"
          multiple
        />
        
        <button
          onClick={() => fileInputRef.current?.click()}
          className="px-3 py-2 flex items-center rounded-md bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50"
          disabled={isUploading}
        >
          {isUploading ? (
            <>
              <Loader2 size={16} className="animate-spin mr-2" />
              Uploading... {uploadProgress}%
            </>
          ) : (
            <>
              <Upload size={16} className="mr-2" />
              Upload Files
            </>
          )}
        </button>
      </div>
    </div>
  );

  // Render filters
  const renderFilters = () => {
    if (!filterOpen) return null;
    
    return (
      <div className="mb-4 p-4 border border-gray-200 rounded-lg bg-gray-50">
        <div className="flex justify-between items-center mb-3">
          <h3 className="text-sm font-medium text-gray-700">Filters</h3>
          <button
            onClick={() => {
              setSelectedCategory(undefined);
              setSelectedTags([]);
            }}
            className="text-xs text-blue-600 hover:text-blue-800"
          >
            Clear all
          </button>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Category filter */}
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">
              Category
            </label>
            <select
              value={selectedCategory || ''}
              onChange={(e) => setSelectedCategory(e.target.value || undefined)}
              className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 text-sm"
            >
              <option value="">All Categories</option>
              {categories.map((category) => (
                <option key={category.name} value={category.name}>
                  {category.name} {category.count ? `(${category.count})` : ''}
                </option>
              ))}
            </select>
          </div>
          
          {/* Tags filter */}
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">
              Tags
            </label>
            <div className="flex flex-wrap gap-2 p-2 border border-gray-300 rounded-md bg-white max-h-24 overflow-y-auto">
              {tags.length === 0 ? (
                <span className="text-sm text-gray-500">No tags available</span>
              ) : (
                tags.map((tag) => (
                  <button
                    key={tag.name}
                    onClick={() => {
                      if (selectedTags.includes(tag.name)) {
                        setSelectedTags(selectedTags.filter(t => t !== tag.name));
                      } else {
                        setSelectedTags([...selectedTags, tag.name]);
                      }
                    }}
                    className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium ${
                      selectedTags.includes(tag.name)
                        ? 'bg-blue-100 text-blue-800'
                        : 'bg-gray-100 text-gray-800 hover:bg-gray-200'
                    }`}
                    type="button"
                  >
                    {tag.name}
                    {tag.count && <span className="ml-1 text-gray-500">({tag.count})</span>}
                  </button>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    );
  };

  // Render bulk action menu
  const renderBulkActionMenu = () => {
    if (!bulkActionOpen || selectedFiles.length === 0) return null;
    
    return (
      <div className="absolute right-0 mt-2 w-56 rounded-md shadow-lg bg-white ring-1 ring-black ring-opacity-5 z-10">
        <div className="py-1" role="menu" aria-orientation="vertical">
          {/* Category bulk actions */}
          <div className="px-4 py-2 text-xs text-gray-500">
            Set Category:
          </div>
          {categories.map(category => (
            <button
              key={category.name}
              onClick={() => handleBulkCategoryUpdate(category.name)}
              className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
              role="menuitem"
              disabled={bulkProcessing}
            >
              <Folder size={12} className="inline mr-2" />
              {category.name}
            </button>
          ))}
          <button
            onClick={() => handleBulkCategoryUpdate('')}
            className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
            role="menuitem"
            disabled={bulkProcessing}
          >
            <X size={12} className="inline mr-2" />
            No Category
          </button>
          
          <hr className="my-1" />
          
          {/* Tag bulk actions */}
          <div className="px-4 py-2 text-xs text-gray-500">
            Add Tags:
          </div>
          {tags.slice(0, 5).map(tag => (
            <button
              key={tag.name}
              onClick={() => handleBulkAddTags([tag.name])}
              className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
              role="menuitem"
              disabled={bulkProcessing}
            >
              <Tag size={12} className="inline mr-2" />
              {tag.name}
            </button>
          ))}
          
          <hr className="my-1" />
          
          {/* Delete action */}
          <button
            onClick={handleBulkDelete}
            className="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50"
            role="menuitem"
            disabled={bulkProcessing}
          >
            <Trash2 size={12} className="inline mr-2" />
            Delete Selected
          </button>
        </div>
      </div>
    );
  };

  // Render grid view
  const renderGridView = () => (
    <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
      {files.map(file => (
        <div
          key={file.id}
          className={`relative p-4 border rounded-lg overflow-hidden transition-colors hover:border-blue-300 cursor-pointer ${
            selectedFiles.includes(file.id) ? 'border-blue-500 bg-blue-50' : 'border-gray-200'
          }`}
          onClick={() => toggleFileSelection(file.id)}
        >
          {/* Checkbox for selection */}
          <div className="absolute top-2 left-2">
            <input
              type="checkbox"
              checked={selectedFiles.includes(file.id)}
              onChange={() => toggleFileSelection(file.id)}
              onClick={e => e.stopPropagation()}
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
            />
          </div>
          
          {/* File icon and info */}
          <div className="flex flex-col items-center pt-4">
            <div className="text-3xl mb-2">{getFileIcon(file.file_type)}</div>
            <h3 className="text-sm font-medium text-center line-clamp-2" title={file.file_name}>
              {file.file_name}
            </h3>
            <div className="mt-2 text-xs text-gray-500">
              {formatFileSize(file.file_size)}
            </div>
            
            {/* Tags */}
            <div className="mt-2 flex flex-wrap justify-center gap-1">
              {getFileTags(file).slice(0, 3).map((tag, index) => (
                <span
                  key={index}
                  className="inline-flex items-center px-2 py-0.5 rounded-full text-xs bg-gray-100 text-gray-800"
                >
                  {tag}
                </span>
              ))}
              {getFileTags(file).length > 3 && (
                <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs bg-gray-100 text-gray-600">
                  +{getFileTags(file).length - 3}
                </span>
              )}
            </div>
          </div>
          
          {/* Actions */}
          <div className="absolute top-2 right-2 flex space-x-1">
            <button
              onClick={e => {
                e.stopPropagation();
                setPreviewFileId(file.id);
              }}
              className="text-gray-500 hover:text-blue-600 p-1"
              title="Preview file"
            >
              <FileText size={16} />
            </button>
            <button
              onClick={e => {
                e.stopPropagation();
                handleDeleteFile(file.id);
              }}
              className="text-gray-500 hover:text-red-600 p-1"
              title="Delete file"
            >
              <Trash2 size={16} />
            </button>
          </div>
        </div>
      ))}
    </div>
  );

  // Render list view
  const renderListView = () => (
    <div className="overflow-x-auto border border-gray-200 rounded-lg">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th scope="col" className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              <input
                type="checkbox"
                checked={selectedFiles.length === files.length && files.length > 0}
                onChange={toggleSelectAll}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
            </th>
            <th scope="col" className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Name
            </th>
            <th scope="col" className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Type
            </th>
            <th scope="col" className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Category
            </th>
            <th scope="col" className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Tags
            </th>
            <th scope="col" className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Size
            </th>
            <th scope="col" className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Uploaded
            </th>
            <th scope="col" className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Actions
            </th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {files.map(file => (
            <tr 
              key={file.id}
              className={selectedFiles.includes(file.id) ? 'bg-blue-50' : 'hover:bg-gray-50'}
              onClick={() => toggleFileSelection(file.id)}
            >
              <td className="px-3 py-4 whitespace-nowrap">
                <input
                  type="checkbox"
                  checked={selectedFiles.includes(file.id)}
                  onChange={() => toggleFileSelection(file.id)}
                  onClick={e => e.stopPropagation()}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
              </td>
              <td className="px-3 py-4 whitespace-nowrap">
                <div className="flex items-center">
                  <span className="mr-2">{getFileIcon(file.file_type)}</span>
                  <span className="text-sm font-medium text-gray-900 truncate max-w-[200px]" title={file.file_name}>
                    {file.file_name}
                  </span>
                </div>
              </td>
              <td className="px-3 py-4 whitespace-nowrap text-sm text-gray-500">
                {file.file_type.split('/').pop()?.toUpperCase()}
              </td>
              <td className="px-3 py-4 whitespace-nowrap text-sm text-gray-500">
                {file.category ? (
                  <span className="px-2 py-1 text-xs rounded-full bg-blue-100 text-blue-800">
                    {file.category}
                  </span>
                ) : (
                  <span className="text-gray-400">—</span>
                )}
              </td>
              <td className="px-3 py-4 whitespace-nowrap">
                <div className="flex flex-wrap gap-1 max-w-[200px]">
                  {getFileTags(file).slice(0, 2).map((tag, index) => (
                    <span
                      key={index}
                      className="inline-flex items-center px-2 py-0.5 rounded-full text-xs bg-gray-100 text-gray-800"
                    >
                      {tag}
                    </span>
                  ))}
                  {getFileTags(file).length > 2 && (
                    <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs bg-gray-100 text-gray-600">
                      +{getFileTags(file).length - 2}
                    </span>
                  )}
                </div>
              </td>
              <td className="px-3 py-4 whitespace-nowrap text-sm text-gray-500">
                {formatFileSize(file.file_size)}
              </td>
              <td className="px-3 py-4 whitespace-nowrap text-sm text-gray-500">
                {formatDate(file.created_at)}
              </td>
              <td className="px-3 py-4 whitespace-nowrap text-sm text-gray-500">
                <div className="flex space-x-2" onClick={e => e.stopPropagation()}>
                  <button
                    onClick={() => setPreviewFileId(file.id)}
                    className="text-gray-500 hover:text-blue-600"
                    title="Preview file"
                  >
                    <FileText size={16} />
                  </button>
                  <button
                    onClick={() => handleDeleteFile(file.id)}
                    className="text-gray-500 hover:text-red-600"
                    title="Delete file"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );

  // Render pagination
  const renderPagination = () => {
    const totalPages = Math.ceil(totalFiles / PAGE_SIZE);
    if (totalPages <= 1) return null;
    
    return (
      <div className="flex justify-between items-center mt-4">
        <div className="text-sm text-gray-700">
          Showing <span className="font-medium">{files.length}</span> of{' '}
          <span className="font-medium">{totalFiles}</span> files
        </div>
        
        <div className="flex space-x-2">
          <button
            onClick={() => setCurrentPage(prev => Math.max(0, prev - 1))}
            disabled={currentPage === 0}
            className="px-3 py-1 rounded border border-gray-300 text-sm font-medium text-gray-700 disabled:opacity-50"
          >
            Previous
          </button>
          
          {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
            // For simplicity, just show 5 page buttons
            let pageNum = i;
            if (totalPages > 5) {
              if (currentPage < 3) {
                pageNum = i;
              } else if (currentPage > totalPages - 3) {
                pageNum = totalPages - 5 + i;
              } else {
                pageNum = currentPage - 2 + i;
              }
            }
            
            return (
              <button
                key={i}
                onClick={() => setCurrentPage(pageNum)}
                className={`w-8 h-8 flex items-center justify-center rounded text-sm font-medium ${
                  currentPage === pageNum
                    ? 'bg-blue-600 text-white'
                    : 'border border-gray-300 text-gray-700 hover:bg-gray-50'
                }`}
              >
                {pageNum + 1}
              </button>
            );
          })}
          
          <button
            onClick={() => setCurrentPage(prev => Math.min(totalPages - 1, prev + 1))}
            disabled={currentPage === totalPages - 1 || totalPages === 0}
            className="px-3 py-1 rounded border border-gray-300 text-sm font-medium text-gray-700 disabled:opacity-50"
          >
            Next
          </button>
        </div>
      </div>
    );
  };

  // Render file detail preview
  const renderFileDetail = () => {
    if (!previewFileId) return null;
    
    return (
      <KnowledgeFilePreview
        fileId={previewFileId}
        onClose={() => setPreviewFileId(null)}
      />
    );
  };

  // Render selected files toolbar
  const renderSelectedFilesToolbar = () => {
    if (selectedFiles.length === 0) return null;
    
    return (
      <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg flex justify-between items-center">
        <div className="text-sm text-blue-700">
          <span className="font-medium">{selectedFiles.length}</span> file{selectedFiles.length !== 1 ? 's' : ''} selected
        </div>
        
        <div className="relative">
          <button
            onClick={() => setBulkActionOpen(!bulkActionOpen)}
            className="px-3 py-1 bg-blue-600 text-white rounded-md hover:bg-blue-700 text-sm flex items-center"
          >
            Bulk Actions
            <svg className="w-4 h-4 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" />
            </svg>
          </button>
          
          {renderBulkActionMenu()}
        </div>
      </div>
    );
  };

  // Render error message
  const renderError = () => {
    if (!error) return null;
    
    return (
      <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 flex items-center">
        <AlertCircle size={20} className="mr-2 text-red-500" />
        {error}
      </div>
    );
  };

  // Render upload error message
  const renderUploadError = () => {
    if (!uploadError) return null;
    
    return (
      <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 flex items-center">
        <AlertCircle size={20} className="mr-2 text-red-500" />
        {uploadError}
        <button
          onClick={() => setUploadError(null)}
          className="ml-auto text-red-500 hover:text-red-700"
        >
          <X size={18} />
        </button>
      </div>
    );
  };

  return (
    <div className="container mx-auto p-4">
      {renderToolbar()}
      {renderError()}
      {renderUploadError()}
      
      {searchMode ? (
        <KnowledgeSearch onSelectFile={(fileId) => {
          setPreviewFileId(fileId);
          setSearchMode(false);
        }} />
      ) : (
        <>
          {renderFilters()}
          {renderSelectedFilesToolbar()}
          
          {isLoading && files.length === 0 ? (
            <div className="flex justify-center py-12">
              <Loader2 size={48} className="animate-spin text-blue-500" />
            </div>
          ) : files.length === 0 ? (
            <div className="text-center py-12 border border-dashed border-gray-300 rounded-lg">
              <FileText size={48} className="mx-auto text-gray-400 mb-2" />
              <h3 className="text-lg font-medium text-gray-800">No files found</h3>
              <p className="text-gray-500 mt-1">
                {selectedCategory || selectedTags.length > 0
                  ? 'Try removing filters or'
                  : 'Get started by'}
                {' '}
                <button
                  onClick={() => fileInputRef.current?.click()}
                  className="text-blue-600 hover:text-blue-800 font-medium"
                >
                  uploading a file
                </button>
              </p>
            </div>
          ) : (
            <>
              {currentView === 'grid' ? renderGridView() : renderListView()}
              {renderPagination()}
              
              {/* File detail view */}
              {previewFileId && (
                <div className="mt-4">
                  <h3 className="text-sm font-medium text-gray-700 mb-2">File Details</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {files.find(f => f.id === previewFileId) && (
                      <>
                        <KnowledgeCategorySelector
                          file={files.find(f => f.id === previewFileId)!}
                          onUpdate={handleFileUpdate}
                        />
                        <KnowledgeTagsManager
                          file={files.find(f => f.id === previewFileId)!}
                          onUpdate={handleFileUpdate}
                        />
                      </>
                    )}
                  </div>
                </div>
              )}
            </>
          )}
        </>
      )}
      
      {renderFileDetail()}
    </div>
  );
}