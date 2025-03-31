"""
File Parser Utility

This module provides utilities for parsing various file types and extracting their content.
Supports PDF, DOCX, and TXT files with extensibility for additional formats.
"""

import os
import logging
import json
import base64
from typing import Dict, List, Any, Optional, Union, Tuple
import tempfile
import re

# Configure logging
logger = logging.getLogger(__name__)

class FileParser:
    """Utility class for parsing different file types"""
    
    @staticmethod
    def parse_pdf(file_data: bytes) -> Dict[str, Any]:
        """
        Parse a PDF file
        
        Args:
            file_data: Raw PDF file data
            
        Returns:
            Dict containing extracted content and metadata
        """
        try:
            from PyPDF2 import PdfReader
            
            # Save file to temporary location
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
                temp_file.write(file_data)
                temp_path = temp_file.name
            
            try:
                # Open and parse PDF
                reader = PdfReader(temp_path)
                
                # Extract metadata
                info = reader.metadata
                metadata = {}
                if info:
                    for key in info:
                        metadata[key] = str(info[key])
                
                # Extract text from each page
                pages = []
                total_text = ""
                
                for i, page in enumerate(reader.pages):
                    text = page.extract_text()
                    if text:
                        total_text += text + "\n\n"
                        pages.append({
                            "page_number": i + 1,
                            "text": text
                        })
                
                result = {
                    "success": True,
                    "content": total_text,
                    "metadata": metadata,
                    "pages": pages,
                    "page_count": len(reader.pages)
                }
                
                return result
                
            finally:
                # Clean up temporary file
                os.unlink(temp_path)
                
        except ImportError:
            logger.error("PyPDF2 not installed. Install with: pip install PyPDF2")
            return {
                "success": False,
                "error": "PDF parser not available. Please install PyPDF2."
            }
            
        except Exception as e:
            logger.error(f"Error parsing PDF: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to parse PDF: {str(e)}"
            }
    
    @staticmethod
    def parse_docx(file_data: bytes) -> Dict[str, Any]:
        """
        Parse a DOCX file
        
        Args:
            file_data: Raw DOCX file data
            
        Returns:
            Dict containing extracted content and metadata
        """
        try:
            from docx import Document
            
            # Save file to temporary location
            with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as temp_file:
                temp_file.write(file_data)
                temp_path = temp_file.name
            
            try:
                # Open and parse DOCX
                doc = Document(temp_path)
                
                # Extract text
                full_text = ""
                paragraphs = []
                
                for para in doc.paragraphs:
                    if para.text:
                        full_text += para.text + "\n"
                        paragraphs.append(para.text)
                
                # Get basic metadata
                core_properties = doc.core_properties
                metadata = {}
                
                if core_properties:
                    metadata_attrs = [
                        'author', 'category', 'comments', 'content_status', 
                        'created', 'identifier', 'keywords', 'language', 
                        'last_modified_by', 'last_printed', 'modified', 
                        'revision', 'subject', 'title', 'version'
                    ]
                    
                    for attr in metadata_attrs:
                        if hasattr(core_properties, attr):
                            value = getattr(core_properties, attr)
                            if value is not None:
                                metadata[attr] = str(value)
                
                result = {
                    "success": True,
                    "content": full_text,
                    "metadata": metadata,
                    "paragraphs": paragraphs,
                    "paragraph_count": len(paragraphs)
                }
                
                return result
                
            finally:
                # Clean up temporary file
                os.unlink(temp_path)
                
        except ImportError:
            logger.error("python-docx not installed. Install with: pip install python-docx")
            return {
                "success": False,
                "error": "DOCX parser not available. Please install python-docx."
            }
            
        except Exception as e:
            logger.error(f"Error parsing DOCX: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to parse DOCX: {str(e)}"
            }
    
    @staticmethod
    def parse_txt(file_data: bytes) -> Dict[str, Any]:
        """
        Parse a TXT file
        
        Args:
            file_data: Raw TXT file data
            
        Returns:
            Dict containing extracted content
        """
        try:
            # Try to decode the text file with different encodings
            encodings = ['utf-8', 'latin-1', 'ascii', 'utf-16']
            content = None
            used_encoding = None
            
            for encoding in encodings:
                try:
                    content = file_data.decode(encoding)
                    used_encoding = encoding
                    break
                except UnicodeDecodeError:
                    continue
            
            if content is None:
                return {
                    "success": False,
                    "error": "Could not decode text file with any supported encoding."
                }
            
            # Split into lines
            lines = content.splitlines()
            
            result = {
                "success": True,
                "content": content,
                "encoding": used_encoding,
                "lines": lines,
                "line_count": len(lines)
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error parsing TXT: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to parse TXT: {str(e)}"
            }
    
    @staticmethod
    def parse_file(file_data: bytes, file_type: str) -> Dict[str, Any]:
        """
        Parse a file based on its type
        
        Args:
            file_data: Raw file data
            file_type: Type of file (pdf, docx, txt)
            
        Returns:
            Dict containing extracted content and metadata
        """
        file_type = file_type.lower()
        
        if file_type == 'pdf':
            return FileParser.parse_pdf(file_data)
        elif file_type in ['docx', 'doc']:
            return FileParser.parse_docx(file_data)
        elif file_type == 'txt':
            return FileParser.parse_txt(file_data)
        else:
            return {
                "success": False,
                "error": f"Unsupported file type: {file_type}"
            }
    
    @staticmethod
    def parse_base64_file(base64_data: str, file_type: str) -> Tuple[str, Dict[str, Any]]:
        """
        Parse a base64-encoded file
        
        Args:
            base64_data: Base64-encoded file data or data URL
            file_type: Type of file (pdf, docx, txt) or MIME type
            
        Returns:
            Tuple of (extracted_text, metadata)
        """
        try:
            logger.debug(f"Parsing base64 file of type: {file_type}")
            
            # Normalize file_type to handle MIME types
            normalized_type = file_type.lower()
            if '/' in normalized_type:
                # It's likely a MIME type (e.g., application/pdf)
                mime_parts = normalized_type.split('/')
                if len(mime_parts) == 2:
                    main_type, sub_type = mime_parts
                    if main_type == 'application':
                        if sub_type in ['pdf', 'vnd.openxmlformats-officedocument.wordprocessingml.document']:
                            normalized_type = 'pdf' if sub_type == 'pdf' else 'docx'
                    elif main_type == 'text':
                        normalized_type = 'txt'
            elif normalized_type.startswith('.'):
                normalized_type = normalized_type[1:]  # Remove leading dot
                
            # Handle file extensions
            if normalized_type in ['doc', 'docx', 'word']:
                normalized_type = 'docx'
            elif normalized_type in ['pdf']:
                normalized_type = 'pdf'
            elif normalized_type in ['txt', 'text', 'plain', 'md', 'markdown']:
                normalized_type = 'txt'
                
            logger.debug(f"Normalized file type: {normalized_type}")
            
            # Check if input is a data URL
            if isinstance(base64_data, str) and base64_data.startswith('data:'):
                # Extract the base64 part
                try:
                    # Format: data:[<MIME-type>][;charset=<encoding>][;base64],<data>
                    parts = base64_data.split(',', 1)
                    if len(parts) != 2:
                        raise ValueError("Invalid data URL format")
                        
                    # Get the base64 data part
                    base64_data = parts[1]
                    
                    # Also try to extract MIME type if file_type is not specific
                    if not normalized_type or normalized_type == 'unknown':
                        header = parts[0].lower()
                        if 'application/pdf' in header:
                            normalized_type = 'pdf'
                        elif 'wordprocessingml' in header or 'msword' in header:
                            normalized_type = 'docx'
                        elif 'text/' in header:
                            normalized_type = 'txt'
                            
                    logger.debug(f"Extracted base64 data from data URL, detected type: {normalized_type}")
                except Exception as e:
                    logger.error(f"Error parsing data URL: {str(e)}")
            
            # Convert base64 to bytes
            try:
                file_bytes = base64.b64decode(base64_data)
                logger.debug(f"Successfully decoded base64 data, size: {len(file_bytes)} bytes")
            except Exception as e:
                logger.error(f"Base64 decoding error: {str(e)}")
                return "", {}
            
            # Parse the file based on normalized type
            result = FileParser.parse_file(file_bytes, normalized_type)
            
            if not result.get('success', False):
                error_msg = result.get('error', 'Unknown error')
                logger.error(f"Error parsing base64 file: {error_msg}")
                return "", {}
            
            # Return extracted text and metadata
            extracted_text = result.get('content', '')
            metadata = result.get('metadata', {})
            
            logger.debug(f"Successfully parsed file. Text length: {len(extracted_text)}, metadata keys: {list(metadata.keys())}")
            return extracted_text, metadata
            
        except Exception as e:
            logger.error(f"Error parsing base64 file: {str(e)}", exc_info=True)
            return "", {}
    
    @staticmethod
    def parse_file_content(content: str, file_type: str) -> Tuple[str, Dict[str, Any]]:
        """
        Parse file content (raw content as string) based on its type
        
        Args:
            content: Raw file content as string
            file_type: Type of file (primarily for txt)
            
        Returns:
            Tuple of (extracted_text, metadata)
        """
        try:
            # For text files, we can just return the content
            if file_type.lower() in ['txt', 'text', 'plain']:
                return content, {}
            
            # For other file types, we need to convert to bytes and parse
            # This is primarily a fallback - using parse_base64_file or parse_file is preferred
            file_bytes = content.encode('utf-8')
            result = FileParser.parse_file(file_bytes, file_type)
            
            if not result.get('success', False):
                logger.error(f"Error parsing file content: {result.get('error', 'Unknown error')}")
                return content, {}  # Return original content on failure
            
            # Return extracted text and metadata
            extracted_text = result.get('content', '')
            metadata = result.get('metadata', {})
            
            return extracted_text, metadata
            
        except Exception as e:
            logger.error(f"Error parsing file content: {str(e)}")
            return content, {}  # Return original content on failure
            
    @staticmethod
    def extract_text_snippets(text: str, query: str, snippet_length: int = 200) -> List[str]:
        """
        Extract relevant text snippets containing the query
        
        Args:
            text: Full text to search in
            query: Search query to find
            snippet_length: Approximate length of each snippet (characters)
            
        Returns:
            List of text snippets
        """
        try:
            snippets = []
            query_lower = query.lower()
            text_lower = text.lower()
            
            # Find all occurrences of the query in the text
            index = 0
            while index < len(text_lower):
                pos = text_lower.find(query_lower, index)
                if pos == -1:
                    break
                    
                # Calculate snippet boundaries
                half_length = snippet_length // 2
                start = max(0, pos - half_length)
                end = min(len(text), pos + len(query) + half_length)
                
                # Find word boundaries if possible
                if start > 0:
                    # Find the first space before the start point
                    space_before = text.rfind(' ', 0, start)
                    if space_before != -1:
                        start = space_before + 1
                
                if end < len(text):
                    # Find the first space after the end point
                    space_after = text.find(' ', end)
                    if space_after != -1:
                        end = space_after
                
                # Extract snippet and add to results
                snippet = text[start:end].strip()
                
                # Add ellipsis if needed
                if start > 0:
                    snippet = "..." + snippet
                if end < len(text):
                    snippet = snippet + "..."
                    
                snippets.append(snippet)
                
                # Move index to after this occurrence
                index = pos + len(query)
            
            return snippets
            
        except Exception as e:
            logger.error(f"Error extracting snippets: {str(e)}")
            return []