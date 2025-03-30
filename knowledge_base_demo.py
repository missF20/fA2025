"""
Knowledge Base Demo Application

This is a simple Flask application to demonstrate the knowledge base functionality.
"""

from flask import Flask, render_template, request, jsonify, send_from_directory
import os
import base64
import json
from utils.file_parser import FileParser
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Ensure the uploads directory exists
UPLOAD_FOLDER = 'sample_docs'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/')
def index():
    """Render the main page"""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Knowledge Base Demo</title>
        <link href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css" rel="stylesheet">
        <style>
            body { padding: 20px; }
            .file-item { margin-bottom: 10px; border: 1px solid #ddd; padding: 10px; border-radius: 4px; }
            .file-content { white-space: pre-wrap; max-height: 300px; overflow-y: auto; background: #f8f9fa; padding: 10px; border-radius: 4px; margin-top: 10px; }
            .dragover { background-color: rgba(0, 123, 255, 0.1); border: 2px dashed #007bff; }
            #dropzone { border: 2px dashed #ccc; padding: 20px; text-align: center; margin-bottom: 20px; }
            .progress { margin-top: 10px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1 class="mb-4">Knowledge Base Demo</h1>
            
            <div class="row mb-4">
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header bg-primary text-white">
                            Upload Document
                        </div>
                        <div class="card-body">
                            <div id="dropzone" class="mb-3">
                                <p>Drag & drop files here or click to select</p>
                                <input type="file" id="fileInput" class="d-none">
                            </div>
                            
                            <div class="progress d-none" id="uploadProgress">
                                <div class="progress-bar" role="progressbar" style="width: 0%"></div>
                            </div>
                            
                            <div class="mt-3">
                                <button id="uploadBtn" class="btn btn-primary">Select File</button>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header bg-success text-white">
                            Search Documents
                        </div>
                        <div class="card-body">
                            <div class="input-group mb-3">
                                <input type="text" id="searchInput" class="form-control" placeholder="Enter search query">
                                <button class="btn btn-success" id="searchBtn">Search</button>
                            </div>
                            <div id="searchResults" class="mt-3"></div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="card">
                <div class="card-header bg-info text-white">
                    Document Library
                </div>
                <div class="card-body">
                    <div id="filesList" class="mt-3">Loading files...</div>
                </div>
            </div>
        </div>
        
        <script>
            document.addEventListener('DOMContentLoaded', function() {
                const dropzone = document.getElementById('dropzone');
                const fileInput = document.getElementById('fileInput');
                const uploadBtn = document.getElementById('uploadBtn');
                const uploadProgress = document.getElementById('uploadProgress');
                const progressBar = uploadProgress.querySelector('.progress-bar');
                const filesList = document.getElementById('filesList');
                const searchInput = document.getElementById('searchInput');
                const searchBtn = document.getElementById('searchBtn');
                const searchResults = document.getElementById('searchResults');
                
                // Load files on page load
                loadFiles();
                
                // Dropzone event handlers
                dropzone.addEventListener('dragover', function(e) {
                    e.preventDefault();
                    dropzone.classList.add('dragover');
                });
                
                dropzone.addEventListener('dragleave', function() {
                    dropzone.classList.remove('dragover');
                });
                
                dropzone.addEventListener('drop', function(e) {
                    e.preventDefault();
                    dropzone.classList.remove('dragover');
                    const files = e.dataTransfer.files;
                    if (files.length > 0) {
                        uploadFile(files[0]);
                    }
                });
                
                dropzone.addEventListener('click', function() {
                    fileInput.click();
                });
                
                uploadBtn.addEventListener('click', function() {
                    fileInput.click();
                });
                
                fileInput.addEventListener('change', function() {
                    if (fileInput.files.length > 0) {
                        uploadFile(fileInput.files[0]);
                    }
                });
                
                searchBtn.addEventListener('click', function() {
                    const query = searchInput.value.trim();
                    if (query) {
                        searchDocuments(query);
                    }
                });
                
                // Search with Enter key
                searchInput.addEventListener('keypress', function(e) {
                    if (e.key === 'Enter') {
                        const query = searchInput.value.trim();
                        if (query) {
                            searchDocuments(query);
                        }
                    }
                });
                
                function uploadFile(file) {
                    const reader = new FileReader();
                    
                    reader.onloadstart = function() {
                        uploadProgress.classList.remove('d-none');
                        progressBar.style.width = '0%';
                        progressBar.textContent = '0%';
                    };
                    
                    reader.onprogress = function(e) {
                        if (e.lengthComputable) {
                            const percentComplete = Math.round((e.loaded / e.total) * 100);
                            progressBar.style.width = percentComplete + '%';
                            progressBar.textContent = percentComplete + '%';
                        }
                    };
                    
                    reader.onload = function(e) {
                        progressBar.style.width = '100%';
                        progressBar.textContent = '100%';
                        
                        const base64Content = e.target.result.split(',')[1];
                        
                        fetch('/api/upload', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify({
                                filename: file.name,
                                content: base64Content,
                                file_type: file.type
                            })
                        })
                        .then(response => response.json())
                        .then(data => {
                            if (data.success) {
                                alert('File uploaded successfully!');
                                loadFiles();
                            } else {
                                alert('Error: ' + data.error);
                            }
                            
                            // Hide progress bar after a delay
                            setTimeout(() => {
                                uploadProgress.classList.add('d-none');
                            }, 1000);
                        })
                        .catch(error => {
                            alert('Upload failed: ' + error);
                            uploadProgress.classList.add('d-none');
                        });
                    };
                    
                    reader.onerror = function() {
                        alert('Error reading file');
                        uploadProgress.classList.add('d-none');
                    };
                    
                    reader.readAsDataURL(file);
                }
                
                function loadFiles() {
                    fetch('/api/files')
                    .then(response => response.json())
                    .then(data => {
                        if (data.files.length === 0) {
                            filesList.innerHTML = '<p>No files uploaded yet.</p>';
                            return;
                        }
                        
                        let html = '';
                        data.files.forEach(file => {
                            html += `
                                <div class="file-item">
                                    <div class="d-flex justify-content-between">
                                        <h5>${file.filename}</h5>
                                        <div>
                                            <button class="btn btn-sm btn-primary view-btn" data-id="${file.id}">View</button>
                                            <button class="btn btn-sm btn-danger delete-btn" data-id="${file.id}">Delete</button>
                                        </div>
                                    </div>
                                    <div class="file-details">
                                        <small class="text-muted">Type: ${file.file_type}</small> | 
                                        <small class="text-muted">Uploaded: ${new Date(file.upload_date).toLocaleString()}</small>
                                    </div>
                                    <div class="file-content d-none" id="content-${file.id}"></div>
                                </div>
                            `;
                        });
                        
                        filesList.innerHTML = html;
                        
                        // Add event listeners for buttons
                        document.querySelectorAll('.view-btn').forEach(btn => {
                            btn.addEventListener('click', function() {
                                const id = this.getAttribute('data-id');
                                const contentDiv = document.getElementById(`content-${id}`);
                                
                                if (contentDiv.classList.contains('d-none')) {
                                    // Load content if it's not yet loaded
                                    if (contentDiv.innerHTML === '') {
                                        contentDiv.innerHTML = 'Loading content...';
                                        
                                        fetch(`/api/files/${id}`)
                                        .then(response => response.json())
                                        .then(data => {
                                            if (data.success) {
                                                contentDiv.innerHTML = `<strong>Extracted Content:</strong><br>${data.content}`;
                                            } else {
                                                contentDiv.innerHTML = `<div class="text-danger">Error loading content: ${data.error}</div>`;
                                            }
                                        })
                                        .catch(error => {
                                            contentDiv.innerHTML = `<div class="text-danger">Error loading content: ${error}</div>`;
                                        });
                                    }
                                    
                                    contentDiv.classList.remove('d-none');
                                    this.textContent = 'Hide';
                                } else {
                                    contentDiv.classList.add('d-none');
                                    this.textContent = 'View';
                                }
                            });
                        });
                        
                        document.querySelectorAll('.delete-btn').forEach(btn => {
                            btn.addEventListener('click', function() {
                                const id = this.getAttribute('data-id');
                                if (confirm('Are you sure you want to delete this file?')) {
                                    fetch(`/api/files/${id}`, {
                                        method: 'DELETE'
                                    })
                                    .then(response => response.json())
                                    .then(data => {
                                        if (data.success) {
                                            alert('File deleted successfully');
                                            loadFiles();
                                        } else {
                                            alert('Error: ' + data.error);
                                        }
                                    })
                                    .catch(error => {
                                        alert('Delete failed: ' + error);
                                    });
                                }
                            });
                        });
                    })
                    .catch(error => {
                        filesList.innerHTML = `<div class="text-danger">Error loading files: ${error}</div>`;
                    });
                }
                
                function searchDocuments(query) {
                    searchResults.innerHTML = '<div class="text-center"><div class="spinner-border" role="status"><span class="visually-hidden">Loading...</span></div></div>';
                    
                    fetch(`/api/search?q=${encodeURIComponent(query)}`)
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            if (data.results.length === 0) {
                                searchResults.innerHTML = '<p>No results found.</p>';
                                return;
                            }
                            
                            let html = `<p>Found ${data.results.length} result(s):</p>`;
                            data.results.forEach(result => {
                                html += `
                                    <div class="card mb-3">
                                        <div class="card-header">
                                            <strong>${result.filename}</strong>
                                        </div>
                                        <div class="card-body">
                                            ${result.snippets.map(snippet => `<p>${snippet}</p>`).join('')}
                                        </div>
                                        <div class="card-footer">
                                            <button class="btn btn-sm btn-primary view-search-btn" data-id="${result.id}">View Full Document</button>
                                        </div>
                                    </div>
                                `;
                            });
                            
                            searchResults.innerHTML = html;
                            
                            // Add event listeners for buttons
                            document.querySelectorAll('.view-search-btn').forEach(btn => {
                                btn.addEventListener('click', function() {
                                    const id = this.getAttribute('data-id');
                                    
                                    // Find and click the corresponding view button in the file list
                                    const viewBtn = document.querySelector(`.view-btn[data-id="${id}"]`);
                                    if (viewBtn) {
                                        viewBtn.scrollIntoView({ behavior: 'smooth' });
                                        setTimeout(() => {
                                            viewBtn.click();
                                        }, 500);
                                    }
                                });
                            });
                        } else {
                            searchResults.innerHTML = `<div class="text-danger">Error: ${data.error}</div>`;
                        }
                    })
                    .catch(error => {
                        searchResults.innerHTML = `<div class="text-danger">Search failed: ${error}</div>`;
                    });
                }
            });
        </script>
    </body>
    </html>
    """

@app.route('/api/files')
def get_files():
    """Get a list of all files"""
    try:
        files = []
        for filename in os.listdir(UPLOAD_FOLDER):
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            if os.path.isfile(file_path):
                stat_info = os.stat(file_path)
                file_info = {
                    'id': filename,  # Using filename as ID for simplicity
                    'filename': filename,
                    'file_type': get_file_type(filename),
                    'upload_date': stat_info.st_mtime * 1000  # Convert to JS timestamp
                }
                files.append(file_info)
                
        # Sort by upload date (most recent first)
        files.sort(key=lambda x: x['upload_date'], reverse=True)
        
        return jsonify({
            'success': True,
            'files': files
        })
    
    except Exception as e:
        logger.error(f"Error getting files: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/files/<file_id>')
def get_file(file_id):
    """Get a specific file's content"""
    try:
        # Security check to prevent path traversal
        if '..' in file_id or '/' in file_id:
            return jsonify({
                'success': False,
                'error': 'Invalid file ID'
            })
            
        file_path = os.path.join(UPLOAD_FOLDER, file_id)
        if not os.path.exists(file_path):
            return jsonify({
                'success': False,
                'error': 'File not found'
            })
            
        # Read and parse the file
        with open(file_path, 'rb') as f:
            file_data = f.read()
            
        file_type = get_file_type(file_id)
        parser_type = get_parser_type(file_type)
        
        if parser_type:
            result = FileParser.parse_file(file_data, parser_type)
            if result.get('success', False):
                return jsonify({
                    'success': True,
                    'content': result.get('content', ''),
                    'metadata': result.get('metadata', {})
                })
            else:
                return jsonify({
                    'success': False,
                    'error': result.get('error', 'Failed to parse file')
                })
        else:
            # For unsupported file types, return raw content as text if possible
            try:
                content = file_data.decode('utf-8')
                return jsonify({
                    'success': True,
                    'content': content,
                    'metadata': {}
                })
            except UnicodeDecodeError:
                return jsonify({
                    'success': False,
                    'error': 'Unsupported file type'
                })
    
    except Exception as e:
        logger.error(f"Error getting file content: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/files/<file_id>', methods=['DELETE'])
def delete_file(file_id):
    """Delete a file"""
    try:
        # Security check to prevent path traversal
        if '..' in file_id or '/' in file_id:
            return jsonify({
                'success': False,
                'error': 'Invalid file ID'
            })
            
        file_path = os.path.join(UPLOAD_FOLDER, file_id)
        if not os.path.exists(file_path):
            return jsonify({
                'success': False,
                'error': 'File not found'
            })
            
        os.remove(file_path)
        
        return jsonify({
            'success': True,
            'message': 'File deleted successfully'
        })
    
    except Exception as e:
        logger.error(f"Error deleting file: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Upload a new file"""
    try:
        data = request.json
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            })
            
        filename = data.get('filename')
        content = data.get('content')
        file_type = data.get('file_type')
        
        if not filename or not content:
            return jsonify({
                'success': False,
                'error': 'Missing filename or content'
            })
            
        # Decode the base64 content
        file_data = base64.b64decode(content)
        
        # Save the file
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        with open(file_path, 'wb') as f:
            f.write(file_data)
            
        return jsonify({
            'success': True,
            'message': 'File uploaded successfully',
            'id': filename
        })
    
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/search')
def search_files():
    """Search for files containing the query"""
    try:
        query = request.args.get('q', '').strip()
        
        if not query:
            return jsonify({
                'success': False,
                'error': 'No query provided'
            })
            
        results = []
        
        for filename in os.listdir(UPLOAD_FOLDER):
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            if os.path.isfile(file_path):
                try:
                    with open(file_path, 'rb') as f:
                        file_data = f.read()
                        
                    file_type = get_file_type(filename)
                    parser_type = get_parser_type(file_type)
                    
                    if parser_type:
                        parse_result = FileParser.parse_file(file_data, parser_type)
                        if parse_result.get('success', False):
                            content = parse_result.get('content', '')
                            
                            # Check if the query is in the content
                            if query.lower() in content.lower():
                                # Get snippets containing the query
                                snippets = FileParser.extract_text_snippets(content, query)
                                
                                results.append({
                                    'id': filename,
                                    'filename': filename,
                                    'file_type': file_type,
                                    'snippets': snippets[:3]  # Limit to 3 snippets
                                })
                except Exception as e:
                    logger.error(f"Error processing file {filename} for search: {str(e)}")
                    continue
                        
        return jsonify({
            'success': True,
            'query': query,
            'results': results
        })
    
    except Exception as e:
        logger.error(f"Error searching files: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/sample_docs/<path:filename>')
def serve_file(filename):
    """Serve a file from the uploads folder"""
    return send_from_directory(UPLOAD_FOLDER, filename)

def get_file_type(filename):
    """Get the MIME type based on file extension"""
    ext = filename.lower().split('.')[-1]
    
    if ext == 'pdf':
        return 'application/pdf'
    elif ext == 'docx':
        return 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    elif ext == 'doc':
        return 'application/msword'
    elif ext == 'txt':
        return 'text/plain'
    else:
        return 'application/octet-stream'

def get_parser_type(file_type):
    """Map MIME type to parser type"""
    if 'pdf' in file_type:
        return 'pdf'
    elif 'wordprocessingml' in file_type or 'msword' in file_type:
        return 'docx'
    elif 'text/plain' in file_type:
        return 'txt'
    else:
        return None

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)