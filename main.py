"""
Dana AI Platform - Proxy Main

This file imports the app from the backend package.
This allows existing code to continue working without changes.
"""

from backend.main import app

# This will be used if running directly with Python
if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
