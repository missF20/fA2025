import { useState, useEffect } from 'react';
import { X, FileText, Calendar, Tag, Loader2 } from 'lucide-react';
import { KnowledgeFile, KnowledgeFileWithContent } from '../types';
import { getKnowledgeFile } from '../services/knowledgeService';

interface KnowledgeFilePreviewProps {
  fileId: string;
  onClose: () => void;
  onUpdate?: (updatedFile: KnowledgeFile | KnowledgeFileWithContent) => void;
}

export function KnowledgeFilePreview({ fileId, onClose, onUpdate }: KnowledgeFilePreviewProps) {
  const [file, setFile] = useState<KnowledgeFileWithContent | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'content'|'metadata'>('content');

  useEffect(() => {
    const fetchFile = async () => {
      try {
        setLoading(true);
        setError(null);
        const fileData = await getKnowledgeFile(fileId);
        setFile(fileData);
      } catch (err) {
        console.error('Error fetching file details:', err);
        setError('Failed to load file details');
      } finally {
        setLoading(false);
      }
    };

    fetchFile();
  }, [fileId]);

  // Prepare metadata for display
  const prepareMetadata = () => {
    if (!file || !file.metadata) return {};
    
    // Parse the metadata if it's a string
    let metadata = file.metadata;
    if (typeof metadata === 'string') {
      try {
        metadata = JSON.parse(metadata);
      } catch (e) {
        return { error: 'Invalid metadata format' };
      }
    }
    
    return metadata;
  };

  // Process file tags for display
  const renderTags = () => {
    if (!file || !file.tags) return null;
    
    // Process tags based on whether they're a string or array
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
    
    if (tags.length === 0) return null;
    
    return (
      <div className="flex flex-wrap gap-1 mt-2">
        {tags.map((tag, index) => (
          <span key={index} className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded">
            {tag}
          </span>
        ))}
      </div>
    );
  };

  // Format dates
  const formatDate = (dateString?: string) => {
    if (!dateString) return 'Unknown';
    try {
      return new Date(dateString).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch (e) {
      return dateString;
    }
  };

  // Render the content section of the preview
  const renderContent = () => {
    if (!file || !file.content) {
      return <div className="italic text-gray-500">No content available</div>;
    }

    // For very large content, we may want to paginate or virtualize
    return (
      <div className="whitespace-pre-wrap font-mono text-sm overflow-auto max-h-[60vh]">
        {file.content}
      </div>
    );
  };

  // Render the metadata section of the preview
  const renderMetadata = () => {
    const metadata = prepareMetadata();
    
    if (!metadata || Object.keys(metadata).length === 0) {
      return <div className="italic text-gray-500">No metadata available</div>;
    }

    return (
      <div className="overflow-auto max-h-[60vh]">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Property
              </th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Value
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {Object.entries(metadata).map(([key, value], index) => (
              <tr key={index}>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                  {key}
                </td>
                <td className="px-6 py-4 text-sm text-gray-500">
                  {typeof value === 'object' 
                    ? JSON.stringify(value) 
                    : String(value)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl shadow-lg w-full max-w-4xl max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="p-4 border-b border-gray-200 flex justify-between items-center">
          <div className="flex items-center gap-3">
            <FileText size={24} className="text-blue-600" />
            <div>
              <h2 className="text-xl font-bold text-gray-900">
                {loading ? 'Loading...' : error ? 'Error' : file?.file_name}
              </h2>
              {file?.category && (
                <p className="text-sm text-gray-500">
                  Category: {file.category}
                </p>
              )}
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 transition-colors"
          >
            <X size={24} />
          </button>
        </div>

        {/* Content */}
        <div className="p-4">
          {loading ? (
            <div className="flex justify-center py-12">
              <Loader2 size={48} className="animate-spin text-blue-500" />
            </div>
          ) : error ? (
            <div className="text-center py-8 text-red-500">{error}</div>
          ) : (
            <>
              {/* Info Bar */}
              <div className="bg-gray-50 p-4 rounded-lg mb-4">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="flex items-center gap-2">
                    <Calendar size={16} className="text-gray-400" />
                    <div>
                      <p className="text-xs text-gray-500">Uploaded</p>
                      <p className="text-sm font-medium text-gray-800">
                        {formatDate(file?.created_at)}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <FileText size={16} className="text-gray-400" />
                    <div>
                      <p className="text-xs text-gray-500">File Type</p>
                      <p className="text-sm font-medium text-gray-800">
                        {file?.file_type}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Tag size={16} className="text-gray-400" />
                    <div>
                      <p className="text-xs text-gray-500">Tags</p>
                      {renderTags() || (
                        <p className="text-sm font-medium text-gray-800">None</p>
                      )}
                    </div>
                  </div>
                </div>
              </div>

              {/* Tabs */}
              <div className="border-b border-gray-200 mb-4">
                <nav className="-mb-px flex space-x-8">
                  <button
                    onClick={() => setActiveTab('content')}
                    className={`pb-3 px-1 border-b-2 font-medium text-sm transition-colors ${
                      activeTab === 'content'
                        ? 'border-blue-500 text-blue-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }`}
                  >
                    Content
                  </button>
                  <button
                    onClick={() => setActiveTab('metadata')}
                    className={`pb-3 px-1 border-b-2 font-medium text-sm transition-colors ${
                      activeTab === 'metadata'
                        ? 'border-blue-500 text-blue-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }`}
                  >
                    Metadata
                  </button>
                </nav>
              </div>

              {/* Tab Content */}
              <div className="p-2">
                {activeTab === 'content' ? renderContent() : renderMetadata()}
              </div>
            </>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-gray-200 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}