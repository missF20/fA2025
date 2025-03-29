# Dana AI Knowledge Base Module

## Overview

The Knowledge Base module is a core component of the Dana AI Platform that enables organizations to store, organize, and retrieve information effectively. This module provides robust file parsing capabilities for various document formats (PDF, DOCX, TXT) along with advanced search functionality.

## Features

- **Multi-format document parsing**: Extract content and metadata from PDF, DOCX, and TXT files
- **Advanced search capabilities**: Full-text search with relevant snippet extraction
- **Metadata extraction**: Automatically extract and index document metadata
- **Base64 support**: Process base64-encoded files for easy API integration
- **Secure file handling**: Properly manage temporary files and sanitize content
- **Comprehensive error handling**: Graceful handling of parsing errors and unsupported formats

## Getting Started

### Installation

The Knowledge Base module is included in the Dana AI Platform and requires the following dependencies:

- PyPDF2 (for PDF parsing)
- python-docx (for DOCX parsing)

These dependencies are installed by default in the Dana AI environment.

### Basic Usage

#### 1. Uploading Files to Knowledge Base

Files can be uploaded to the knowledge base through the REST API:

```bash
curl -X POST https://your-dana-api.com/api/knowledge/files \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "file_name": "product_overview.pdf",
    "file_type": "pdf",
    "content": "base64_encoded_file_content",
    "is_base64": true
  }'
```

#### 2. Searching the Knowledge Base

Search across all knowledge base files:

```bash
curl -X GET "https://your-dana-api.com/api/knowledge/search?query=integration&include_snippets=true" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### 3. Retrieving File Information

Get file metadata without content:

```bash
curl -X GET "https://your-dana-api.com/api/knowledge/files/FILE_ID?exclude_content=true" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Integration with Other Dana AI Components

The Knowledge Base module integrates with other Dana AI components:

- **Conversation System**: Automatically retrieve relevant information when responding to user queries
- **Automation Engine**: Include knowledge base content in automated workflows
- **User Dashboard**: Browse and search knowledge base files through the web interface

## File Parser Utilities

The Knowledge Base module includes powerful file parsing utilities that can be used programmatically:

```python
from utils.file_parser import FileParser

# Parse a PDF file
with open('document.pdf', 'rb') as f:
    pdf_data = f.read()
    result = FileParser.parse_pdf(pdf_data)
    
    if result.get('success'):
        content = result.get('content')
        metadata = result.get('metadata')
        page_count = result.get('page_count')
        
        print(f"Successfully parsed {page_count} pages")
        
# Search within content
search_term = "integration"
snippets = FileParser.extract_text_snippets(content, search_term)

for snippet in snippets:
    print(f"Found match: {snippet}")
```

## Security

The Knowledge Base module implements several security measures:

1. **User Isolation**: All knowledge base content is isolated by user account
2. **Authentication**: All endpoints require valid authentication
3. **Content Validation**: Files are validated before processing
4. **Secure Temporary Files**: Temporary files are securely handled and cleaned up

## Testing

The repository includes several test scripts to verify knowledge base functionality:

- `test_knowledge_operations.py`: Tests file parsing and search operations
- `demonstrate_pdf_parser.py`: Demonstrates PDF parsing capabilities
- `create_sample_docx.py`: Creates a sample DOCX file for testing

To run the tests:

```bash
python test_knowledge_operations.py path/to/file.pdf --search "your search term"
```

## Documentation

For more detailed information, see the following documentation files:

- [KNOWLEDGE_BASE_API.md](KNOWLEDGE_BASE_API.md): API documentation for knowledge base endpoints
- [KNOWLEDGE_BASE_FILE_PARSER.md](KNOWLEDGE_BASE_FILE_PARSER.md): Detailed explanation of file parsing capabilities