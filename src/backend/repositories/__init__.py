"""
Initializes the repositories package and exports repository classes for data access layer in the Interaction Management System. This file serves as the entry point for all repository imports, implementing the repository pattern for database operations with site-scoping support.
"""

from .base_repository import BaseRepository  # Import and re-export the base repository class
from .connection_manager import ConnectionManager  # Import and re-export the connection manager class
from .interaction_repository import InteractionRepository  # Import and re-export the interaction repository class
from .site_repository import SiteRepository  # Import and re-export the site repository class
from .user_repository import UserRepository  # Import and re-export the user repository class

__all__ = [
    "BaseRepository",  # Abstract base class providing common repository operations with site-scoping support
    "ConnectionManager",  # Database connection management and transaction handling
    "InteractionRepository",  # Repository implementation for Interaction entity with specialized search methods
    "SiteRepository",  # Repository implementation for Site entity with user-site relationship management
    "UserRepository",  # Repository implementation for User entity with authentication and site access management
]