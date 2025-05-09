"""
Slack integration blueprint module

This module provides routes for Slack integration functionality.
"""

from routes.slack.routes import slack_bp

# Export the blueprint for direct import
__all__ = ['slack_bp']