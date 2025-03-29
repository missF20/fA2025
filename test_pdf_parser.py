"""
Test script for PDF parsing functionality
"""

import sys
import os
from utils.file_parser import parse_file
import base64

def main():
    """Main function to test PDF parsing"""
    
    # Check if file path was provided
    if len(sys.argv) < 2:
        print("Usage: python test_pdf_parser.py <path_to_pdf_file>")
        sys.exit(1)
        
    # Get the file path
    file_path = sys.argv[1]
    
    # Check if file exists
    if not os.path.exists(file_path):
        print(f"Error: File '{file_path}' not found.")
        sys.exit(1)
        
    # Get file extension
    _, ext = os.path.splitext(file_path)
    file_type = ext[1:].lower()  # Remove the dot
    
    print(f"Parsing file: {file_path}")
    print(f"File type: {file_type}")
    
    try:
        # Read the file
        with open(file_path, 'rb') as f:
            file_content = f.read()
            
        # Parse the file directly
        text, metadata = parse_file_content(file_content, file_type)
        
        # Print the results
        print("\nExtracted Text:")
        print("=" * 50)
        print(text[:500] + "..." if len(text) > 500 else text)
        print("=" * 50)
        
        print("\nMetadata:")
        print("=" * 50)
        for key, value in metadata.items():
            print(f"{key}: {value}")
            
        print("\nText length:", len(text))
        
    except Exception as e:
        print(f"Error parsing file: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    from utils.file_parser import parse_file_content
    main()