"""
Dana AI Platform - Knowledge Base Demo Entry Point

This is an entry point for running the Knowledge Base Demo application.
"""

import sys
import threading
import time
from app import app
from knowledge_base_demo import app as knowledge_demo_app

def run_knowledge_demo():
    """Run the knowledge base demo app"""
    knowledge_demo_app.run(host="0.0.0.0", port=5001, debug=False)

if __name__ == "__main__":
    # Start the knowledge base demo in a separate thread
    print("Starting Knowledge Base Demo on port 5001...")
    knowledge_thread = threading.Thread(target=run_knowledge_demo)
    knowledge_thread.daemon = True
    knowledge_thread.start()
    
    # Start the main application
    print("Starting main application on port 5000...")
    app.run(host="0.0.0.0", port=5000, debug=True)