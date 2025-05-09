"""
Dana AI Platform Main Module

This is the entry point for the Dana AI Platform application.
The actual app is initialized in app.py.
"""
from app import app
from direct_email_endpoints import add_direct_email_endpoints

# Add direct email endpoints to the app
add_direct_email_endpoints(app)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)