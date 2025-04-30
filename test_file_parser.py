"""
Test File Parser

This script tests the file parser functionality, particularly for DOCX files.
"""

import os
import sys
from utils.file_parser import FileParser

def test_docx_parser():
    """
    Test parsing a DOCX file
    """
    print("Testing DOCX file parser...")
    
    docx_path = "sample_docs/dana_knowledge_base.docx"
    
    # Check if file exists
    if not os.path.exists(docx_path):
        print(f"❌ Error: Test file {docx_path} not found!")
        return False
    
    # Read the file
    with open(docx_path, "rb") as f:
        file_data = f.read()
    
    # Parse the file
    try:
        result = FileParser.parse_docx(file_data)
        if result.get("success"):
            print("✅ Successfully parsed DOCX file!")
            print(f"Content length: {len(result.get('content', ''))} characters")
            print(f"Paragraphs: {result.get('paragraph_count', 0)}")
            print(f"Metadata: {result.get('metadata', {})}")
            return True
        else:
            print(f"❌ Error parsing DOCX file: {result.get('error', 'Unknown error')}")
            return False
    except Exception as e:
        print(f"❌ Exception during DOCX parsing: {str(e)}")
        return False

if __name__ == "__main__":
    test_docx_parser()