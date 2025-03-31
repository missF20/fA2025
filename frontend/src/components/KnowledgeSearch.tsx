import React, { useState, useEffect } from 'react';
import { Search, Filter, FileText, Tag, Folder, X, AlertCircle, Loader2 } from 'lucide-react';
import { KnowledgeSearchResult, KnowledgeCategory, KnowledgeTag } from '../types';
import { searchKnowledgeBase, getCategories, getTags } from '../services/knowledgeService';

interface KnowledgeSearchProps {
  onSelectFile: (fileId: string) => void;
}

export function KnowledgeSearch({ onSelectFile }: KnowledgeSearchProps) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<KnowledgeSearchResult[]>([]);
  const [categories, setCategories] = useState<KnowledgeCategory[]>([]);
  const [tags, setTags] = useState<KnowledgeTag[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string | undefined>(undefined);
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [selectedFileType, setSelectedFileType] = useState<string | undefined>(undefined);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showFilters, setShowFilters] = useState(false);
  const [selectedResult, setSelectedResult] = useState<string | null>(null);

  // Load categories and tags
  useEffect(() => {
    const loadFilters = async () => {
      try {
        const [categoriesData, tagsData] = await Promise.all([
          getCategories(),
          getTags()
        ]);
        setCategories(categoriesData);
        setTags(tagsData);
      } catch (err) {
        console.error('Error loading filters:', err);
      }
    };

    loadFilters();
  }, []);

  // Handle search
  const handleSearch = async () => {
    if (!query.trim()) {
      setResults([]);
      return;
    }

    try {
      setIsLoading(true);
      setError(null);

      const searchResults = await searchKnowledgeBase(query, {
        category: selectedCategory,
        fileType: selectedFileType,
        tags: selectedTags.length > 0 ? selectedTags : undefined,
        includeSnippets: true
      });

      setResults(searchResults);
    } catch (err) {
      console.error('Search error:', err);
      setError('An error occurred while searching');
      setResults([]);
    } finally {
      setIsLoading(false);
    }
  };

  // Handle form submission
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    handleSearch();
  };

  // Clear all filters
  const clearFilters = () => {
    setSelectedCategory(undefined);
    setSelectedTags([]);
    setSelectedFileType(undefined);
  };

  // Format file type for display
  const formatFileType = (fileType: string) => {
    if (fileType.includes('pdf')) return 'PDF';
    if (fileType.includes('wordprocessingml') || fileType.includes('msword')) return 'Word';
    if (fileType.includes('text/plain')) return 'Text';
    if (fileType.includes('html')) return 'HTML';
    return fileType.split('/').pop()?.toUpperCase() || fileType;
  };

  // Handle tag selection
  const toggleTag = (tag: string) => {
    if (selectedTags.includes(tag)) {
      setSelectedTags(selectedTags.filter(t => t !== tag));
    } else {
      setSelectedTags([...selectedTags, tag]);
    }
  };

  return (
    <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
      <div className="space-y-4">
        {/* Search form */}
        <form onSubmit={handleSubmit} className="flex w-full">
          <div className="relative flex-grow">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <Search size={18} className="text-gray-400" />
            </div>
            <input
              type="text"
              className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-l-md leading-5 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="Search knowledge base..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
          </div>
          <button
            type="button"
            onClick={() => setShowFilters(!showFilters)}
            className={`px-3 py-2 border-y border-r border-gray-300 ${
              showFilters ? 'bg-blue-50 text-blue-700' : 'text-gray-500 hover:bg-gray-100'
            }`}
            title="Toggle filters"
          >
            <Filter size={18} />
          </button>
          <button
            type="submit"
            className="ml-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
          >
            Search
          </button>
        </form>

        {/* Filters section */}
        {showFilters && (
          <div className="p-4 border border-gray-200 rounded-md bg-gray-50">
            <div className="flex justify-between items-center mb-3">
              <h3 className="text-sm font-medium text-gray-700">Filters</h3>
              <button
                onClick={clearFilters}
                className="text-xs text-blue-600 hover:text-blue-800"
              >
                Clear all
              </button>
            </div>

            <div className="space-y-4">
              {/* Categories filter */}
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

              {/* File type filter */}
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">
                  File Type
                </label>
                <select
                  value={selectedFileType || ''}
                  onChange={(e) => setSelectedFileType(e.target.value || undefined)}
                  className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 text-sm"
                >
                  <option value="">All Types</option>
                  <option value="application/pdf">PDF</option>
                  <option value="application/vnd.openxmlformats-officedocument.wordprocessingml.document">DOCX</option>
                  <option value="application/msword">DOC</option>
                  <option value="text/plain">TXT</option>
                  <option value="text/html">HTML</option>
                </select>
              </div>

              {/* Tags filter */}
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">
                  Tags
                </label>
                <div className="flex flex-wrap gap-2">
                  {tags.length === 0 ? (
                    <span className="text-sm text-gray-500">No tags available</span>
                  ) : (
                    tags.map((tag) => (
                      <button
                        key={tag.name}
                        onClick={() => toggleTag(tag.name)}
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
        )}

        {/* Selected filters display */}
        {(selectedCategory || selectedFileType || selectedTags.length > 0) && (
          <div className="flex flex-wrap gap-2 mt-2">
            {selectedCategory && (
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                <Folder size={12} className="mr-1" />
                {selectedCategory}
                <button
                  onClick={() => setSelectedCategory(undefined)}
                  className="ml-1 text-blue-500 hover:text-blue-700"
                >
                  <X size={14} />
                </button>
              </span>
            )}
            
            {selectedFileType && (
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                <FileText size={12} className="mr-1" />
                {formatFileType(selectedFileType)}
                <button
                  onClick={() => setSelectedFileType(undefined)}
                  className="ml-1 text-blue-500 hover:text-blue-700"
                >
                  <X size={14} />
                </button>
              </span>
            )}
            
            {selectedTags.map((tag) => (
              <span 
                key={tag}
                className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
              >
                <Tag size={12} className="mr-1" />
                {tag}
                <button
                  onClick={() => toggleTag(tag)}
                  className="ml-1 text-blue-500 hover:text-blue-700"
                >
                  <X size={14} />
                </button>
              </span>
            ))}
          </div>
        )}

        {/* Results section */}
        <div className="mt-6">
          {isLoading ? (
            <div className="flex justify-center py-12">
              <Loader2 size={48} className="animate-spin text-blue-500" />
            </div>
          ) : error ? (
            <div className="flex items-center justify-center p-4 bg-red-50 text-red-700 rounded-lg">
              <AlertCircle size={20} className="mr-2" />
              {error}
            </div>
          ) : results.length > 0 ? (
            <div className="space-y-4">
              <h3 className="text-sm font-medium text-gray-700">
                {results.length} {results.length === 1 ? 'result' : 'results'} found for "{query}"
              </h3>
              <div className="space-y-4 max-h-96 overflow-y-auto pr-2">
                {results.map((result) => (
                  <div 
                    key={result.id}
                    className={`p-4 border rounded-lg cursor-pointer transition-colors ${
                      selectedResult === result.id
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 hover:bg-gray-50'
                    }`}
                    onClick={() => {
                      setSelectedResult(result.id);
                      onSelectFile(result.id);
                    }}
                  >
                    <div className="flex items-center mb-2">
                      <FileText size={16} className="text-blue-600 mr-2" />
                      <h4 className="text-sm font-medium text-gray-800">{result.file_name}</h4>
                      <span className="ml-2 px-2 py-0.5 rounded text-xs bg-gray-100 text-gray-600">
                        {formatFileType(result.file_type)}
                      </span>
                    </div>
                    
                    {result.category && (
                      <div className="flex items-center text-xs text-gray-500 mb-1">
                        <Folder size={12} className="mr-1" />
                        {result.category}
                      </div>
                    )}
                    
                    {result.tags && result.tags.length > 0 && (
                      <div className="flex flex-wrap gap-1 mb-2">
                        {result.tags.map((tag, i) => (
                          <span 
                            key={i}
                            className="inline-flex items-center px-2 py-0.5 rounded-full text-xs bg-gray-100 text-gray-600"
                          >
                            <Tag size={10} className="mr-1" />
                            {tag}
                          </span>
                        ))}
                      </div>
                    )}
                    
                    {result.snippets && result.snippets.length > 0 && (
                      <div className="mt-2 space-y-2">
                        {result.snippets.map((snippet, i) => (
                          <div key={i} className="text-xs text-gray-600 bg-gray-50 p-2 rounded">
                            <span dangerouslySetInnerHTML={{
                              __html: snippet.replace(
                                new RegExp(query, 'gi'),
                                match => `<mark class="bg-yellow-200">${match}</mark>`
                              )
                            }} />
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          ) : query ? (
            <div className="text-center py-12 text-gray-500">
              <p>No results found for "{query}"</p>
              <p className="text-sm mt-2">Try changing your search terms or filters</p>
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
}