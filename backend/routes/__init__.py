"""
Dana AI Platform - Routes Package

This module initializes and registers all route blueprints.
"""

import logging
from flask import Blueprint

# Import all route modules
from backend.routes.integrations import integration_bp, register_integration_routes

logger = logging.getLogger(__name__)

def register_all_routes(app):
    """Register all route blueprints with the application"""
    logger.info("Registering all route blueprints")
    
    # Register individual route sets
    register_integration_routes(app)
    
    logger.info("All routes registered successfully")