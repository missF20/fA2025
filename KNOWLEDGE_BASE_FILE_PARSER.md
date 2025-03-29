# Knowledge Base File Parser

This document outlines the file parsing capabilities of the Dana AI Platform's knowledge base management system.

## Overview

The Knowledge Base File Parser is a utility that extracts content and metadata from various file types, enabling effective storage, search, and retrieval of information within the Dana AI platform. This document details how the file parser works and how to integrate it into your knowledge base operations.

## Supported File Types

The parser currently supports the following file types:

1. **PDF (.pdf)**
   - Full text extraction
   - Metadata extraction (title, author, creation date, etc.)
   - Page-by-page content extraction

2. **Microsoft Word (.docx)**
   - Full text extraction
   - Metadata extraction (title, author, creation date, etc.)
   - Paragraph-level content extraction

3. **Plain Text (.txt)**
   - Full text extraction
   - Line-by-line content access
   - Multiple encoding support (UTF-8, Latin-1, ASCII, UTF-16)

## Integration Methods

The file parser can be integrated with files in various formats:

### 1. Direct File Parsing

Parse files directly from binary data:

```python
from utils.file_parser import FileParser

# Read file binary data
with open('document.pdf', 'rb') as file:
    file_data = file.read()
    
# Parse the file
result = FileParser.parse_file(file_data, 'pdf')

if result.get('success', False):
    # Access the content and metadata
    content = result.get('content', '')
    metadata = result.get('metadata', {})
    
    # For specific file types, additional information is available
    if 'page_count' in result:  # PDF files
        print(f"PDF has {result['page_count']} pages")
    elif 'paragraph_count' in result:  # Word documents
        print(f"Document has {result['paragraph_count']} paragraphs")
```

### 2. Base64-Encoded File Parsing

Parse files from base64-encoded strings (useful for API integrations and web uploads):

```python
from utils.file_parser import FileParser
import base64

# Get base64-encoded file data (e.g., from an API or form)
with open('document.pdf', 'rb') as file:
    file_bytes = file.read()
    base64_data = base64.b64encode(file_bytes).decode('utf-8')

# Parse the base64 data
extracted_text, metadata = FileParser.parse_base64_file(base64_data, 'pdf')

if extracted_text:
    print("File parsed successfully")
    print(f"Content length: {len(extracted_text)} characters")
    print(f"Metadata: {metadata}")
```

### 3. Raw Content Parsing

Parse content that's already in string format (useful for already extracted text or API responses):

```python
from utils.file_parser import FileParser

# Assuming we have content from another source
content = "This is some text content from a document..."

# Parse the content (mainly useful for applying consistent processing)
extracted_text, metadata = FileParser.parse_file_content(content, 'txt')
```

## Search Functionality

The file parser includes a utility to extract relevant snippets from text based on search queries:

```python
from utils.file_parser import FileParser

# Assuming we have already extracted text content
content = "Large block of text from a parsed document..."

# Search for specific terms and get contextual snippets
query = "integration"
snippets = FileParser.extract_text_snippets(content, query, snippet_length=200)

# Display the snippets
for i, snippet in enumerate(snippets):
    print(f"Snippet {i+1}: {snippet}")
```

## Implementation in Knowledge Base API

The file parser is integrated into the Knowledge Base API in the following ways:

1. **File Upload Endpoint**: When uploading files to the knowledge base, the parser automatically extracts and stores content and metadata.

2. **Search Endpoint**: When searching the knowledge base, the parser helps generate relevant snippets and context from the stored documents.

3. **Content Extraction**: The parser supports converting various file formats into searchable text content.

## Error Handling

The file parser implements comprehensive error handling to ensure reliability:

1. **File Type Validation**: Validates supported file types before processing.

2. **Parsing Errors**: Catches and logs errors during the parsing process, returning informative error messages.

3. **Encoding Issues**: For text files, attempts multiple encodings to handle different character sets.

4. **Missing Dependencies**: Provides clear error messages if required libraries are missing.

## Security Considerations

1. **File Size Limits**: The knowledge base API enforces file size limits to prevent resource exhaustion attacks.

2. **Content Sanitization**: Text extraction includes sanitization to remove potentially harmful content.

3. **Temporary File Handling**: Secure handling of temporary files during parsing to prevent information leakage.

## Best Practices

1. **File Type Detection**: Always specify the correct file type when parsing to ensure optimal results.

2. **Error Handling**: Implement proper error handling when using the file parser to handle parsing failures gracefully.

3. **Large Files**: For very large files, consider implementing chunked processing or background jobs.

4. **Metadata Utilization**: Use extracted metadata to enhance search and organization of knowledge base content.

5. **Regular Updates**: Keep the file parser updated to support new file formats and improve extraction quality.

## Conclusion

The Knowledge Base File Parser is a powerful utility that enables Dana AI to efficiently manage and extract value from various document types. It supports the core knowledge management functionality of the platform and can be extended to support additional file types as needed.