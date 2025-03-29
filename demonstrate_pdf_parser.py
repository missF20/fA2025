#!/usr/bin/env python3
"""
Demonstrate PDF Parser

A script to showcase the usage of the enhanced file parser utility with PDF files.
"""

import os
import sys
import base64
import json
from utils.file_parser import FileParser

def demonstrate_pdf_parsing(pdf_path):
    """
    Demonstrate reading and parsing a PDF file using the FileParser utility
    
    Args:
        pdf_path: Path to PDF file
    """
    print(f"Demonstrating PDF parsing with file: {pdf_path}")
    
    # 1. Direct parsing of the PDF file
    try:
        with open(pdf_path, 'rb') as file:
            file_data = file.read()
            
            print("\n1. Direct PDF parsing:")
            result = FileParser.parse_pdf(file_data)
            
            if result.get('success', False):
                print(f"  PDF parsed successfully")
                print(f"  Page count: {result.get('page_count', 0)}")
                print(f"  Metadata: {json.dumps(result.get('metadata', {}), indent=2)}")
                print(f"  Content excerpt (first 150 chars): {result.get('content', '')[:150]}...")
            else:
                print(f"  Error parsing PDF: {result.get('error', 'Unknown error')}")
    except Exception as e:
        print(f"Error reading file: {str(e)}")
    
    # 2. Base64 encoding and parsing
    try:
        with open(pdf_path, 'rb') as file:
            file_data = file.read()
            base64_data = base64.b64encode(file_data).decode('utf-8')
            
            print("\n2. Base64 PDF parsing:")
            extracted_text, metadata = FileParser.parse_base64_file(base64_data, 'pdf')
            
            if extracted_text:
                print(f"  PDF parsed successfully from base64")
                print(f"  Metadata: {json.dumps(metadata, indent=2)}")
                print(f"  Content excerpt (first 150 chars): {extracted_text[:150]}...")
            else:
                print(f"  Error parsing base64 PDF data")
    except Exception as e:
        print(f"Error with base64 encoding/parsing: {str(e)}")
    
    # 3. Extract snippets
    try:
        with open(pdf_path, 'rb') as file:
            file_data = file.read()
            result = FileParser.parse_pdf(file_data)
            
            if result.get('success', False):
                content = result.get('content', '')
                query = "integration"  # Example search term
                
                print(f"\n3. Text snippet extraction (searching for '{query}'):")
                snippets = FileParser.extract_text_snippets(content, query)
                
                for i, snippet in enumerate(snippets[:3]):  # Show up to 3 snippets
                    print(f"  Snippet {i+1}: {snippet}")
            else:
                print(f"  Error extracting snippets: File parsing failed")
    except Exception as e:
        print(f"Error extracting snippets: {str(e)}")

def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: demonstrate_pdf_parser.py <path_to_pdf_file>")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    if not os.path.exists(pdf_path):
        print(f"Error: File not found: {pdf_path}")
        sys.exit(1)
    
    demonstrate_pdf_parsing(pdf_path)

if __name__ == "__main__":
    main()