"""
New File Upload Server

A standalone server dedicated to handling file uploads for the Dana AI Platform.
This server focuses on binary file handling with a clean, simple implementation.
"""

import os
import json
import base64
import logging
import uuid
import tempfile
from datetime import datetime
from flask import Flask, jsonify, request, send_file

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure upload folder
UPLOAD_FOLDER = os.path.join(tempfile.gettempdir(), "dana_uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Create Flask app
app = Flask(__name__)

# Set JSON response to not sort keys
app.json.sort_keys = False

@app.route('/status', methods=['GET'])
def status():
    """Application status endpoint"""
    return jsonify({
        "status": "ok",
        "server": "Dana AI File Upload Server",
        "version": "1.0.0",
        "upload_folder": UPLOAD_FOLDER,
        "uploads": len([f for f in os.listdir(UPLOAD_FOLDER) if f.endswith('.json')])
    })

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload"""
    try:
        # Get request data
        data = request.json or {}
        
        # Extract data
        user_id = data.get('user_id', 'anonymous')
        file_name = data.get('file_name', f'upload_{datetime.now().strftime("%Y%m%d%H%M%S")}')
        file_content = data.get('content')
        file_type = data.get('file_type', 'application/octet-stream')
        
        if not file_content:
            return jsonify({"error": "No file content provided"}), 400
        
        # Generate file ID
        file_id = str(uuid.uuid4())
        
        # Save file to disk
        try:
            file_content_bytes = base64.b64decode(file_content)
            file_path = os.path.join(UPLOAD_FOLDER, file_id)
            with open(file_path, 'wb') as f:
                f.write(file_content_bytes)
            
            # Save metadata
            metadata = {
                'file_id': file_id,
                'user_id': user_id,
                'file_name': file_name,
                'file_type': file_type,
                'upload_time': datetime.now().isoformat(),
                'file_size': len(file_content_bytes)
            }
            
            metadata_path = os.path.join(UPLOAD_FOLDER, f"{file_id}.json")
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f)
            
            return jsonify({
                "status": "success",
                "file_id": file_id,
                "message": "File uploaded successfully"
            }), 201
            
        except Exception as e:
            logger.error(f"Error saving file: {str(e)}")
            return jsonify({"error": f"Error saving file: {str(e)}"}), 500
    
    except Exception as e:
        logger.error(f"Error processing upload: {str(e)}")
        return jsonify({"error": f"Error processing upload: {str(e)}"}), 500

@app.route('/files', methods=['GET'])
def list_files():
    """List all uploaded files"""
    try:
        files = []
        for filename in os.listdir(UPLOAD_FOLDER):
            if filename.endswith('.json'):
                with open(os.path.join(UPLOAD_FOLDER, filename), 'r') as f:
                    metadata = json.load(f)
                    files.append(metadata)
        
        return jsonify({
            "status": "success",
            "files": files
        })
    
    except Exception as e:
        logger.error(f"Error listing files: {str(e)}")
        return jsonify({"error": f"Error listing files: {str(e)}"}), 500

@app.route('/files/<file_id>', methods=['GET'])
def get_file(file_id):
    """Retrieve a file by ID"""
    try:
        # Check if metadata exists
        metadata_path = os.path.join(UPLOAD_FOLDER, f"{file_id}.json")
        if not os.path.exists(metadata_path):
            return jsonify({"error": "File not found"}), 404
        
        # Get metadata
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        # Check if file exists
        file_path = os.path.join(UPLOAD_FOLDER, file_id)
        if not os.path.exists(file_path):
            return jsonify({"error": "File content not found"}), 404
        
        # Return file
        return send_file(
            file_path,
            mimetype=metadata.get('file_type', 'application/octet-stream'),
            as_attachment=True,
            download_name=metadata.get('file_name', 'download')
        )
    
    except Exception as e:
        logger.error(f"Error retrieving file: {str(e)}")
        return jsonify({"error": f"Error retrieving file: {str(e)}"}), 500

@app.route('/files/<file_id>', methods=['DELETE'])
def delete_file(file_id):
    """Delete a file by ID"""
    try:
        # Check if metadata exists
        metadata_path = os.path.join(UPLOAD_FOLDER, f"{file_id}.json")
        if not os.path.exists(metadata_path):
            return jsonify({"error": "File not found"}), 404
        
        # Check if file exists
        file_path = os.path.join(UPLOAD_FOLDER, file_id)
        
        # Delete file if it exists
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # Delete metadata
        os.remove(metadata_path)
        
        return jsonify({
            "status": "success",
            "message": "File deleted successfully"
        })
    
    except Exception as e:
        logger.error(f"Error deleting file: {str(e)}")
        return jsonify({"error": f"Error deleting file: {str(e)}"}), 500

@app.route('/routes', methods=['GET'])
def list_routes():
    """List all routes"""
    routes = []
    for rule in app.url_map.iter_rules():
        routes.append({
            "endpoint": rule.endpoint,
            "methods": [method for method in rule.methods if method not in ["OPTIONS", "HEAD"]],
            "path": str(rule)
        })
    
    return jsonify(routes)

@app.route('/test-upload', methods=['GET'])
def test_upload_form():
    """Display a simple HTML form for testing uploads"""
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test File Upload</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
            h1 { color: #333; }
            .form-group { margin-bottom: 15px; }
            label { display: block; margin-bottom: 5px; }
            input, textarea { width: 100%; padding: 8px; box-sizing: border-box; }
            button { background: #4CAF50; color: white; padding: 10px 15px; border: none; cursor: pointer; }
            pre { background: #f4f4f4; padding: 10px; border-radius: 4px; overflow: auto; }
        </style>
    </head>
    <body>
        <h1>Dana AI File Upload Test</h1>
        <div class="form-group">
            <label for="file">Select File:</label>
            <input type="file" id="file" name="file">
        </div>
        <div class="form-group">
            <label for="userId">User ID:</label>
            <input type="text" id="userId" name="userId" value="test-user">
        </div>
        <button onclick="uploadFile()">Upload File</button>
        <hr>
        <h3>Response:</h3>
        <pre id="response">Select a file and click upload...</pre>
        
        <script>
            async function uploadFile() {
                const fileInput = document.getElementById('file');
                const userId = document.getElementById('userId').value;
                const responseElem = document.getElementById('response');
                
                if (!fileInput.files.length) {
                    responseElem.textContent = 'Please select a file';
                    return;
                }
                
                const file = fileInput.files[0];
                
                try {
                    // Read file as base64
                    const base64Content = await readFileAsBase64(file);
                    
                    // Prepare request payload
                    const payload = {
                        user_id: userId,
                        file_name: file.name,
                        file_type: file.type,
                        content: base64Content
                    };
                    
                    // Send request
                    responseElem.textContent = 'Uploading...';
                    
                    const response = await fetch('/upload', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify(payload)
                    });
                    
                    const result = await response.json();
                    responseElem.textContent = JSON.stringify(result, null, 2);
                    
                } catch (error) {
                    responseElem.textContent = `Error: ${error.message}`;
                    console.error(error);
                }
            }
            
            function readFileAsBase64(file) {
                return new Promise((resolve, reject) => {
                    const reader = new FileReader();
                    reader.readAsDataURL(file);
                    reader.onload = () => {
                        // Extract base64 part without mime type prefix
                        const base64Content = reader.result.split(',')[1];
                        resolve(base64Content);
                    };
                    reader.onerror = error => reject(error);
                });
            }
        </script>
    </body>
    </html>
    '''

if __name__ == '__main__':
    port = int(os.environ.get('UPLOAD_SERVER_PORT', 5005))
    logger.info(f"Starting Dana AI File Upload Server on port {port}...")
    app.run(host="0.0.0.0", port=port, debug=True)