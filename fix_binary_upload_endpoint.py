"""
Fix Binary Upload Endpoint

This script creates a direct endpoint to test and fix the binary file upload functionality.
"""
from flask import Flask, request, jsonify
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route('/test')
def test():
    """
    Simple test endpoint
    """
    return "Test endpoint is working!"

@app.route('/api/binary-upload', methods=['POST'])
def binary_upload():
    """
    Test binary upload endpoint
    """
    try:
        data = request.json
        if not data:
            logger.warning("No data provided")
            return jsonify({"error": "No data provided"}), 400
            
        logger.info(f"Received data: {data}")
        
        # Validate required fields
        required_fields = ['filename', 'file_type', 'content']
        for field in required_fields:
            if field not in data:
                logger.warning(f"Missing required field: {field}")
                return jsonify({"error": f"Missing required field: {field}"}), 400
                
        # Return success response
        return jsonify({
            "message": "File received successfully",
            "file_info": {
                "filename": data['filename'],
                "file_type": data['file_type'],
                "content_length": len(data['content']),
                "file_size": data.get('file_size', len(data['content']))
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}", exc_info=True)
        return jsonify({"error": f"Server error: {str(e)}"}), 500

if __name__ == '__main__':
    print("Starting test server for binary upload endpoint")
    print("Test the endpoint with:")
    print('curl -v -X POST -H "Content-Type: application/json" http://localhost:8080/api/binary-upload -d \'{"filename":"test.txt", "file_type":"text/plain", "content":"Test content"}\'')
    
    app.run(host='0.0.0.0', port=8080, debug=True)