#!/usr/bin/env python3
"""
Test Knowledge Base Operations

A script to test knowledge base file operations using the enhanced file parser utility.
This script demonstrates how to parse different file types and search within them.
"""

import os
import base64
import json
import argparse
from utils.file_parser import FileParser

def test_parse_file(file_path):
    """
    Test parsing a file using direct method
    
    Args:
        file_path: Path to the file
    """
    _, ext = os.path.splitext(file_path)
    file_type = ext[1:] if ext else 'txt'
    
    try:
        with open(file_path, 'rb') as file:
            file_data = file.read()
            
            print(f"\nDirect file parsing ({file_type}):")
            result = FileParser.parse_file(file_data, file_type)
            
            if result.get('success', False):
                print(f"- File parsed successfully")
                
                if file_type == 'pdf':
                    print(f"- Page count: {result.get('page_count', 0)}")
                elif file_type in ['docx', 'doc']:
                    print(f"- Paragraph count: {result.get('paragraph_count', 0)}")
                elif file_type == 'txt':
                    print(f"- Line count: {result.get('line_count', 0)}")
                
                # Print metadata if available
                metadata = result.get('metadata', {})
                if metadata:
                    print(f"- Metadata: {json.dumps(metadata, indent=2)[:200]}...")
                
                # Print content excerpt
                content = result.get('content', '')
                print(f"- Content excerpt (first 150 chars): {content[:150]}...")
                
                return content
            else:
                print(f"- Error parsing file: {result.get('error', 'Unknown error')}")
                return None
    except Exception as e:
        print(f"Error reading file: {str(e)}")
        return None

def test_parse_base64(file_path):
    """
    Test parsing a file using base64 encoding
    
    Args:
        file_path: Path to the file
    """
    _, ext = os.path.splitext(file_path)
    file_type = ext[1:] if ext else 'txt'
    
    try:
        with open(file_path, 'rb') as file:
            file_data = file.read()
            base64_data = base64.b64encode(file_data).decode('utf-8')
            
            print(f"\nBase64 file parsing ({file_type}):")
            extracted_text, metadata = FileParser.parse_base64_file(base64_data, file_type)
            
            if extracted_text:
                print(f"- File parsed successfully from base64")
                
                # Print metadata if available
                if metadata:
                    print(f"- Metadata: {json.dumps(metadata, indent=2)[:200]}...")
                
                # Print content excerpt
                print(f"- Content excerpt (first 150 chars): {extracted_text[:150]}...")
                
                return extracted_text
            else:
                print(f"- Error parsing base64 file data")
                return None
    except Exception as e:
        print(f"Error with base64 encoding/parsing: {str(e)}")
        return None

def test_search_content(content, query, snippet_length=200):
    """
    Test searching content for a query
    
    Args:
        content: Text content to search
        query: Search query string
        snippet_length: Length of each snippet
    """
    if not content or not query:
        print(f"\nSkipping search: Content or query is empty")
        return
    
    print(f"\nText snippet extraction (searching for '{query}'):")
    try:
        snippets = FileParser.extract_text_snippets(content, query, snippet_length)
        
        if snippets:
            print(f"- Found {len(snippets)} instances of '{query}'")
            
            for i, snippet in enumerate(snippets[:3]):  # Show up to 3 snippets
                print(f"- Snippet {i+1}: {snippet}")
        else:
            print(f"- No instances of '{query}' found in content")
    except Exception as e:
        print(f"Error extracting snippets: {str(e)}")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Test knowledge base file operations')
    parser.add_argument('file', help='Path to file for testing')
    parser.add_argument('--search', '-s', help='Search query to test', default='integration')
    parser.add_argument('--length', '-l', type=int, help='Snippet length', default=200)
    
    args = parser.parse_args()
    
    if not os.path.exists(args.file):
        print(f"Error: File not found: {args.file}")
        return
    
    print(f"Testing file operations with: {args.file}")
    print(f"Search query: '{args.search}'")
    print(f"Snippet length: {args.length}")
    
    # Test direct parsing
    content = test_parse_file(args.file)
    
    # Test base64 parsing
    test_parse_base64(args.file)
    
    # Test search functionality
    if content:
        test_search_content(content, args.search, args.length)

if __name__ == "__main__":
    main()