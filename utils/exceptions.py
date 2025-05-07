"""
Dana AI Platform - Standard Exceptions

This module defines standard exceptions for the Dana AI platform.
All custom exceptions should inherit from DanaBaseError.
"""

class DanaBaseError(Exception):
    """Base exception for Dana AI platform"""
    def __init__(self, message, status_code=500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class AuthenticationError(DanaBaseError):
    """Authentication error"""
    def __init__(self, message="Authentication failed"):
        super().__init__(message, status_code=401)

class AuthorizationError(DanaBaseError):
    """Authorization error (authenticated but not authorized)"""
    def __init__(self, message="Not authorized to perform this action"):
        super().__init__(message, status_code=403)

class ValidationError(DanaBaseError):
    """Data validation error"""
    def __init__(self, message="Invalid data provided"):
        super().__init__(message, status_code=400)

class ResourceNotFoundError(DanaBaseError):
    """Resource not found error"""
    def __init__(self, message="Resource not found"):
        super().__init__(message, status_code=404)

class DatabaseAccessError(DanaBaseError):
    """Database access error"""
    def __init__(self, message="Database error"):
        super().__init__(message, status_code=500)

class ConfigurationError(DanaBaseError):
    """Configuration error"""
    def __init__(self, message="System configuration error"):
        super().__init__(message, status_code=500)

class IntegrationError(DanaBaseError):
    """Integration error (issues with external services)"""
    def __init__(self, message="Integration error", status_code=500):
        super().__init__(message, status_code=status_code)

class CSRFError(DanaBaseError):
    """CSRF validation error"""
    def __init__(self, message="CSRF token validation failed"):
        super().__init__(message, status_code=400)