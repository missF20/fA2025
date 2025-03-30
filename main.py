"""
Dana AI Platform - Main Entry Point

This is the main entry point for running the Dana AI Platform.
"""

from app import app
import threading
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import knowledge base demo app 
try:
    from knowledge_base_demo import app as kb_app
    
    def run_knowledge_demo():
        """Run the knowledge base demo on port 5173"""
        logger.info("Starting Knowledge Base Demo on port 5173...")
        kb_app.run(host="0.0.0.0", port=5173, debug=False, use_reloader=False)
        
    # Start knowledge base demo in a thread
    kb_thread = threading.Thread(target=run_knowledge_demo)
    kb_thread.daemon = True
    kb_thread.start()
    logger.info("Knowledge Base Demo thread started")
except Exception as e:
    logger.error(f"Failed to start Knowledge Base Demo: {str(e)}")

if __name__ == "__main__":
    # Start the main application
    logger.info("Starting main Dana AI Platform on port 5000...")
    app.run(host="0.0.0.0", port=5000, debug=True)