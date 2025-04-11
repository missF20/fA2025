"""
Simple Routes Lister

This script directly lists all routes in the main application.
"""
import sys
import logging
from urllib.parse import urlparse

# Suppress all logging
logging.getLogger().setLevel(logging.CRITICAL)

try:
    # Import app and blueprints
    from main import app
    
    # List all routes
    print("\nRegistered routes:")
    routes = []
    for rule in app.url_map.iter_rules():
        routes.append((str(rule), rule.endpoint, ", ".join(sorted(rule.methods))))
    
    # Sort routes by path
    routes.sort(key=lambda x: x[0])
    
    for route, endpoint, methods in routes:
        print(f"Route: {route:50} Endpoint: {endpoint:40} Methods: {methods}")
    
    # Count the routes
    route_count = len(routes)
    print(f"\nTotal registered routes: {route_count}")
    
    # Special check for knowledge file deletion
    print("\nSearching for knowledge file delete endpoints...")
    for route, endpoint, methods in routes:
        if ("knowledge" in route and "delete" in endpoint.lower()) or \
           ("file" in route and "delete" in endpoint.lower()):
            print(f"Found delete endpoint: {route}, Endpoint: {endpoint}, Methods: {methods}")
    
except Exception as e:
    import traceback
    print(f"Error listing routes: {str(e)}")
    print(traceback.format_exc())
    sys.exit(1)