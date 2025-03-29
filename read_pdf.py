#!/usr/bin/env python3
"""
PDF Reader Script

This script reads the content of a PDF file and prints it to the console.
It's useful for examining PDF files that can't be viewed directly.
"""

import sys
import PyPDF2

def read_pdf(pdf_path):
    """
    Read and return the content of a PDF file
    
    Args:
        pdf_path (str): Path to the PDF file
        
    Returns:
        str: The text content of the PDF
    """
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = ""
        
        # Get information about the document
        info = reader.metadata
        if info:
            text += "Document Information:\n"
            for key, value in info.items():
                if key and value:
                    text += f"{key}: {value}\n"
            text += "\n"
        
        # Get the number of pages
        num_pages = len(reader.pages)
        text += f"Number of pages: {num_pages}\n\n"
        
        # Extract text from each page
        text += "Content:\n"
        for page_num in range(num_pages):
            page = reader.pages[page_num]
            text += f"--- Page {page_num + 1} ---\n"
            text += page.extract_text()
            text += "\n\n"
        
        return text

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python read_pdf.py <pdf_file_path>")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    try:
        content = read_pdf(pdf_path)
        print(content)
    except Exception as e:
        print(f"Error reading PDF: {e}")