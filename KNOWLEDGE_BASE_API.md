# Knowledge Base API Documentation

## Overview

The Knowledge Base API provides comprehensive endpoints for managing knowledge files, searching, categorizing, and tagging content. It supports various file formats including PDF, DOCX, TXT, and HTML, with automatic content extraction and metadata parsing.

The API features a resilient architecture with direct endpoint registration that ensures high availability and fault tolerance. This implementation bypasses the standard Flask blueprint registration system to guarantee consistent access to knowledge management functionality even when other system components experience issues.

## Key Features

- File upload with automatic content extraction
- Support for multiple file types (PDF, DOCX, TXT, HTML)
- File metadata extraction
- Tagging and categorization
- Advanced search with filtering and snippets
- Content management (create, read, update, delete)
- Direct endpoint registration for enhanced reliability
- Redundant access paths to critical functionality
- Fault-tolerant architecture with automatic recovery

## API Endpoints

### List Knowledge Files

```
GET /api/knowledge/files
```

Retrieves a paginated list of knowledge files for the authenticated user.

**Query Parameters:**
- `limit` (optional) - Maximum number of files to return (default: 20)
- `offset` (optional) - Offset for pagination (default: 0)

**Response Example:**
```json
{
  "files": [
    {
      "id": "123",
      "user_id": "user_456",
      "file_name": "product_catalog.pdf",
      "file_size": 1024567,
      "file_type": "application/pdf",
      "category": "Product Information",
      "tags": ["catalog", "products", "2023"],
      "created_at": "2023-06-15T14:30:45Z",
      "updated_at": "2023-06-15T14:30:45Z"
    },
    ...
  ],
  "total": 45,
  "limit": 20,
  "offset": 0
}
```

### Get File Details

```
GET /api/knowledge/files/{file_id}
```

Retrieves detailed information about a specific knowledge file.

**Query Parameters:**
- `exclude_content` (optional) - Set to 'true' to exclude file content in response (default: false)

**Response Example:**
```json
{
  "id": "123",
  "user_id": "user_456",
  "file_name": "product_catalog.pdf",
  "file_size": 1024567,
  "file_type": "application/pdf",
  "content": "Lorem ipsum dolor sit amet...",
  "category": "Product Information",
  "tags": ["catalog", "products", "2023"],
  "metadata": {
    "author": "John Smith",
    "title": "Product Catalog 2023",
    "pages": 42
  },
  "created_at": "2023-06-15T14:30:45Z",
  "updated_at": "2023-06-15T14:30:45Z"
}
```

### Upload File

```
POST /api/knowledge/files
```

Uploads a new file to the knowledge base with automatic content extraction.

**Request Body:**
```json
{
  "file_name": "product_catalog.pdf",
  "file_size": 1024567,
  "file_type": "application/pdf",
  "content": "base64_encoded_file_content",
  "is_base64": true,
  "category": "Product Information",
  "tags": ["catalog", "products", "2023"]
}
```

**Response Example:**
```json
{
  "message": "File uploaded successfully",
  "file": {
    "id": "123",
    "user_id": "user_456",
    "file_name": "product_catalog.pdf",
    "file_size": 1024567,
    "file_type": "application/pdf",
    "category": "Product Information",
    "tags": ["catalog", "products", "2023"],
    "created_at": "2023-06-15T14:30:45Z",
    "updated_at": "2023-06-15T14:30:45Z"
  }
}
```

### Update File

```
PUT /api/knowledge/files/{file_id}
```

Updates an existing knowledge file.

**Request Body:**
```json
{
  "file_name": "updated_product_catalog.pdf",
  "content": "updated_content",
  "category": "Updated Category",
  "tags": ["updated", "tags"]
}
```

**Response Example:**
```json
{
  "message": "File updated successfully",
  "file": {
    "id": "123",
    "user_id": "user_456",
    "file_name": "updated_product_catalog.pdf",
    "file_size": 1024567,
    "file_type": "application/pdf",
    "category": "Updated Category",
    "tags": ["updated", "tags"],
    "created_at": "2023-06-15T14:30:45Z",
    "updated_at": "2023-06-16T09:12:33Z"
  }
}
```

### Delete File

```
DELETE /api/knowledge/files/{file_id}
```

