"""
A simple Flask server to test knowledge file uploading
"""
from flask import Flask, request, jsonify
from datetime import datetime
import json
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route('/')
def home():
    """Home page with test form"""
    return """
    <html>
        <head>
            <title>Knowledge File Test</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .container { max-width: 800px; margin: 0 auto; }
                .form-group { margin-bottom: 15px; }
                label { display: block; margin-bottom: 5px; }
                button { padding: 8px 15px; background: #4CAF50; color: white; border: none; cursor: pointer; }
                pre { background: #f4f4f4; padding: 15px; border-radius: 5px; }
                #result { margin-top: 20px; padding: 10px; border: 1px solid #ddd; min-height: 100px; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Knowledge File Test</h1>
                <form id="uploadForm">
                    <div class="form-group">
                        <label for="filename">Filename:</label>
                        <input type="text" id="filename" value="test.txt" />
                    </div>
                    <div class="form-group">
                        <label for="fileSize">File Size:</label>
                        <input type="number" id="fileSize" value="12" />
                    </div>
                    <div class="form-group">
                        <label for="fileType">File Type:</label>
                        <input type="text" id="fileType" value="text" />
                    </div>
                    <div class="form-group">
                        <label for="content">Content:</label>
                        <textarea id="content" rows="4" cols="50">Test content</textarea>
                    </div>
                    <div class="form-group">
                        <label for="category">Category (optional):</label>
                        <input type="text" id="category" value="" />
                    </div>
                    <div class="form-group">
                        <label for="tags">Tags (optional, comma-separated):</label>
                        <input type="text" id="tags" value="" />
                    </div>
                    <button type="button" onclick="uploadFile()">Upload File</button>
                </form>
                <div id="result"></div>
            </div>
            
            <script>
                function uploadFile() {
                    const data = {
                        filename: document.getElementById('filename').value,
                        file_size: parseInt(document.getElementById('fileSize').value),
                        file_type: document.getElementById('fileType').value,
                        content: document.getElementById('content').value,
                    };
                    
                    const category = document.getElementById('category').value;
                    if (category) {
                        data.category = category;
                    }
                    
                    const tags = document.getElementById('tags').value;
                    if (tags) {
                        data.tags = tags.split(',').map(tag => tag.trim());
                    }
                    
                    document.getElementById('result').innerHTML = 'Uploading...';
                    
                    fetch('/api/upload', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify(data)
                    })
                    .then(response => response.json())
                    .then(data => {
                        document.getElementById('result').innerHTML = '<pre>' + JSON.stringify(data, null, 2) + '</pre>';
                    })
                    .catch(error => {
                        document.getElementById('result').innerHTML = 'Error: ' + error.message;
                    });
                }
            </script>
        </body>
    </html>
    """

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Handle file upload"""
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        # Basic validation
        required_fields = ['filename', 'file_size', 'file_type', 'content']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
                
        # Add test user ID
        data['user_id'] = '1'
        
        # Add timestamps
        now = datetime.now().isoformat()
        data['created_at'] = now
        data['updated_at'] = now
        
        # Simulate database insert
        # In a real application, this would connect to the database
        file_id = 12345
        
        # Create a mock response
        return jsonify({
            'message': 'File uploaded successfully (simulated)',
            'file': {
                'id': file_id,
                'user_id': data['user_id'],
                'filename': data['filename'],
                'file_type': data['file_type'],
                'file_size': data['file_size'],
                'created_at': data['created_at'],
                'updated_at': data['updated_at'],
                'category': data.get('category', ''),
                'tags': data.get('tags', []),
            }
        }), 201
    except Exception as e:
        logger.error(f"Error processing upload: {str(e)}", exc_info=True)
        return jsonify({'error': f'Server error: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)