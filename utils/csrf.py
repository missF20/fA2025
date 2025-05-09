"""
CSRF protection utilities
"""
from functools import wraps
from flask import current_app
from flask_wtf.csrf import CSRFProtect

csrf = CSRFProtect()

def csrf_exempt(view):
    """Mark a view as exempt from CSRF protection"""
    if isinstance(view, str):
        return csrf.exempt(view)

    view.csrf_exempt = True
    return view

def init_csrf(app):
    """Initialize CSRF protection"""
    csrf.init_app(app)