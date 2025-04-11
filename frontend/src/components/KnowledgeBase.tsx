import React, { useState, useEffect, useRef, useCallback } from 'react';
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
  const [isDragging, setIsDragging] = useState(false);
  
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

  // Handle file upload from input element
  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (!files || files.length === 0) return;
    
    // Convert FileList to array for processing
    const filesArray = Array.from(files);
    
    // Process files using the common upload handler
    await handleUploadFiles(filesArray);
    
    // Reset file input
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
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
      await bulkUpdateKnowledgeFiles(selectedFiles, { tags: tagsToAdd });
      
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
  
  // Drag and drop handlers
  const handleDragEnter = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    if (!isDragging) {
      setIsDragging(true);
    }
  }, [isDragging]);

  const handleDrop = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      console.log(`${e.dataTransfer.files.length} files dropped`);
      
      // Convert FileList to array for processing
      const filesArray = Array.from(e.dataTransfer.files);
      
      // Process dropped files
      handleUploadFiles(filesArray);
    }
  }, [selectedCategory, selectedTags]);
  
  // Success message state
  const [uploadSuccess, setUploadSuccess] = useState<string | null>(null);
  
  // Process multiple files for upload
  const handleUploadFiles = async (filesToUpload: File[]) => {
    if (!filesToUpload || filesToUpload.length === 0) return;
    
    setIsUploading(true);
    setUploadProgress(0);
    setUploadError(null);
    setUploadSuccess(null);
    
    try {
      // Process each file
      const totalFiles = filesToUpload.length;
      let successCount = 0;
      let successFiles: string[] = [];
      let errorFiles: string[] = [];
      
      for (let i = 0; i < totalFiles; i++) {
        const file = filesToUpload[i];
        
        try {
          console.log(`Uploading file ${i+1}/${totalFiles}: ${file.name} (${file.size} bytes, type: ${file.type})`);
          
          // Check file type support
          const fileType = file.type.toLowerCase();
          const isSupported = 
            fileType.includes('pdf') || 
            fileType.includes('word') || 
            fileType.includes('docx') ||
            fileType.includes('text/plain') ||
            fileType.includes('text/markdown') ||
            fileType.includes('text/html') ||
            file.name.endsWith('.md') ||
            file.name.endsWith('.txt') ||
            file.name.endsWith('.docx') ||
            file.name.endsWith('.pdf');
          
          if (!isSupported) {
            console.warn(`File type ${fileType} may not be fully supported`);
          }
          
          // Show current progress visually
          const currentProgress = Math.round(((i) / totalFiles) * 100);
          setUploadProgress(currentProgress);
          
          // Upload the file with progress callback
          await uploadKnowledgeFile(
            file, 
            selectedCategory, 
            selectedTags,
            (progress) => {
              // Use either the callback progress or calculate based on file count
              const fileProgress = progress || Math.round(((i) / totalFiles) * 100);
              setUploadProgress(fileProgress);
            }
          );
          successCount++;
          successFiles.push(file.name);
          
          // Update progress after successful upload
          const newProgress = Math.round(((i + 1) / totalFiles) * 100);
          setUploadProgress(newProgress);
        } catch (fileErr) {
          console.error(`Error uploading ${file.name}:`, fileErr);
          errorFiles.push(file.name);
          // Continue with next file despite error
        }
      }
      
      // Refresh file list
      fetchFiles();
      
      // Show success message if any files were successful
      if (successCount > 0) {
        const successMessage = successCount === 1 
          ? `Successfully uploaded ${successFiles[0]}`
          : `Successfully uploaded ${successCount} files`;
        setUploadSuccess(successMessage);
        
        // Auto dismiss success message after 5 seconds
        setTimeout(() => {
          setUploadSuccess(null);
        }, 5000);
      }
      
      // Show error message if any files failed
      if (errorFiles.length > 0) {
        if (successCount > 0) {
          setUploadError(`Successfully uploaded ${successCount} files, but failed to upload: ${errorFiles.join(', ')}`);
        } else {
          setUploadError(`Failed to upload files: ${errorFiles.join(', ')}`);
        }
      }
    } catch (err) {
      console.error('Upload error:', err);
      setUploadError('Failed to upload one or more files. Please try again.');
    } finally {
      setIsUploading(false);
      // Keep final progress value for a moment before resetting
      setTimeout(() => {
        setUploadProgress(0);
      }, 1000);
    }
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

  // Render selected files toolbar
  const renderSelectedFilesToolbar = () => {
    if (selectedFiles.length === 0) return null;
    
    return (
      <div className="mb-4 p-2 bg-gray-50 border border-gray-200 rounded-lg flex items-center justify-between">
        <div className="text-sm text-gray-700">
          {selectedFiles.length} {selectedFiles.length === 1 ? 'file' : 'files'} selected
        </div>
        
        <div className="flex items-center space-x-2 relative">
          <button
            onClick={() => setSelectedFiles([])}
            className="p-1.5 rounded-md text-gray-600 hover:bg-gray-200"
            title="Clear selection"
          >
            <X size={16} />
          </button>
          
          <button
            onClick={() => setBulkActionOpen(!bulkActionOpen)}
            className="px-3 py-1.5 rounded-md bg-blue-600 text-white hover:bg-blue-700 flex items-center"
            disabled={bulkProcessing}
          >
            {bulkProcessing ? (
              <Loader2 size={14} className="animate-spin mr-1" />
            ) : null}
            Actions
          </button>
          
          {renderBulkActionMenu()}
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
              Category
            </th>
            <th scope="col" className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Tags
            </th>
            <th scope="col" className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Size
            </th>
            <th scope="col" className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Updated
            </th>
            <th scope="col" className="px-3 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
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
                  <span className="text-xl mr-3">{getFileIcon(file.file_type)}</span>
                  <div className="text-sm font-medium text-gray-900 line-clamp-1" title={file.file_name}>
                    {file.file_name}
                  </div>
                </div>
              </td>
              <td className="px-3 py-4 whitespace-nowrap">
                <div className="text-sm text-gray-500">
                  {file.category || '-'}
                </div>
              </td>
              <td className="px-3 py-4 whitespace-nowrap">
                <div className="flex flex-wrap gap-1 max-w-xs">
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
              </td>
              <td className="px-3 py-4 whitespace-nowrap text-sm text-gray-500">
                {formatFileSize(file.file_size)}
              </td>
              <td className="px-3 py-4 whitespace-nowrap text-sm text-gray-500">
                {formatDate(file.updated_at || file.created_at)}
              </td>
              <td className="px-3 py-4 whitespace-nowrap text-right text-sm font-medium">
                <div className="flex justify-end space-x-2">
                  <button
                    onClick={e => {
                      e.stopPropagation();
                      setPreviewFileId(file.id);
                    }}
                    className="text-blue-600 hover:text-blue-900"
                    title="Preview file"
                  >
                    <FileText size={16} />
                  </button>
                  <button
                    onClick={e => {
                      e.stopPropagation();
                      handleDeleteFile(file.id);
                    }}
                    className="text-red-600 hover:text-red-900"
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
      <div className="flex justify-center items-center mt-4 space-x-2">
        <button
          onClick={() => setCurrentPage(currentPage - 1)}
          disabled={currentPage === 0}
          className="px-3 py-1 rounded-md bg-gray-100 text-gray-700 hover:bg-gray-200 disabled:opacity-50"
        >
          Previous
        </button>
        
        <div className="text-sm text-gray-700">
          Page {currentPage + 1} of {totalPages}
        </div>
        
        <button
          onClick={() => setCurrentPage(currentPage + 1)}
          disabled={currentPage >= totalPages - 1}
          className="px-3 py-1 rounded-md bg-gray-100 text-gray-700 hover:bg-gray-200 disabled:opacity-50"
        >
          Next
        </button>
      </div>
    );
  };

  // Render file detail
  const renderFileDetail = () => {
    if (!previewFileId) return null;
    
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
        <div className="bg-white rounded-lg shadow-xl w-full max-w-4xl h-4/5 flex flex-col">
          <div className="p-4 border-b flex items-center justify-between">
            <h3 className="text-lg font-medium text-gray-900">
              File Preview
            </h3>
            <button
              onClick={() => setPreviewFileId(null)}
              className="text-gray-500 hover:text-gray-700"
            >
              <X size={20} />
            </button>
          </div>
          
          <div className="flex-1 overflow-auto p-4">
            <KnowledgeFilePreview 
              fileId={previewFileId} 
              onUpdate={handleFileUpdate}
            />
          </div>
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
        <button
          onClick={() => setError(null)}
          className="ml-auto text-red-500 hover:text-red-700"
        >
          <X size={18} />
        </button>
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
  
  // Render upload success message
  const renderUploadSuccess = () => {
    if (!uploadSuccess) return null;
    
    return (
      <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-lg text-green-700 flex items-center">
        <CheckCircle size={20} className="mr-2 text-green-500" />
        {uploadSuccess}
        <button
          onClick={() => setUploadSuccess(null)}
          className="ml-auto text-green-500 hover:text-green-700"
        >
          <X size={18} />
        </button>
      </div>
    );
  };
  
  // Render drag overlay
  const renderDragOverlay = () => {
    if (!isDragging) return null;
    
    return (
      <div className="fixed inset-0 bg-blue-600 bg-opacity-30 flex items-center justify-center z-50 pointer-events-none">
        <div className="bg-white p-8 rounded-lg shadow-lg text-center">
          <Upload size={48} className="mx-auto text-blue-600 mb-4" />
          <h3 className="text-xl font-medium text-gray-900 mb-2">Drop files to upload</h3>
          <p className="text-gray-600">Release to upload your files to the knowledge base</p>
        </div>
      </div>
    );
  };

  return (
    <div 
      className="container mx-auto p-4"
      onDragEnter={handleDragEnter}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      {renderDragOverlay()}
      {renderToolbar()}
      {renderError()}
      {renderUploadError()}
      {renderUploadSuccess()}
      
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
            <div 
              className="text-center py-12 border-2 border-dashed border-gray-300 rounded-lg bg-gray-50 transition-colors duration-200 hover:bg-gray-100 hover:border-blue-300"
              onClick={() => fileInputRef.current?.click()}
              style={{ cursor: 'pointer' }}
            >
              <Upload size={48} className="mx-auto text-gray-400 mb-2" />
              <h3 className="text-lg font-medium text-gray-800">No files found</h3>
              <p className="text-gray-500 mt-1">
                {selectedCategory || selectedTags.length > 0
                  ? 'Try removing filters or'
                  : 'Get started by'}
                {' '}
                <span className="text-blue-600 font-medium">
                  clicking to upload files
                </span>
              </p>
              <p className="text-gray-500 mt-2 text-sm">
                or drag and drop files here
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