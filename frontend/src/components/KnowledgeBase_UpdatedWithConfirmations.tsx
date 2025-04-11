import React, { useState, useEffect, useCallback, useRef } from 'react';
import { 
  Button, Card, Container, Row, Col, Form, Table, 
  Badge, Spinner, Alert, Modal, Toast, ToastContainer 
} from 'react-bootstrap';
import { 
  FiTrash2, FiSearch, FiRefreshCw, FiUpload, FiFileText, 
  FiAlertCircle, FiCheckCircle, FiAlertTriangle, FiInfo 
} from 'react-icons/fi';
import { 
  getKnowledgeFiles, deleteKnowledgeFile, getCategories, 
  bulkDeleteKnowledgeFiles 
} from '../services/knowledgeService';
import { KnowledgeFile } from '../types';
import KnowledgeFileUpload from './KnowledgeFileUpload';
import KnowledgeFilePreview from './KnowledgeFilePreview';
import KnowledgeSearch from './KnowledgeSearch';
import './KnowledgeBase.css';

const KnowledgeBase: React.FC = () => {
  // State variables
  const [files, setFiles] = useState<KnowledgeFile[]>([]);
  const [totalFiles, setTotalFiles] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<KnowledgeFile | null>(null);
  const [showUpload, setShowUpload] = useState<boolean>(false);
  const [showSearch, setShowSearch] = useState<boolean>(false);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [filterCategory, setFilterCategory] = useState<string>('');
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [itemsPerPage] = useState<number>(10);
  const [refreshTrigger, setRefreshTrigger] = useState<number>(0);
  const [lastDeletedId, setLastDeletedId] = useState<string | null>(null);
  const [deleteStatus, setDeleteStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');
  const [deleteMessage, setDeleteMessage] = useState<string>('');
  
  // New state variables for enhanced UI
  const [showDeleteModal, setShowDeleteModal] = useState<boolean>(false);
  const [fileToDelete, setFileToDelete] = useState<{id: string, name: string} | null>(null);
  const [showToast, setShowToast] = useState<boolean>(false);
  const [toastMessage, setToastMessage] = useState<string>('');
  const [toastVariant, setToastVariant] = useState<'success' | 'danger' | 'warning' | 'info'>('info');
  const [showBulkDeleteModal, setShowBulkDeleteModal] = useState<boolean>(false);
  const [recentlyUsedWarning, setRecentlyUsedWarning] = useState<boolean>(false);
  
  // Mock function to check if file was recently used (in real implementation, this would make an API call)
  const checkIfFileRecentlyUsed = (fileId: string): boolean => {
    // For demonstration - check if file ID ends with a specific character
    // In a real implementation, this would check against actual usage data
    return fileId.endsWith('a') || fileId.endsWith('e');
  };

  // Function to fetch knowledge files
  const fetchFiles = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const offset = (currentPage - 1) * itemsPerPage;
      const result = await getKnowledgeFiles(itemsPerPage, offset);
      setFiles(result.files || []);
      setTotalFiles(result.total || 0);
      
      // Log the file info for debugging
      console.log(`Fetched ${result.files?.length || 0} files out of ${result.total || 0} total`);
    } catch (err) {
      setError('Failed to load knowledge files. Please try again.');
      console.error('Error fetching knowledge files:', err);
    } finally {
      setLoading(false);
    }
  }, [currentPage, itemsPerPage, refreshTrigger]);

  // Function to fetch categories
  const fetchCategories = useCallback(async () => {
    try {
      const categoriesData = await getCategories();
      setCategories(categoriesData.map(cat => cat.name));
    } catch (err) {
      console.error('Error fetching categories:', err);
    }
  }, []);

  // Load files and categories on mount and when refreshTrigger changes
  useEffect(() => {
    fetchFiles();
    fetchCategories();
  }, [fetchFiles, fetchCategories, refreshTrigger]);

  // Show toast message
  const showToastMessage = (message: string, variant: 'success' | 'danger' | 'warning' | 'info' = 'info') => {
    setToastMessage(message);
    setToastVariant(variant);
    setShowToast(true);
  };

  // Handle file selection for preview
  const handleSelectFile = (file: KnowledgeFile) => {
    setSelectedFile(file);
  };

  // Handle file selection for bulk actions (checkbox)
  const handleToggleSelect = (file: KnowledgeFile) => {
    setSelectedIds(prev => {
      if (prev.includes(file.id)) {
        return prev.filter(id => id !== file.id);
      } else {
        return [...prev, file.id];
      }
    });
  };

  // Handle bulk selection of all files
  const handleSelectAll = () => {
    if (selectedIds.length === files.length) {
      setSelectedIds([]);
    } else {
      setSelectedIds(files.map(file => file.id));
    }
  };

  // Handle file upload completion
  const handleUploadComplete = () => {
    setShowUpload(false);
    setRefreshTrigger(prev => prev + 1);
    setSelectedFile(null);
    showToastMessage('File uploaded successfully', 'success');
  };

  // Initiate file deletion (shows confirmation modal)
  const initiateDeleteFile = (fileId: string) => {
    const fileToDelete = files.find(f => f.id === fileId);
    if (!fileToDelete) return;
    
    // Check if the file was recently used
    const wasRecentlyUsed = checkIfFileRecentlyUsed(fileId);
    setRecentlyUsedWarning(wasRecentlyUsed);
    
    setFileToDelete({
      id: fileId,
      name: fileToDelete.file_name || fileToDelete.filename || 'Unnamed file'
    });
    setShowDeleteModal(true);
  };
  
  // Initiate bulk delete (shows confirmation modal)
  const initiateBulkDelete = () => {
    if (selectedIds.length === 0) return;
    
    // Check if any of the selected files were recently used
    const anyRecentlyUsed = selectedIds.some(id => checkIfFileRecentlyUsed(id));
    setRecentlyUsedWarning(anyRecentlyUsed);
    
    setShowBulkDeleteModal(true);
  };

  // Handle file deletion with improved error handling and user feedback
  const handleDeleteFile = async (fileId: string) => {
    setShowDeleteModal(false);
    setDeleteStatus('loading');
    setLastDeletedId(fileId);
    setDeleteMessage('Deleting file...');
    
    try {
      console.log(`Attempting to delete file with ID: ${fileId}`);
      const result = await deleteKnowledgeFile(fileId);
      console.log(`Delete result:`, result);
      
      // Remove file from state
      setFiles(prevFiles => prevFiles.filter(file => file.id !== fileId));
      setSelectedIds(prev => prev.filter(id => id !== fileId));
      
      // If the deleted file was the selected file, clear selection
      if (selectedFile && selectedFile.id === fileId) {
        setSelectedFile(null);
      }
      
      setDeleteStatus('success');
      setDeleteMessage('File successfully deleted');
      
      // Show success toast
      showToastMessage('File successfully deleted', 'success');
      
      // Refresh the file list after a short delay
      setTimeout(() => {
        setRefreshTrigger(prev => prev + 1);
        setDeleteStatus('idle');
      }, 2000);
      
    } catch (error) {
      console.error(`Error deleting file:`, error);
      setDeleteStatus('error');
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      setDeleteMessage(`Failed to delete file: ${errorMessage}`);
      
      // Show error toast
      showToastMessage(`Failed to delete file: ${errorMessage}`, 'danger');
      
      // Reset error message after a delay
      setTimeout(() => {
        setDeleteStatus('idle');
      }, 5000);
    }
  };

  // Handle bulk file deletion
  const handleBulkDelete = async () => {
    setShowBulkDeleteModal(false);
    
    if (selectedIds.length === 0) {
      return;
    }
    
    setDeleteStatus('loading');
    setDeleteMessage(`Deleting ${selectedIds.length} files...`);
    
    try {
      await bulkDeleteKnowledgeFiles(selectedIds);
      
      // Remove files from state
      setFiles(prevFiles => prevFiles.filter(file => !selectedIds.includes(file.id)));
      
      // If the deleted file was the selected file, clear selection
      if (selectedFile && selectedIds.includes(selectedFile.id)) {
        setSelectedFile(null);
      }
      
      // Show success toast
      showToastMessage(`Successfully deleted ${selectedIds.length} files`, 'success');
      
      setDeleteStatus('success');
      setDeleteMessage(`${selectedIds.length} files successfully deleted`);
      
      // Clear selection
      setSelectedIds([]);
      
      // Refresh the file list after a short delay
      setTimeout(() => {
        setRefreshTrigger(prev => prev + 1);
        setDeleteStatus('idle');
      }, 2000);
      
    } catch (error) {
      console.error(`Error deleting files:`, error);
      setDeleteStatus('error');
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      setDeleteMessage(`Failed to delete files: ${errorMessage}`);
      
      // Show error toast
      showToastMessage(`Failed to delete files: ${errorMessage}`, 'danger');
      
      // Reset error message after a delay
      setTimeout(() => {
        setDeleteStatus('idle');
      }, 5000);
    }
  };

  // Handle category filter change
  const handleFilterChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setFilterCategory(e.target.value);
    setCurrentPage(1);
  };

  // Filter files by category
  const filteredFiles = filterCategory 
    ? files.filter(file => file.category === filterCategory)
    : files;

  // Pagination setup
  const totalPages = Math.ceil(totalFiles / itemsPerPage);
  
  const handlePageChange = (page: number) => {
    setCurrentPage(page);
  };

  // Format file size for display (KB, MB, etc.)
  const formatFileSize = (bytes?: number) => {
    if (!bytes) return '0 B';
    const units = ['B', 'KB', 'MB', 'GB'];
    let size = bytes;
    let unitIndex = 0;
    
    while (size >= 1024 && unitIndex < units.length - 1) {
      size /= 1024;
      unitIndex++;
    }
    
    return `${size.toFixed(1)} ${units[unitIndex]}`;
  };

  return (
    <Container fluid className="knowledge-base-container">
      <h2 className="mb-4">Knowledge Base</h2>
      
      {/* Error and status messages */}
      {error && <Alert variant="danger">{error}</Alert>}
      
      {deleteStatus !== 'idle' && (
        <Alert variant={deleteStatus === 'error' ? 'danger' : 
                        deleteStatus === 'success' ? 'success' : 'info'}>
          {deleteMessage}
        </Alert>
      )}
      
      {/* Toasts */}
      <ToastContainer position="top-end" className="p-3">
        <Toast 
          show={showToast} 
          onClose={() => setShowToast(false)}
          delay={5000}
          autohide
          bg={toastVariant}
        >
          <Toast.Header closeButton>
            <strong className="me-auto">
              {toastVariant === 'success' && <FiCheckCircle className="me-2" />}
              {toastVariant === 'danger' && <FiAlertCircle className="me-2" />}
              {toastVariant === 'warning' && <FiAlertTriangle className="me-2" />}
              {toastVariant === 'info' && <FiInfo className="me-2" />}
              Knowledge Base
            </strong>
          </Toast.Header>
          <Toast.Body className={toastVariant === 'danger' ? 'text-white' : ''}>
            {toastMessage}
          </Toast.Body>
        </Toast>
      </ToastContainer>
      
      {/* Delete Confirmation Modal */}
      <Modal show={showDeleteModal} onHide={() => setShowDeleteModal(false)}>
        <Modal.Header closeButton>
          <Modal.Title>
            <FiAlertTriangle className="text-warning me-2" /> Confirm Deletion
          </Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <p>Are you sure you want to delete the file: <strong>{fileToDelete?.name}</strong>?</p>
          <p>This action cannot be undone.</p>
          
          {recentlyUsedWarning && (
            <Alert variant="warning">
              <FiAlertTriangle className="me-2" />
              <strong>Warning:</strong> This file has been recently used in conversations or workflows. 
              Deleting it may impact existing operations.
            </Alert>
          )}
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowDeleteModal(false)}>
            Cancel
          </Button>
          <Button 
            variant="danger" 
            onClick={() => fileToDelete && handleDeleteFile(fileToDelete.id)}
          >
            Delete File
          </Button>
        </Modal.Footer>
      </Modal>
      
      {/* Bulk Delete Confirmation Modal */}
      <Modal show={showBulkDeleteModal} onHide={() => setShowBulkDeleteModal(false)}>
        <Modal.Header closeButton>
          <Modal.Title>
            <FiAlertTriangle className="text-warning me-2" /> Confirm Bulk Deletion
          </Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <p>Are you sure you want to delete <strong>{selectedIds.length}</strong> files?</p>
          <p>This action cannot be undone.</p>
          
          {recentlyUsedWarning && (
            <Alert variant="warning">
              <FiAlertTriangle className="me-2" />
              <strong>Warning:</strong> One or more of these files have been recently used
              in conversations or workflows. Deleting them may impact existing operations.
            </Alert>
          )}
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowBulkDeleteModal(false)}>
            Cancel
          </Button>
          <Button 
            variant="danger" 
            onClick={handleBulkDelete}
          >
            Delete {selectedIds.length} Files
          </Button>
        </Modal.Footer>
      </Modal>
      
      {/* Action buttons */}
      <div className="action-buttons mb-4">
        <Button 
          variant="primary" 
          onClick={() => setShowUpload(true)}
          className="me-2"
        >
          <FiUpload /> Upload Files
        </Button>
        
        <Button 
          variant="outline-secondary" 
          onClick={() => setShowSearch(!showSearch)}
          className="me-2"
        >
          <FiSearch /> {showSearch ? 'Hide Search' : 'Search'}
        </Button>
        
        <Button 
          variant="outline-secondary" 
          onClick={() => setRefreshTrigger(prev => prev + 1)}
          className="me-2"
          disabled={loading}
        >
          <FiRefreshCw className={loading ? 'spin' : ''} /> Refresh
        </Button>
        
        {selectedIds.length > 0 && (
          <Button 
            variant="danger" 
            onClick={initiateBulkDelete}
            className="me-2"
          >
            <FiTrash2 /> Delete Selected ({selectedIds.length})
          </Button>
        )}
        
        {/* Category filter */}
        <Form.Group className="d-inline-block filter-group">
          <Form.Select 
            value={filterCategory} 
            onChange={handleFilterChange}
            className="form-select-sm"
          >
            <option value="">All Categories</option>
            {categories.map(category => (
              <option key={category} value={category}>{category}</option>
            ))}
          </Form.Select>
        </Form.Group>
      </div>
      
      {/* Search component */}
      {showSearch && (
        <Card className="mb-4">
          <Card.Body>
            <KnowledgeSearch onSearch={() => {}} />
          </Card.Body>
        </Card>
      )}
      
      {/* File upload component */}
      {showUpload && (
        <Card className="mb-4">
          <Card.Body>
            <KnowledgeFileUpload 
              onClose={() => setShowUpload(false)} 
              onComplete={handleUploadComplete}
            />
          </Card.Body>
        </Card>
      )}
      
      {/* Main content */}
      <Row>
        {/* File list */}
        <Col lg={selectedFile ? 7 : 12}>
          <Card>
            <Card.Body>
              <h5 className="mb-3">Files {loading && <Spinner animation="border" size="sm" />}</h5>
              
              {loading && files.length === 0 ? (
                <div className="text-center p-4">
                  <Spinner animation="border" />
                </div>
              ) : filteredFiles.length === 0 ? (
                <div className="text-center p-4">
                  <p className="text-muted">No files found</p>
                  <Button variant="primary" onClick={() => setShowUpload(true)}>
                    <FiUpload /> Upload Files
                  </Button>
                </div>
              ) : (
                <>
                  <Table hover responsive>
                    <thead>
                      <tr>
                        <th>
                          <Form.Check 
                            type="checkbox" 
                            checked={selectedIds.length === files.length && files.length > 0}
                            onChange={handleSelectAll}
                          />
                        </th>
                        <th>Name</th>
                        <th>Type</th>
                        <th>Size</th>
                        <th>Category</th>
                        <th>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredFiles.map(file => (
                        <tr 
                          key={file.id} 
                          className={`file-row ${selectedFile?.id === file.id ? 'selected' : ''} ${lastDeletedId === file.id && deleteStatus === 'loading' ? 'deleting' : ''}`}
                          onClick={() => handleSelectFile(file)}
                        >
                          <td onClick={e => { e.stopPropagation(); handleToggleSelect(file); }}>
                            <Form.Check 
                              type="checkbox" 
                              checked={selectedIds.includes(file.id)}
                              onChange={() => {}}
                            />
                          </td>
                          <td>
                            <div className="file-name-cell">
                              <FiFileText className="file-icon" />
                              <span>{file.file_name || file.filename}</span>
                              {checkIfFileRecentlyUsed(file.id) && (
                                <Badge 
                                  bg="warning" 
                                  text="dark" 
                                  className="ms-2" 
                                  title="This file was recently used in conversations or workflows"
                                >
                                  Active
                                </Badge>
                              )}
                            </div>
                          </td>
                          <td>
                            <Badge bg="secondary">
                              {file.file_type?.split('/')[1] || 'unknown'}
                            </Badge>
                          </td>
                          <td>{formatFileSize(file.file_size)}</td>
                          <td>
                            {file.category ? (
                              <Badge bg="info">{file.category}</Badge>
                            ) : (
                              <span className="text-muted">—</span>
                            )}
                          </td>
                          <td>
                            <Button 
                              variant="outline-danger" 
                              size="sm"
                              onClick={(e) => {
                                e.stopPropagation();
                                initiateDeleteFile(file.id);
                              }}
                              aria-label="Delete file"
                              disabled={deleteStatus === 'loading' && lastDeletedId === file.id}
                            >
                              {deleteStatus === 'loading' && lastDeletedId === file.id ? (
                                <Spinner animation="border" size="sm" />
                              ) : (
                                <FiTrash2 />
                              )}
                            </Button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </Table>
                  
                  {/* Pagination */}
                  {totalPages > 1 && (
                    <div className="d-flex justify-content-between align-items-center mt-3">
                      <div>
                        Showing {filteredFiles.length} of {totalFiles} files
                      </div>
                      <div className="pagination-controls">
                        <Button 
                          variant="outline-secondary" 
                          size="sm"
                          onClick={() => handlePageChange(currentPage - 1)}
                          disabled={currentPage === 1}
                          className="me-2"
                        >
                          Previous
                        </Button>
                        
                        <span className="mx-2">
                          Page {currentPage} of {totalPages}
                        </span>
                        
                        <Button 
                          variant="outline-secondary" 
                          size="sm"
                          onClick={() => handlePageChange(currentPage + 1)}
                          disabled={currentPage === totalPages}
                          className="ms-2"
                        >
                          Next
                        </Button>
                      </div>
                    </div>
                  )}
                </>
              )}
            </Card.Body>
          </Card>
        </Col>
        
        {/* File preview */}
        {selectedFile && (
          <Col lg={5}>
            <KnowledgeFilePreview 
              file={selectedFile} 
              onClose={() => setSelectedFile(null)}
              onDelete={initiateDeleteFile}
            />
          </Col>
        )}
      </Row>
    </Container>
  );
};

export default KnowledgeBase;