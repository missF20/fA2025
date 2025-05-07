"""
Dana AI Platform - Route Registration Utilities

This module provides standardized route registration for the Dana AI platform.
It includes utilities for blueprint registration with consistent error handling.
"""

import logging
import importlib
from typing import Dict, List, Optional, Callable

# Configure logger
logger = logging.getLogger(__name__)

def register_blueprint(app, blueprint_path: str, blueprint_name: Optional[str] = None, 
                       on_success: Optional[Callable] = None, on_failure: Optional[Callable] = None) -> bool:
    """
    Register a Flask blueprint with standardized error handling.
    
    Args:
        app: Flask application instance
        blueprint_path: Import path of the blueprint (e.g., 'routes.integrations.standard_email')
        blueprint_name: Name of the blueprint object (if different from the module name)
        on_success: Optional callback to execute on successful registration
        on_failure: Optional callback to execute on failed registration
        
    Returns:
        bool: True if registration succeeded, False otherwise
    """
    try:
        # Import the blueprint
        module = importlib.import_module(blueprint_path)
        
        # Get the blueprint object
        if blueprint_name:
            blueprint = getattr(module, blueprint_name)
        else:
            # Extract name from path
            name_parts = blueprint_path.split('.')
            prefix = name_parts[-1]
            # Try standard naming conventions
            for suffix in ['_bp', '_blueprint']:
                bp_name = f"{prefix}{suffix}" 
                if hasattr(module, bp_name):
                    blueprint = getattr(module, bp_name)
                    break
            else:
                # If no standard name found, look for any Blueprint instance
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if attr_name.endswith('_bp') or attr_name.endswith('_blueprint'):
                        blueprint = attr
                        break
                else:
                    raise AttributeError(f"Could not find blueprint in module {blueprint_path}")
        
        # Register the blueprint
        app.register_blueprint(blueprint)
        logger.info(f"Blueprint {blueprint_path} registered successfully")
        
        # Execute success callback if provided
        if on_success:
            on_success(blueprint)
            
        return True
        
    except ImportError as e:
        logger.warning(f"Could not import blueprint {blueprint_path}: {e}")
        if on_failure:
            on_failure(e)
        return False
    except AttributeError as e:
        logger.warning(f"Could not find blueprint in {blueprint_path}: {e}")
        if on_failure:
            on_failure(e)
        return False
    except Exception as e:
        logger.error(f"Error registering blueprint {blueprint_path}: {e}")
        if on_failure:
            on_failure(e)
        return False

def register_blueprints(app, blueprint_configs: List[Dict]) -> Dict:
    """
    Register multiple blueprints from configuration.
    
    Args:
        app: Flask application instance
        blueprint_configs: List of blueprint configurations, each containing:
            - path: Import path
            - name: (Optional) Blueprint object name
            - fallback: (Optional) Fallback function to call if registration fails
            
    Returns:
        Dict: Report of registration results with counts
    """
    results = {
        'total': len(blueprint_configs),
        'success': 0,
        'failed': 0,
        'names': {
            'success': [],
            'failed': []
        }
    }
    
    for config in blueprint_configs:
        path = config.get('path')
        name = config.get('name')
        fallback = config.get('fallback')
        
        if register_blueprint(app, path, name):
            results['success'] += 1
            results['names']['success'].append(path)
        else:
            results['failed'] += 1
            results['names']['failed'].append(path)
            
            # Execute fallback if provided
            if fallback and callable(fallback):
                try:
                    fallback(app)
                    logger.info(f"Executed fallback for {path}")
                except Exception as e:
                    logger.error(f"Error executing fallback for {path}: {e}")
    
    # Log summary
    logger.info(f"Blueprint registration summary: {results['success']} succeeded, "
                f"{results['failed']} failed out of {results['total']}")
                
    return results

def direct_register_route(app, route_path: str, endpoint: Callable, methods: List[str], 
                          csrf_exempt: bool = False) -> bool:
    """
    Register a route directly to the Flask app.
    This is a fallback mechanism when blueprint registration fails.
    
    Args:
        app: Flask application instance
        route_path: URL path for the route
        endpoint: View function to register
        methods: HTTP methods for the route
        csrf_exempt: Whether to exempt this route from CSRF protection
        
    Returns:
        bool: True if registration succeeded, False otherwise
    """
    try:
        # Register the route
        app.route(route_path, methods=methods)(endpoint)
        
        # Apply CSRF exemption if requested
        if csrf_exempt and hasattr(app, 'csrf'):
            app.csrf.exempt(endpoint)
            
        logger.info(f"Direct route registered successfully: {route_path}")
        return True
    except Exception as e:
        logger.error(f"Error registering direct route {route_path}: {e}")
        return False