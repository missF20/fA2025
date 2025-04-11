import { useState, useEffect } from 'react';
import { X, FileText, Calendar, Tag, Loader2, Eye, Download, FileType } from 'lucide-react';
import { KnowledgeFile, KnowledgeFileWithContent } from '../types';
import { getKnowledgeFile } from '../services/knowledgeService';

// Helper functions
const isPdfFile = (file: KnowledgeFile | KnowledgeFileWithContent): boolean => {
  return file.file_type === 'pdf' || file.file_type === 'application/pdf';
};

const isImageFile = (file: KnowledgeFile | KnowledgeFileWithContent): boolean => {
  const imageTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/svg+xml', 'jpeg', 'png', 'gif', 'svg'];
  return imageTypes.includes(file.file_type);
};

const isDocFile = (file: KnowledgeFile | KnowledgeFileWithContent): boolean => {
  const docTypes = ['application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 
                    'application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    'application/vnd.ms-powerpoint', 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
                    'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx'];
  return docTypes.includes(file.file_type);
};

interface KnowledgeFilePreviewProps {
  fileId: string;
  onClose: () => void;
  onUpdate?: (updatedFile: KnowledgeFile | KnowledgeFileWithContent) => void;
}

export function KnowledgeFilePreview({ fileId, onClose, onUpdate }: KnowledgeFilePreviewProps) {
  const [file, setFile] = useState<KnowledgeFileWithContent | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'content'|'metadata'|'preview'>('content');
  const [isDownloading, setIsDownloading] = useState(false);

  useEffect(() => {
    const fetchFile = async () => {
      try {
        setLoading(true);
        setError(null);
        const fileData = await getKnowledgeFile(fileId);
        
        // Make sure we have the correct file data structure
        if (fileData) {
          // Normalize the data to ensure we have consistent field names
          const normalizedFile: KnowledgeFileWithContent = {
            ...fileData,
            // Ensure we have file_name (some endpoints return filename instead)
            file_name: fileData.file_name || (fileData as any).filename || 'Unnamed file',
            // Ensure proper text content
            content: fileData.content || ''
          };
          
          setFile(normalizedFile);
          console.log("File details loaded successfully:", normalizedFile.file_name);
        } else {
          setError('File data is incomplete or invalid');
        }
      } catch (err) {
        console.error('Error fetching file details:', err);
        setError('Failed to load file details for file preview');
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
  
  // Render file preview based on file type
  const renderFilePreview = () => {
    if (!file) {
      return <div className="italic text-gray-500">No file to preview</div>;
    }
    
    if (isPdfFile(file)) {
      // For PDF files, create an embedded preview
      // Use content as base64
      const pdfSrc = `data:application/pdf;base64,${file.content}`;
      
      return (
        <div className="relative w-full h-[60vh]">
          <iframe 
            src={pdfSrc}
            title={file.file_name || 'PDF Preview'} 
            className="w-full h-full border-0 rounded"
            allowFullScreen
          >
            Your browser does not support PDF previews.
          </iframe>
        </div>
      );
    } else if (isImageFile(file)) {
      // For image files
      const imageSrc = `data:${file.file_type};base64,${file.content}`;
      
      return (
        <div className="flex justify-center">
          <img 
            src={imageSrc} 
            alt={file.file_name || 'Image Preview'} 
            className="max-w-full max-h-[60vh] object-contain"
          />
        </div>
      );
    } else {
      // For unsupported preview types
      return (
        <div className="flex flex-col items-center justify-center py-10">
          <FileType size={48} className="text-gray-400 mb-4" />
          <h3 className="text-lg font-medium text-gray-700 mb-2">
            Preview not available
          </h3>
          <p className="text-gray-500 text-center max-w-md mb-4">
            This file type doesn't support preview. You can view the extracted content 
            in the Content tab or download the file.
          </p>
          <button
            onClick={() => {
              setIsDownloading(true);
              // Implement download logic here
              setTimeout(() => setIsDownloading(false), 1000);
            }}
            className="px-4 py-2 bg-blue-100 text-blue-700 rounded-md hover:bg-blue-200 transition-colors inline-flex items-center"
            disabled={isDownloading}
          >
            {isDownloading ? (
              <>
                <Loader2 size={16} className="animate-spin mr-2" />
                Downloading...
              </>
            ) : (
              <>
                <Download size={16} className="mr-2" />
                Download File
              </>
            )}
          </button>
        </div>
      );
    }
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
                    className={`pb-3 px-1 border-b-2 font-medium text-sm transition-colors flex items-center ${
                      activeTab === 'content'
                        ? 'border-blue-500 text-blue-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }`}
                  >
                    <FileText size={16} className="mr-1" />
                    Content
                  </button>
                  <button
                    onClick={() => setActiveTab('metadata')}
                    className={`pb-3 px-1 border-b-2 font-medium text-sm transition-colors flex items-center ${
                      activeTab === 'metadata'
                        ? 'border-blue-500 text-blue-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }`}
                  >
                    <Tag size={16} className="mr-1" />
                    Metadata
                  </button>
                  {file && (isPdfFile(file) || isImageFile(file)) && (
                    <button
                      onClick={() => setActiveTab('preview')}
                      className={`pb-3 px-1 border-b-2 font-medium text-sm transition-colors flex items-center ${
                        activeTab === 'preview'
                          ? 'border-blue-500 text-blue-600'
                          : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                      }`}
                    >
                      <Eye size={16} className="mr-1" />
                      Preview
                    </button>
                  )}
                </nav>
              </div>

              {/* Tab Content */}
              <div className="p-2">
                {activeTab === 'content' ? renderContent() : 
                 activeTab === 'metadata' ? renderMetadata() : 
                 renderFilePreview()}
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