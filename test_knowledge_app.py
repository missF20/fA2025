"""
Simple Flask app to test knowledge file uploads
"""
from flask import Flask, request, jsonify
import os
# No external dependencies needed

app = Flask(__name__)

@app.route('/')
def home():
    return """
    <html>
        <head>
            <title>Knowledge Test</title>
        </head>
        <body>
            <h1>Knowledge API Test</h1>
            <form id="testForm">
                <button type="button" onclick="testGetFiles()">Test Get Files</button>
                <button type="button" onclick="testCreateFile()">Test Create File</button>
                <button type="button" onclick="testBinaryUpload()">Test Binary Upload</button>
            </form>
            <div id="result" style="margin-top: 20px; padding: 10px; border: 1px solid #ccc;"></div>
            
            <script>
                async function testGetFiles() {
                    try {
                        const response = await fetch('http://localhost:5000/api/knowledge/files', {
                            method: 'GET',
                            headers: {
                                'Authorization': 'dev-token'
                            }
                        });
                        const data = await response.json();
                        document.getElementById('result').innerText = JSON.stringify(data, null, 2);
                    } catch (error) {
                        document.getElementById('result').innerText = 'Error: ' + error.message;
                    }
                }
                
                async function testCreateFile() {
                    try {
                        const response = await fetch('http://localhost:5000/api/knowledge/files', {
                            method: 'POST',
                            headers: {
                                'Authorization': 'dev-token',
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify({
                                filename: 'test.txt',
                                file_size: 12,
                                file_type: 'text',
                                content: 'Test content'
                            })
                        });
                        const data = await response.json();
                        document.getElementById('result').innerText = JSON.stringify(data, null, 2);
                    } catch (error) {
                        document.getElementById('result').innerText = 'Error: ' + error.message;
                    }
                }
                
                async function testBinaryUpload() {
                    try {
                        const response = await fetch('http://localhost:5000/api/knowledge/files/binary', {
                            method: 'POST',
                            headers: {
                                'Authorization': 'dev-token',
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify({
                                filename: 'test.txt',
                                file_size: 12,
                                file_type: 'text',
                                content: 'Test content'
                            })
                        });
                        const data = await response.json();
                        document.getElementById('result').innerText = JSON.stringify(data, null, 2);
                    } catch (error) {
                        document.getElementById('result').innerText = 'Error: ' + error.message;
                    }
                }
            </script>
        </body>
    </html>
    """

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)