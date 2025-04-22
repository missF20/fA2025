"""
Dana AI Platform - Application Runner

This script launches both the backend Flask API and frontend services.
It handles port management to ensure there are no conflicts.
"""

import os
import sys
import subprocess
import threading
import time
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_backend():
    """
    Run the Flask backend API on port 5000
    """
    logger.info("Starting Flask backend on port 5000...")
    backend_cmd = "cd backend && gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app"
    subprocess.run(backend_cmd, shell=True)

def run_frontend():
    """
    Run the React frontend on port 5173
    """
    logger.info("Starting React frontend on port 5173...")
    frontend_cmd = "cd frontend && npm run dev"
    subprocess.run(frontend_cmd, shell=True)

def main():
    """
    Main function to start both servers
    """
    try:
        # Start backend in a thread
        backend_thread = threading.Thread(target=run_backend, daemon=True)
        backend_thread.start()
        logger.info("Backend thread started")
        
        # Wait a moment to ensure backend is starting
        time.sleep(1)
        
        # Start frontend in the main thread
        run_frontend()
    except KeyboardInterrupt:
        logger.info("Shutting down servers...")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error running servers: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()