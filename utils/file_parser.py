"""
File Parser Module

This module provides utilities for parsing different file types to extract content
for use in the knowledge base.
"""

import logging
import io
import os
import base64
from typing import Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)

def extract_text_from_pdf(file_content: bytes) -> Tuple[str, Optional[Dict[str, Any]]]:
    """
    Extract text content from a PDF file
    
    Args:
        file_content: Binary file content
        
    Returns:
        Tuple of (extracted text, metadata dictionary or None)
    """
    try:
        from PyPDF2 import PdfReader
        
        # Create a PDF reader object
        pdf = PdfReader(io.BytesIO(file_content))
        
        # Get the number of pages
        num_pages = len(pdf.pages)
        
        # Extract text from each page
        text = ""
        for page_num in range(num_pages):
            page = pdf.pages[page_num]
            text += page.extract_text() + "\n\n"
            
        # Create metadata with page count
        metadata = {
            "page_count": num_pages,
            "version": pdf.pdf_header if hasattr(pdf, 'pdf_header') else "Unknown"
        }
        
        return text, metadata
        
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {str(e)}", exc_info=True)
        return "", None


def extract_text_from_docx(file_content: bytes) -> Tuple[str, Optional[Dict[str, Any]]]:
    """
    Extract text content from a DOCX file
    
    Args:
        file_content: Binary file content
        
    Returns:
        Tuple of (extracted text, metadata dictionary or None)
    """
    try:
        from docx import Document
        
        # Create a document object
        doc = Document(io.BytesIO(file_content))
        
        # Extract text from paragraphs
        text = ""
        for para in doc.paragraphs:
            text += para.text + "\n"
            
        # Extract text from tables
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    text += cell.text + " "
                text += "\n"
                
        # Create metadata with paragraph and table counts
        metadata = {
            "paragraph_count": len(doc.paragraphs),
            "table_count": len(doc.tables)
        }
        
        return text, metadata
        
    except Exception as e:
        logger.error(f"Error extracting text from DOCX: {str(e)}", exc_info=True)
        return "", None


def extract_text_from_txt(file_content: bytes) -> Tuple[str, Optional[Dict[str, Any]]]:
    """
    Extract text content from a plain text file
    
    Args:
        file_content: Binary file content
        
    Returns:
        Tuple of (extracted text, metadata dictionary or None)
    """
    try:
        # Decode the bytes to string
        text = file_content.decode('utf-8')
        
        # Create metadata with line count
        line_count = text.count('\n') + 1
        metadata = {
            "line_count": line_count,
            "character_count": len(text)
        }
        
        return text, metadata
        
    except UnicodeDecodeError:
        # Try another encoding if UTF-8 fails
        try:
            text = file_content.decode('latin-1')
            
            # Create metadata with line count
            line_count = text.count('\n') + 1
            metadata = {
                "line_count": line_count,
                "character_count": len(text),
                "encoding": "latin-1"
            }
            
            return text, metadata
            
        except Exception as e:
            logger.error(f"Error decoding text file: {str(e)}", exc_info=True)
            return "", None
            
    except Exception as e:
        logger.error(f"Error extracting text from TXT: {str(e)}", exc_info=True)
        return "", None


def parse_file_content(file_content: bytes, file_type: str) -> Tuple[str, Optional[Dict[str, Any]]]:
    """
    Parse file content based on file type
    
    Args:
        file_content: Binary file content
        file_type: File type/extension (pdf, docx, txt, etc.)
        
    Returns:
        Tuple of (extracted text, metadata dictionary or None)
    """
    file_type = file_type.lower()
    
    if file_type == 'pdf':
        return extract_text_from_pdf(file_content)
    elif file_type in ['docx', 'doc']:
        return extract_text_from_docx(file_content)
    elif file_type == 'txt':
        return extract_text_from_txt(file_content)
    else:
        logger.warning(f"Unsupported file type: {file_type}")
        return "", None


def parse_file(file_path: str) -> Tuple[str, Optional[Dict[str, Any]]]:
    """
    Parse a file from disk
    
    Args:
        file_path: Path to the file
        
    Returns:
        Tuple of (extracted text, metadata dictionary or None)
    """
    try:
        # Get file extension
        _, file_extension = os.path.splitext(file_path)
        file_type = file_extension[1:].lower()  # Remove the dot
        
        # Read file content
        with open(file_path, 'rb') as f:
            file_content = f.read()
            
        return parse_file_content(file_content, file_type)
        
    except Exception as e:
        logger.error(f"Error parsing file {file_path}: {str(e)}", exc_info=True)
        return "", None


def parse_base64_file(base64_content: str, file_type: str) -> Tuple[str, Optional[Dict[str, Any]]]:
    """
    Parse a file from base64 encoded content
    
    Args:
        base64_content: Base64 encoded file content
        file_type: File type/extension (pdf, docx, txt, etc.)
        
    Returns:
        Tuple of (extracted text, metadata dictionary or None)
    """
    try:
        # Decode base64 content
        file_content = base64.b64decode(base64_content)
        
        return parse_file_content(file_content, file_type)
        
    except Exception as e:
        logger.error(f"Error parsing base64 file: {str(e)}", exc_info=True)
        return "", None