Deletes a knowledge file.

**Response Example:**
```json
{
  "message": "File deleted successfully"
}
```

### Search Knowledge Base

```
GET /api/knowledge/search
```

Searches the knowledge base for specific content.

**Query Parameters:**
- `query` (required) - Search term
- `category` (optional) - Filter by category
- `file_type` (optional) - Filter by file type
- `tags` (optional) - Comma-separated list of tags to filter by
- `limit` (optional) - Maximum number of results (default: 20)
- `include_snippets` (optional) - Whether to include text snippets in results (default: false)

**Response Example:**
```json
{
  "query": "product specifications",
  "filters": {
    "category": "Product Information",
    "file_type": "application/pdf",
    "tags": ["catalog", "specifications"]
  },
  "results": [
    {
      "id": "123",
      "file_name": "product_catalog.pdf",
      "file_type": "application/pdf",
      "category": "Product Information",
      "tags": ["catalog", "specifications", "2023"],
      "created_at": "2023-06-15T14:30:45Z",
      "updated_at": "2023-06-15T14:30:45Z",
      "snippets": [
        "...detailed product specifications for all models...",
        "...refer to the product specifications section on page 24..."
      ]
    },
    ...
  ],
  "count": 3,
  "limit": 20
}
```

### Get Categories

```
GET /api/knowledge/files/categories
```

Retrieves all categories used in the knowledge base.

**Response Example:**
```json
{
  "categories": [
    "Product Information",
    "Technical Documentation",
    "Marketing Materials",
    "Research Papers"
  ]
}
```

### Get Tags

```
GET /api/knowledge/files/tags
```

Retrieves all tags used in the knowledge base.

**Response Example:**
```json
{
  "tags": [
    "catalog",
    "documentation",
    "marketing",
    "products",
    "research",
    "specifications",
    "technical",
    "2023"
  ]
}
```

## File Parsing

The system automatically extracts content and metadata from uploaded files based on their format:

### PDF Upload Endpoint

```
POST /api/knowledge/pdf-upload
```

Specialized endpoint for uploading PDF files to the knowledge base with improved handling.

**Request:**
- Content-Type: `multipart/form-data`
- File must be sent as a form field named `file`
- Additional metadata can be included as form fields:
  - `category` (optional) - Category to associate with the file
  - `tags` (optional) - JSON array of tags as a string

**Response Example:**
```json
{
  "success": true,
  "file": {
    "id": "42782b4d-7de6-4b5f-8650-d430a0e3e935",
    "user_id": "c94900e9-d587-4798-a3b0-38b92f3971dd",
    "filename": "document.pdf",
    "file_type": "application/pdf",
    "file_size": 12658,
    "created_at": "2025-04-20T15:50:53.685956",
    "updated_at": "2025-04-20T15:50:53.685956"
  },
  "message": "PDF document.pdf uploaded successfully"
}
```

### Supported File Types

1. **PDF**
   - Extracts text content from all pages
   - Retrieves metadata (author, title, creator, etc.)
   - Preserves page structure in output
   - Specialized upload endpoint for improved handling

2. **DOCX**
   - Extracts paragraphs and text content
   - Retrieves document properties (author, created date, etc.)
   - Maintains basic text formatting

3. **TXT**
   - Directly uses text content
   - Simple text processing for readability

4. **HTML**
   - Strips HTML tags to extract plain text
   - Preserves content structure where possible
   - Handles basic HTML entities

## Implementing Client Integration

To integrate with the Knowledge Base API, follow these steps:

1. **Authentication**: All requests require a valid user authentication token in the `Authorization` header as `Bearer {token}`.

2. **File Upload**:
   - Convert file to base64 before sending
   - Specify correct file type for accurate parsing
   - Add categories and tags for better organization

3. **Searching**:
   - Use specific search terms for better results
   - Apply filters to narrow down search scope
   - Request snippets for context in search results

4. **Real-time Updates**:
   - Listen for WebSocket events for real-time notifications
   - Available events: `new_knowledge_file`, `knowledge_file_updated`, `knowledge_file_deleted`

## Error Handling

Common error responses include:

