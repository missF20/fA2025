"""
Verify CSRF Protection in App Configuration

This script inspects the app configuration to verify that CSRF protection is enabled.
"""

import os
import logging
from app import app, csrf

def verify_csrf_protection():
    """
    Verify that CSRF protection is properly configured in the application
    """
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # Check if csrf extension is initialized
    logger.info("Checking CSRF protection configuration...")
    
    # Check if CSRF is enabled
    csrf_enabled = app.config.get('WTF_CSRF_ENABLED', False)
    logger.info(f"CSRF Protection Enabled: {csrf_enabled}")
    
    # Check CSRF methods
    csrf_methods = app.config.get('WTF_CSRF_METHODS', [])
    logger.info(f"CSRF Protected Methods: {csrf_methods}")
    
    # Check CSRF time limit
    csrf_time_limit = app.config.get('WTF_CSRF_TIME_LIMIT', None)
    logger.info(f"CSRF Time Limit: {csrf_time_limit} seconds")
    
    # Check if csrf object is initialized
    if csrf:
        logger.info("CSRF object is properly initialized.")
    else:
        logger.warning("CSRF object is not properly initialized!")
    
    # Check for secret key, which is required for CSRF
    has_secret_key = bool(app.secret_key)
    logger.info(f"Application has secret key: {has_secret_key}")
    
    # Check endpoints with CSRF protection
    protected_endpoints = []
    for rule in app.url_map.iter_rules():
        if 'POST' in rule.methods and not rule.endpoint.startswith('static'):
            if any(part in rule.endpoint for part in ['payment', 'config', 'save']):
                protected_endpoints.append(f"{rule.endpoint} - {rule.rule}")
    
    logger.info(f"Potentially protected endpoints:")
    for endpoint in protected_endpoints:
        logger.info(f"  {endpoint}")
    
    # Check for HTTPS/SSL Configuration
    ssl_context = app.config.get('SSL_CONTEXT')
    if ssl_context:
        logger.info(f"SSL Context configured: {ssl_context}")
    else:
        logger.warning("No SSL context found in app config")
    
    # Overall assessment
    if csrf_enabled and has_secret_key:
        logger.info("✅ CSRF protection appears to be properly configured.")
    else:
        logger.warning("❌ CSRF protection may not be properly configured!")
        
    # Return results for programmatic use
    return {
        "csrf_enabled": csrf_enabled,
        "csrf_methods": csrf_methods,
        "has_secret_key": has_secret_key,
        "csrf_object_initialized": bool(csrf),
        "protected_endpoints": protected_endpoints
    }

if __name__ == "__main__":
    verify_csrf_protection()