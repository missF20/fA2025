import React, { useState, useEffect } from 'react';
import { supabase } from '../lib/supabase';
import { FileText, Upload, Trash2, AlertCircle, CheckCircle, Loader2 } from 'lucide-react';
import type { KnowledgeFile } from '../types';

export function KnowledgeBase() {
  const [files, setFiles] = useState<KnowledgeFile[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isDragging, setIsDragging] = useState(false);

  useEffect(() => {
    fetchKnowledgeFiles();
  }, []);

  async function fetchKnowledgeFiles() {
    try {
      setIsLoading(true);
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) throw new Error('Not authenticated');

      const { data, error } = await supabase
        .from('knowledge_files')
        .select('*')
        .eq('user_id', user.id)
        .order('created_at', { ascending: false });

      if (error) throw error;
      setFiles(data || []);
    } catch (err) {
      console.error('Error fetching knowledge files:', err);
      setError('Failed to load knowledge files');
    } finally {
      setIsLoading(false);
    }
  }

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (!selectedFile) return;

    // Check file size (max 10MB)
    if (selectedFile.size > 10 * 1024 * 1024) {
      setError('File size exceeds the 10MB limit');
      return;
    }

    // Check file type (PDF only)
    if (selectedFile.type !== 'application/pdf') {
      setError('Only PDF files are supported');
      return;
    }

    setIsUploading(true);
    setUploadProgress(0);
    setError(null);
    setSuccess(null);

    try {
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) throw new Error('Not authenticated');

      // Read file as binary data
      const reader = new FileReader();

      reader.onload = async (event) => {
        const fileContent = event.target?.result;

        if (fileContent) {
          // Simulate upload progress
          const progressInterval = setInterval(() => {
            setUploadProgress(prev => {
              if (prev >= 90) {
                clearInterval(progressInterval);
                return 90;
              }
              return prev + 10;
            });
          }, 300);

          // Upload to Supabase
          const { error } = await supabase
            .from('knowledge_files')
            .insert({
              user_id: user.id,
              file_name: selectedFile.name,
              file_size: selectedFile.size,
              file_type: selectedFile.type,
              content: fileContent
            });

          clearInterval(progressInterval);

          if (error) throw error;

          setUploadProgress(100);
          setSuccess('File uploaded successfully');
          fetchKnowledgeFiles();
        }
      };

      reader.onerror = () => {
        throw new Error('Error reading file');
      };

      reader.readAsArrayBuffer(selectedFile);
    } catch (err) {
      console.error('Error uploading file:', err);
      setError('Failed to upload file');
    } finally {
      setIsUploading(false);
      // Reset the file input
      e.target.value = '';
    }
  };

  const handleDeleteFile = async (fileId: string) => {
    try {
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) throw new Error('Not authenticated');

      const { error } = await supabase
        .from('knowledge_files')
        .delete()
        .eq('id', fileId)
        .eq('user_id', user.id);

      if (error) throw error;

      setSuccess('File deleted successfully');
      setFiles(files.filter(file => file.id !== fileId));
    } catch (err) {
      console.error('Error deleting file:', err);
      setError('Failed to delete file');
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' bytes';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const handleDragEnter = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    const file = e.dataTransfer.files[0];
    if (!file) return;

    // Create a new input element
    const input = document.createElement('input');
    input.type = 'file';

    // Create a new file list
    const dataTransfer = new DataTransfer();
    dataTransfer.items.add(file);
    input.files = dataTransfer.files;

    // Trigger the file upload handler
    handleFileUpload({ target: input } as any);
  };

  return (
    <div className="p-8">
      <div className="bg-white rounded-xl p-8 shadow-sm border border-gray-100 max-w-4xl mx-auto">
        <div className="flex items-center gap-3 mb-6">
          <div className="p-2 bg-blue-50 rounded-lg">
            <FileText className="h-6 w-6 text-blue-600" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-gray-900">Knowledge Base</h2>
            <p className="text-sm text-gray-500">
              Upload and manage your knowledge base documents
            </p>
          </div>
        </div>

        {error && (
          <div className="bg-red-50 text-red-600 p-3 rounded-lg mb-6 text-sm">
            {error}
          </div>
        )}

        {success && (
          <div className="bg-green-50 text-green-600 p-3 rounded-lg mb-6 text-sm">
            {success}
          </div>
        )}

        <div className="mb-6">
          <div
            onDragEnter={handleDragEnter}
            onDragLeave={handleDragLeave}
            onDragOver={handleDragOver}
            onDrop={handleDrop}
            className={`flex items-center justify-center gap-2 p-8 border-2 border-dashed rounded-lg cursor-pointer transition-colors ${
              isDragging ? 'bg-blue-50 border-blue-500' :
              isUploading ? 'bg-gray-50 border-gray-300' : 
              'border-blue-300 hover:bg-blue-50'
            }`}
          >
            <label 
              htmlFor="file-upload" 
              className="w-full h-full flex flex-col items-center justify-center cursor-pointer"
            >
              {isUploading ? (
                <div className="text-center">
                  <Loader2 size={24} className="mx-auto mb-2 animate-spin text-blue-500" />
                  <p className="text-sm font-medium text-gray-700">Uploading... {uploadProgress}%</p>
                  <div className="w-full bg-gray-200 rounded-full h-2.5 mt-2">
                    <div 
                      className="bg-blue-600 h-2.5 rounded-full transition-all duration-300" 
                      style={{ width: `${uploadProgress}%` }}
                    ></div>
                  </div>
                </div>
              ) : (
                <>
                  <Upload size={24} className="text-blue-500" />
                  <span className="text-sm font-medium text-gray-700 mt-2">
                    Drag and drop your PDF file here, or click to browse
                  </span>
                </>
              )}
              <input
                id="file-upload"
                type="file"
                accept=".pdf"
                className="hidden"
                onChange={handleFileUpload}
                disabled={isUploading}
              />
            </label>
          </div>
          <p className="text-xs text-gray-500 mt-2">
            Only PDF files are supported. Maximum file size: 10MB.
          </p>
        </div>

        <div className="bg-white rounded-xl">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Your Knowledge Files</h3>

          {isLoading ? (
            <div className="flex justify-center py-8">
              <Loader2 size={24} className="animate-spin text-blue-500" />
            </div>
          ) : files.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <FileText size={40} className="mx-auto mb-2 text-gray-300" />
              <p>No knowledge files uploaded yet</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      File Name
                    </th>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Size
                    </th>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Uploaded
                    </th>
                    <th scope="col" className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {files.map((file) => (
                    <tr key={file.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <FileText size={18} className="text-red-500 mr-2" />
                          <span className="text-sm font-medium text-gray-900">{file.file_name}</span>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {formatFileSize(file.file_size)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {formatDate(file.created_at)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        <button
                          onClick={() => handleDeleteFile(file.id)}
                          className="text-red-600 hover:text-red-900 transition-colors"
                        >
                          <Trash2 size={18} />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
import React, { useState, useEffect } from 'react';
import { useAuth } from '../hooks/useAuth';

interface KnowledgeFile {
  id: string;
  file_name: string;
  file_type: string;
  file_size: number;
  created_at: string;
}

export default function KnowledgeBase() {
  const [files, setFiles] = useState<KnowledgeFile[]>([]);
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const { token } = useAuth();

  useEffect(() => {
    fetchFiles();
  }, []);

  const fetchFiles = async () => {
    try {
      const response = await fetch('/api/knowledge/files', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      const data = await response.json();
      setFiles(data.files);
    } catch (error) {
      console.error('Error fetching files:', error);
    }
  };

  const handleFileUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!uploadFile) return;

    const formData = new FormData();
    formData.append('file', uploadFile);

    try {
      const response = await fetch('/api/knowledge/files', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });

      if (response.ok) {
        fetchFiles();
        setUploadFile(null);
      }
    } catch (error) {
      console.error('Error uploading file:', error);
    }
  };

  return (
    <div className="p-6">
      <h2 className="text-2xl font-bold mb-6">Knowledge Base</h2>

      <div className="mb-8">
        <form onSubmit={handleFileUpload} className="flex gap-4 items-center">
          <input
            type="file"
            onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
            className="border p-2 rounded"
          />
          <button 
            type="submit"
            className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
          >
            Upload
          </button>
        </form>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {files.map((file) => (
          <div key={file.id} className="border rounded p-4">
            <h3 className="font-semibold">{file.file_name}</h3>
            <p className="text-sm text-gray-600">Type: {file.file_type}</p>
            <p className="text-sm text-gray-600">
              Size: {Math.round(file.file_size / 1024)} KB
            </p>
            <p className="text-sm text-gray-600">
              Uploaded: {new Date(file.created_at).toLocaleDateString()}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}