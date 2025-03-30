
import React, { useState, useEffect } from 'react';
import { useAuth } from '../hooks/useAuth';
import { Loader2 } from 'lucide-react';

interface KnowledgeFile {
  id: string;
  name: string;
  size: number;
  type: string;
  created_at: string;
}

export default function KnowledgeBase() {
  const { user } = useAuth();
  const [files, setFiles] = useState<KnowledgeFile[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [uploadProgress, setUploadProgress] = useState<number>(0);

  useEffect(() => {
    fetchKnowledgeFiles();
  }, []);

  const fetchKnowledgeFiles = async () => {
    try {
      const response = await fetch('/api/knowledge/files', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      const data = await response.json();
      setFiles(data.files);
    } catch (err) {
      setError('Failed to fetch knowledge files');
    } finally {
      setIsLoading(false);
    }
  };

  const handleFileUpload = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    const file = formData.get('file') as File;

    if (!file) {
      setError('Please select a file');
      return;
    }

    try {
      setUploadProgress(0);
      const response = await fetch('/api/knowledge/upload', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: formData
      });

      if (response.ok) {
        setSuccess('File uploaded successfully');
        fetchKnowledgeFiles();
      } else {
        setError('Failed to upload file');
      }
    } catch (err) {
      setError('Error uploading file');
    }
  };

  const handleFileDelete = async (fileId: string) => {
    try {
      const response = await fetch(`/api/knowledge/files/${fileId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (response.ok) {
        setSuccess('File deleted successfully');
        setFiles(files.filter(file => file.id !== fileId));
      } else {
        setError('Failed to delete file');
      }
    } catch (err) {
      setError('Error deleting file');
    }
  };

  return (
    <div className="p-6">
      <h2 className="text-2xl font-bold mb-6">Knowledge Base</h2>

      <div className="mb-8">
        <form onSubmit={handleFileUpload} className="flex gap-4 items-center">
          <input
            type="file"
            name="file"
            className="border p-2 rounded"
            accept=".pdf,.doc,.docx,.txt"
          />
          <button
            type="submit"
            className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
          >
            Upload
          </button>
        </form>
      </div>

      {error && (
        <div className="bg-red-100 text-red-700 p-4 rounded mb-4">
          {error}
        </div>
      )}

      {success && (
        <div className="bg-green-100 text-green-700 p-4 rounded mb-4">
          {success}
        </div>
      )}

      <div className="bg-white rounded-xl">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Your Knowledge Files</h3>

        {isLoading ? (
          <div className="flex justify-center py-8">
            <Loader2 size={24} className="animate-spin text-blue-500" />
          </div>
        ) : (
          <div className="divide-y">
            {files.map((file) => (
              <div key={file.id} className="py-4 flex justify-between items-center">
                <div>
                  <p className="font-medium">{file.name}</p>
                  <p className="text-sm text-gray-500">
                    Size: {(file.size / 1024).toFixed(2)} KB • 
                    Added: {new Date(file.created_at).toLocaleDateString()}
                  </p>
                </div>
                <button
                  onClick={() => handleFileDelete(file.id)}
                  className="text-red-600 hover:text-red-800"
                >
                  Delete
                </button>
              </div>
            ))}
            {files.length === 0 && (
              <p className="py-4 text-gray-500 text-center">
                No files uploaded yet
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
