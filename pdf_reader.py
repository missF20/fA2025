#!/usr/bin/env python3
"""
PDF Reader Tool

A simple utility to read and extract text from PDF documents.
"""

import os
import sys
import logging
from PyPDF2 import PdfReader

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def read_pdf(file_path):
    """
    Read PDF file and extract text content
    
    Args:
        file_path: Path to the PDF file
        
    Returns:
        Dict containing extracted content and metadata
    """
    try:
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return {"error": "File not found"}
            
        reader = PdfReader(file_path)
        
        # Extract metadata
        info = reader.metadata
        metadata = {}
        if info:
            for key in info:
                try:
                    metadata[key] = str(info[key])
                except:
                    metadata[key] = "Unable to decode metadata value"
        
        # Extract text from each page
        pages = []
        total_text = ""
        
        for i, page in enumerate(reader.pages):
            try:
                text = page.extract_text()
                if text:
                    total_text += text + "\n\n"
                    pages.append({
                        "page_number": i + 1,
                        "text": text
                    })
            except Exception as e:
                logger.error(f"Error extracting text from page {i+1}: {str(e)}")
                pages.append({
                    "page_number": i + 1,
                    "text": f"[Error extracting text: {str(e)}]"
                })
        
        result = {
            "success": True,
            "content": total_text,
            "metadata": metadata,
            "pages": pages,
            "page_count": len(reader.pages)
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Error reading PDF: {str(e)}")
        return {
            "success": False,
            "error": f"Failed to parse PDF: {str(e)}"
        }

def main():
    """Main function to run as a script"""
    if len(sys.argv) < 2:
        print("Usage: pdf_reader.py <path_to_pdf_file>")
        sys.exit(1)
        
    file_path = sys.argv[1]
    result = read_pdf(file_path)
    
    if result.get("success", False):
        print(f"PDF Information:")
        print(f"Pages: {result['page_count']}")
        print(f"Metadata: {result['metadata']}")
        print("\nContent:")
        print(result['content'])
    else:
        print(f"Error: {result.get('error', 'Unknown error')}")

if __name__ == "__main__":
    main()