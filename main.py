"""
Dana AI Platform - Main Entry Point

This is the main entry point for running the Dana AI Platform.
"""

from app import app, socketio
import threading
import logging
import subprocess
import os
from flask import jsonify, request

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import knowledge base demo app - DISABLED to free up port 5173 for React frontend
"""
try:
    from knowledge_base_demo import app as kb_app
    
    def run_knowledge_demo():
        Run the knowledge base demo on port 5173
        logger.info("Starting Knowledge Base Demo on port 5173...")
        kb_app.run(host="0.0.0.0", port=5173, debug=False, use_reloader=False)
        
    # Start knowledge base demo in a thread
    kb_thread = threading.Thread(target=run_knowledge_demo)
    kb_thread.daemon = True
    kb_thread.start()
    logger.info("Knowledge Base Demo thread started")
except Exception as e:
    logger.error(f"Failed to start Knowledge Base Demo: {str(e)}")
"""
logger.info("Knowledge Base Demo disabled to free up port 5173 for React frontend")

# Start React frontend
try:
    def run_react_frontend():
        """Run the React frontend on port 5173"""
        logger.info("Starting React Frontend on port 5173...")
        # Use subprocess to run npm in the frontend directory
        frontend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'frontend')
        process = subprocess.Popen(
            "cd {} && npm run dev -- --host 0.0.0.0 --port 5173".format(frontend_dir),
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        # Log any stdout/stderr in a non-blocking way
        def log_output():
            for line in iter(process.stdout.readline, ''):
                if line:
                    logger.info(f"React Frontend: {line.strip()}")
            for line in iter(process.stderr.readline, ''):
                if line:
                    logger.error(f"React Frontend Error: {line.strip()}")
        
        threading.Thread(target=log_output, daemon=True).start()
        logger.info("React Frontend process started")
        
    # Start React frontend in a thread
    react_thread = threading.Thread(target=run_react_frontend)
    react_thread.daemon = True
    react_thread.start()
    logger.info("React Frontend thread started")
except Exception as e:
    logger.error(f"Failed to start React Frontend: {str(e)}")

# Import simple API app
try:
    from simple_app import app as simple_app
    
    def run_simple_app():
        """Run the simple API on port 5001"""
        logger.info("Starting Simple API on port 5001...")
        simple_app.run(host="0.0.0.0", port=5001, debug=False, use_reloader=False)
        
    # Start simple app in a thread
    simple_thread = threading.Thread(target=run_simple_app)
    simple_thread.daemon = True
    simple_thread.start()
    logger.info("Simple API thread started")
except Exception as e:
    logger.error(f"Failed to start Simple API: {str(e)}")


# Direct knowledge API endpoints
@app.route('/api/knowledge/files', methods=['GET'])
def knowledge_files_api():
    # Direct endpoint for knowledge files API
    try:
        # Import only when needed to avoid circular imports
        from routes.knowledge import get_knowledge_files
        return get_knowledge_files()
    except Exception as e:
        logger.error(f"Error in direct knowledge files endpoint: {str(e)}")
        return jsonify({"error": "Knowledge files API error", "details": str(e)}), 500

@app.route('/api/knowledge/binary/upload', methods=['POST'])
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

@app.route('/api/knowledge/stats', methods=['GET'])
def knowledge_stats_api():
    # Direct endpoint for knowledge stats API
    try:
        # Import function from knowledge blueprint
        from routes.knowledge import get_knowledge_stats
        return get_knowledge_stats()
    except Exception as e:
        logger.error(f"Error in direct knowledge stats endpoint: {str(e)}")
        return jsonify({"error": "Knowledge stats API error", "details": str(e)}), 500


if __name__ == "__main__":
    # Start the main application using SocketIO
    logger.info("Starting main Dana AI Platform on port 5000 with SocketIO support...")
    try:
        socketio.run(
            app, 
            host="0.0.0.0", 
            port=5000, 
            debug=True,
            allow_unsafe_werkzeug=True  # Required for newer versions of Flask-SocketIO
        )
    except TypeError as e:
        # Fallback for older Flask-SocketIO versions
        logger.warning(f"SocketIO error with allow_unsafe_werkzeug, trying without: {e}")
        socketio.run(app, host="0.0.0.0", port=5000, debug=True)