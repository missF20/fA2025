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

export function KnowledgeBase() {
  const [files, setFiles] = useState<KnowledgeFile[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [success, setSuccess] = useState('');
  const [error, setError] = useState('');
  const { user } = useAuth();

  useEffect(() => {
    fetchKnowledgeFiles();
  }, []);

  async function fetchKnowledgeFiles() {
    try {
      const response = await fetch('/api/knowledge/files');
      const data = await response.json();
      setFiles(data);
      setIsLoading(false);
    } catch (err) {
      setError('Failed to fetch knowledge files');
      setIsLoading(false);
    }
  }

  async function handleFileUpload(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const fileInput = e.currentTarget.querySelector('input[type="file"]') as HTMLInputElement;
    const file = fileInput?.files?.[0];

    if (!file) return;

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch('/api/knowledge/upload', {
        method: 'POST',
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
  }

  return (
    <div className="p-6">
      <h2 className="text-2xl font-bold mb-6">Knowledge Base</h2>

      <div className="mb-8">
        <form onSubmit={handleFileUpload} className="flex gap-4 items-center">
          <input
            type="file"
            className="bg-white border rounded px-3 py-2"
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

      {error && <div className="text-red-600 mb-4">{error}</div>}
      {success && <div className="text-green-600 mb-4">{success}</div>}

      <div className="bg-white rounded-xl">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Your Knowledge Files</h3>

        {isLoading ? (
          <div className="flex justify-center py-8">
            <Loader2 size={24} className="animate-spin text-blue-500" />
          </div>
        ) : (
          <div className="divide-y">
            {files.map(file => (
              <div key={file.id} className="py-4 flex justify-between items-center">
                <div>
                  <p className="font-medium">{file.name}</p>
                  <p className="text-sm text-gray-500">
                    {new Date(file.created_at).toLocaleDateString()}
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}