"""
Exception Definitions

This module defines custom exceptions used throughout the application.
"""


class BaseError(Exception):
    """Base class for all custom exceptions"""
    pass


class ValidationError(BaseError):
    """Exception raised for validation errors"""
    pass


class DatabaseAccessError(BaseError):
    """Exception raised for database access errors"""
    pass


class AuthenticationError(BaseError):
    """Exception raised for authentication errors"""
    pass


class IntegrationError(BaseError):
    """Exception raised for integration errors"""
    pass


class RateLimitError(BaseError):
    """Exception raised for rate limit errors"""
    pass


class ConfigurationError(BaseError):
    """Exception raised for configuration errors"""
    pass


class FileProcessingError(BaseError):
    """Exception raised for file processing errors"""
    pass


class APIError(BaseError):
    """Exception raised for API errors"""
    pass


class ResourceNotFoundError(BaseError):
    """Exception raised when a requested resource is not found"""
    pass