"""
Debug Endpoint for Authentication

This script adds a direct debug endpoint to test authentication.
"""

from app import app
from flask import jsonify, request
import base64
import json
import os
import time
from datetime import datetime

@app.route('/api/auth/debug')
def debug_auth():
    """Debug endpoint for authentication issues"""
    # Get token from request
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        token = auth_header[7:]  # Remove 'Bearer ' prefix
    else:
        token = request.cookies.get('token')
        
    if not token:
        # Also check for JWT token in query string
        token = request.args.get('token')
    
    # Debug info to return
    debug_info = {
        'has_token': bool(token),
        'token_length': len(token) if token else 0,
        'endpoint_timestamp': datetime.now().isoformat()
    }
    
    # If we have a token, try to decode it
    if token:
        try:
            # Decode token parts
            token_parts = token.split('.')
            debug_info['token_parts'] = len(token_parts)
            
            if len(token_parts) >= 2:
                # Decode header
                try:
                    header_padding = token_parts[0] + '=' * (4 - len(token_parts[0]) % 4)
                    header_json = base64.b64decode(header_padding)
                    header = json.loads(header_json)
                    debug_info['header'] = header
                except Exception as e:
                    debug_info['header_error'] = str(e)
                
                # Decode payload
                try:
                    payload_padding = token_parts[1] + '=' * (4 - len(token_parts[1]) % 4)
                    payload_json = base64.b64decode(payload_padding)
                    payload = json.loads(payload_json)
                    
                    # Only include safe fields
                    safe_payload = {
                        'exp': payload.get('exp'),
                        'iat': payload.get('iat'),
                        'aud': payload.get('aud'),
                        'role': payload.get('role'),
                        'iss': payload.get('iss'),
                        'email_exists': 'email' in payload,
                        'sub_exists': 'sub' in payload,
                    }
                    
                    # Check token expiration
                    if 'exp' in payload:
                        now = time.time()
                        exp = payload['exp']
                        safe_payload['expires_in_seconds'] = exp - now
                        safe_payload['is_expired'] = now > exp
                    
                    debug_info['payload'] = safe_payload
                except Exception as e:
                    debug_info['payload_error'] = str(e)
        except Exception as e:
            debug_info['token_error'] = str(e)
    
    return jsonify(debug_info)

# Load this endpoint by importing this file in main.py
if __name__ == "__main__":
    print("This file should be imported, not run directly.")