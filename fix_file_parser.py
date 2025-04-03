"""
Fix File Parser

This script adds the missing parse_file method to the FileParser class.
"""

import os
import sys
import logging
from typing import Dict, Any

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def fix_file_parser():
    """Add the parse_file method to the FileParser class"""
    try:
        # Define the path to the file parser
        file_parser_path = os.path.join('utils', 'file_parser.py')
        
        # Read the current content
        with open(file_parser_path, 'r') as file:
            content = file.read()
        
        # Check if parse_file method already exists
        if 'def parse_file(' in content:
            print("parse_file method already exists, skipping...")
            return
        
        # Find the location to insert the new method
        # Let's add it after parse_base64 method, before parse_file_content
        insertion_point = content.find('def parse_file_content(')
        
        if insertion_point == -1:
            print("Could not find insertion point, looking for alternative...")
            insertion_point = content.find('def extract_text_snippets(')
        
        if insertion_point == -1:
            print("Could not find suitable insertion point, aborting...")
            return
        
        # Create the new method content
        parse_file_method = '''    @staticmethod
    def parse_file(file_data: bytes, file_type: str) -> Dict[str, Any]:
        """
        Parse a file based on its type
        
        Args:
            file_data: Raw file data as bytes
            file_type: Type of file (pdf, docx, txt) or MIME type
            
        Returns:
            Dict containing extracted content, metadata, and success indicator
        """
        try:
            logger.debug(f"Parsing file of type: {file_type}")
            
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
            
            # Process based on file type
            if normalized_type == 'pdf':
                return FileParser.parse_pdf(file_data)
            elif normalized_type == 'docx':
                return FileParser.parse_docx(file_data)
            elif normalized_type == 'txt':
                return FileParser.parse_txt(file_data)
            else:
                # Fallback to trying to parse as text
                logger.warning(f"Unknown file type '{file_type}', trying to parse as text")
                return FileParser.parse_txt(file_data)
                
        except Exception as e:
            logger.error(f"Error parsing file: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": f"Failed to parse file: {str(e)}",
                "content": "",
                "metadata": {}
            }
'''
        
        # Insert the new method
        updated_content = content[:insertion_point] + parse_file_method + content[insertion_point:]
        
        # Write the updated content back to the file
        with open(file_parser_path, 'w') as file:
            file.write(updated_content)
            
        print("Successfully added parse_file method to FileParser class")
        
    except Exception as e:
        logger.error(f"Error fixing file parser: {str(e)}", exc_info=True)

if __name__ == "__main__":
    fix_file_parser()