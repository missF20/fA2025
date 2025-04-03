"""
Fix Binary Upload Endpoint

This script creates a direct endpoint to test and fix the binary file upload functionality.
"""

import os
import base64
import logging
import datetime
from flask import Flask, request, jsonify

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route('/test', methods=['GET'])
def test():
    """
    Simple test endpoint
    """
    return jsonify({
        'success': True,
        'message': 'Test endpoint is operational'
    })

@app.route('/binary-upload', methods=['POST'])
def binary_upload():
    """
    Test binary upload endpoint
    """
    try:
        # Check if this is a test request
        if request.args.get('test') == 'true':
            return jsonify({
                'success': True,
                'message': 'Binary upload endpoint is accessible'
            })
        
        # For testing purposes, we'll use a hardcoded user_id
        user_id = "test-user-id"
        
        # Check if a file was provided
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file provided',
                'message': 'Please provide a file in the multipart/form-data'
            }), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'Empty filename',
                'message': 'The provided file has no filename'
            }), 400
        
        # Get file metadata
        filename = file.filename
        file_type = file.content_type or 'application/octet-stream'
        
        # Read the file data
        file_data = file.read()
        file_size = len(file_data)
        
        # Base64 encode the file data for storage
        encoded_data = base64.b64encode(file_data).decode('utf-8')
        
        # For testing purposes, just log the upload information
        logger.info(f"File uploaded: {filename}, type: {file_type}, size: {file_size} bytes")
        
        # Return success message with basic file info
        return jsonify({
            'success': True, 
            'message': 'File uploaded successfully',
            'file_info': {
                'filename': filename,
                'file_type': file_type,
                'file_size': file_size,
                'upload_time': datetime.datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Error uploading binary file: {str(e)}")
        return jsonify({'error': f'Failed to upload file: {str(e)}'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5002))
    app.run(host='0.0.0.0', port=port, debug=True)