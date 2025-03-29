"""
PDF Parser Test

This script tests the PDF parsing functionality.
"""

import os
import sys
import json
import base64
import logging
from utils.file_parser import FileParser

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_pdf_parser():
    """Test the PDF parser with a sample PDF file"""
    
    # Get test file path - this should be a path to a valid PDF file
    if len(sys.argv) > 1:
        test_file_path = sys.argv[1]
    else:
        test_file_path = "attached_assets/Untitled document (1).pdf"
    
    # Check if file exists
    if not os.path.isfile(test_file_path):
        logger.error(f"Test file not found: {test_file_path}")
        logger.info("Usage: python test_pdf_parser.py [path_to_pdf_file]")
        return
    
    logger.info(f"Testing PDF parser with file: {test_file_path}")
    
    try:
        # Read file
        with open(test_file_path, 'rb') as f:
            file_data = f.read()
        
        # Parse file
        result = FileParser.parse_pdf(file_data)
        
        # Print result
        if result["success"]:
            logger.info("PDF parsing successful!")
            logger.info(f"Page count: {result['page_count']}")
            logger.info(f"Content length: {len(result['content'])} characters")
            
            # Print metadata
            if result["metadata"]:
                logger.info("Metadata:")
                for key, value in result["metadata"].items():
                    logger.info(f"  {key}: {value}")
            
            # Print content snippets
            if result["content"]:
                content_preview = result["content"][:200] + "..." if len(result["content"]) > 200 else result["content"]
                logger.info(f"Content preview: {content_preview}")
            
            # Print page info
            logger.info("Pages:")
            for page in result["pages"]:
                page_preview = page["text"][:50] + "..." if len(page["text"]) > 50 else page["text"]
                logger.info(f"  Page {page['page_number']}: {page_preview}")
        else:
            logger.error(f"PDF parsing failed: {result['error']}")
    
    except Exception as e:
        logger.error(f"Error testing PDF parser: {str(e)}")

if __name__ == "__main__":
    test_pdf_parser()