"""
Authentication module for the Interaction Management System.

This module provides authentication, authorization, and site-scoped access control
functionality for the application. It serves as the entry point for all authentication-related
features and provides a simplified interface for other modules to interact with 
the authentication system.
"""

# Import components for re-export
from .auth0 import Auth0Client
from .token_service import TokenService
from .permission_service import PermissionService
from .user_context_service import UserContext, UserContextService
from .site_context_service import SiteContext, SiteContextService

# Module version
__version__ = "1.0.0"