| Status Code | Description |
| ----------- | ----------- |
| 400 | Bad Request - Invalid parameters or missing required fields |
| 401 | Unauthorized - Authentication required |
| 404 | Not Found - Requested file doesn't exist or isn't accessible |
| 500 | Server Error - Internal server error |

## Code Example: Uploading a File

### Standard File Upload (Base64)

```javascript
async function uploadFile(file, token) {
  // Read file as base64
  const reader = new FileReader();
  
  return new Promise((resolve, reject) => {
    reader.onload = async () => {
      const base64Content = reader.result.split(',')[1];
      
      try {
        const response = await fetch('/api/knowledge/files', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            file_name: file.name,
            file_size: file.size,
            file_type: file.type,
            content: base64Content,
            is_base64: true,
            category: 'Documentation',
            tags: ['upload', 'example']
          })
        });
        
        const result = await response.json();
        resolve(result);
      } catch (error) {
        reject(error);
      }
    };
    
    reader.onerror = () => {
      reject(new Error('Failed to read file'));
    };
    
    reader.readAsDataURL(file);
  });
}
```

### PDF-Specific Upload (FormData)

```javascript
async function uploadPdfFile(file, token, category = '', tags = []) {
  // Use FormData for multipart/form-data uploads
  const formData = new FormData();
  formData.append('file', file);
  
  // Add optional metadata
  if (category) {
    formData.append('category', category);
  }
  
  if (tags && tags.length > 0) {
    formData.append('tags', JSON.stringify(tags));
  }
  
  try {
    // Force cache invalidation by adding timestamp parameter
    const timestamp = new Date().getTime();
    const response = await fetch(`/api/knowledge/pdf-upload?t=${timestamp}`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`
        // Do not set Content-Type header, browser will set it with boundary
      },
      body: formData
    });
    
    const result = await response.json();
    
    // Clear cache to ensure fresh data on next listing
    if (result.success) {
      await fetch('/api/knowledge/files?force_refresh=true', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
    }
    
    return result;
  } catch (error) {
    console.error('PDF upload failed:', error);
    throw error;
  }
}
```

## Code Example: Searching

```javascript
async function searchKnowledgeBase(query, filters, token) {
  const params = new URLSearchParams({
    query: query
  });
  
  if (filters.category) {
    params.append('category', filters.category);
  }
  
  if (filters.file_type) {
    params.append('file_type', filters.file_type);
  }
  
  if (filters.tags && filters.tags.length > 0) {
    params.append('tags', filters.tags.join(','));
  }
  
  if (filters.include_snippets) {
    params.append('include_snippets', 'true');
  }
  
  try {
    const response = await fetch(`/api/knowledge/search?${params.toString()}`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    return await response.json();
  } catch (error) {
    console.error('Search failed:', error);
    throw error;
  }
}
```

## Resilient Architecture

The Knowledge Base API implements a resilient architecture designed to ensure high availability and fault tolerance:

1. **Direct Endpoint Registration**:
   - Critical endpoints are registered directly with the Flask application
   - Bypasses the Flask blueprint registration system that may fail in certain conditions
   - Ensures knowledge management functionality remains available even when other components experience issues

2. **Redundant Access Paths**:
   - Multiple ways to access the same functionality
   - Both blueprint-based and direct routes to key features
   - Automatic failover between access methods

3. **Database Connection Handling**:
   - Robust connection management with automatic retry mechanisms
   - Fallback connection methods when primary approaches fail
   - Connection pooling to optimize performance

4. **Error Recovery**:
   - Comprehensive error handling with graceful degradation
   - Automatic recovery from transient failures
   - Detailed logging for troubleshooting

## Best Practices

1. **File Handling**:
   - Keep files under 50MB for optimal performance
   - Use appropriate file types for different content (PDFs for formatted documents, TXT for plain text)
   - Include meaningful file names to improve searchability

2. **Content Organization**:
   - Use consistent category names
   - Apply relevant tags to improve searchability
   - Update metadata when content changes

3. **Search Optimization**:
   - Use specific search terms
   - Combine search with filters
   - Request snippets only when needed to reduce payload size

4. **Performance Considerations**:
   - Paginate file lists for large knowledge bases
   - Exclude content when retrieving file lists
   - Cache frequently accessed files client-side
   - Use the force_refresh parameter when you need the latest data