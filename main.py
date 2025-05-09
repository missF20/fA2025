"""
Dana AI Platform Main Module

This is the entry point for the Dana AI Platform application.
The actual app is initialized in app.py.
"""
from app import app

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)