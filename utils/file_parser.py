"""
File Parser Utility

This module provides utilities for parsing various file types.
"""

import os
import logging
import json
import base64
from typing import Dict, List, Any, Optional, Union, Tuple
import tempfile

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