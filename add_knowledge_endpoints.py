#!/usr/bin/env python3
"""
Add Knowledge Endpoints Directly to Main App

This script adds direct endpoints to handle knowledge base operations
in the main application, bypassing the blueprint registration mechanism.
"""
import logging
import sys
import traceback
from flask import Flask, Blueprint, jsonify, request
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_knowledge_endpoints():
    """
    Add knowledge endpoints directly to main.py 
    This ensures they're available regardless of blueprint registration
    """
    try:
        with open('main.py', 'r') as f:
            content = f.read()
        
        # Check if the direct knowledge endpoint is already added
        if "def knowledge_files_api():" in content:
            logger.info("Knowledge endpoints already added to main.py")
            return True
        
        # Find the insertion point right before the app run line
        insert_point = "if __name__ == \"__main__\":"
        
        # Prepare the direct endpoint code
        direct_endpoints = """
# Direct knowledge API endpoints
@app.route('/api/knowledge/files', methods=['GET'])
def knowledge_files_api():
    # Direct endpoint for knowledge files API
    try:
        # Import only when needed to avoid circular imports
        from routes.knowledge import get_knowledge_files
        from flask import request
        return get_knowledge_files()
    except Exception as e:
        logger.error(f"Error in direct knowledge files endpoint: {str(e)}")
        return jsonify({"error": "Knowledge files API error", "details": str(e)}), 500

@app.route('/api/knowledge/files/binary', methods=['POST'])
def binary_upload_api():
    # Direct endpoint for binary file upload
    try:
        # Import only when needed to avoid circular imports
        from routes.knowledge_binary import upload_binary_file
        return upload_binary_file()
    except Exception as e:
        logger.error(f"Error in direct binary upload endpoint: {str(e)}")
        return jsonify({"error": "Binary upload API error", "details": str(e)}), 500

@app.route('/api/knowledge/search', methods=['GET', 'POST'])
def knowledge_search_api():
    # Direct endpoint for knowledge search API
    try:
        # Import search function from knowledge blueprint
        from routes.knowledge import search_knowledge_base
        return search_knowledge_base()
    except Exception as e:
        logger.error(f"Error in direct knowledge search endpoint: {str(e)}")
        return jsonify({"error": "Knowledge search API error", "details": str(e)}), 500

@app.route('/api/knowledge/categories', methods=['GET'])
def knowledge_categories_api():
    # Direct endpoint for knowledge categories API
    try:
        # Import function from knowledge blueprint
        from routes.knowledge import get_knowledge_categories
        return get_knowledge_categories()
    except Exception as e:
        logger.error(f"Error in direct knowledge categories endpoint: {str(e)}")
        return jsonify({"error": "Knowledge categories API error", "details": str(e)}), 500

"""
        
        # Insert the direct endpoints
        updated_content = content.replace(insert_point, direct_endpoints + "\n" + insert_point)
        
        # Write the updated content back to main.py
        with open('main.py', 'w') as f:
            f.write(updated_content)
            
        logger.info("Successfully added direct knowledge endpoints to main.py")
        return True
    except Exception as e:
        logger.error(f"Error adding direct knowledge endpoints: {str(e)}")
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    logger.info("Adding direct knowledge endpoints...")
    success = add_knowledge_endpoints()
    if success:
        logger.info("Direct knowledge endpoints added successfully")
    else:
        logger.error("Failed to add direct knowledge endpoints")
        sys.exit(1)