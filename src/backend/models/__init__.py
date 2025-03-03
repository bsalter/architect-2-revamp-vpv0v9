"""
Models package for the Interaction Management System.

This package contains SQLAlchemy ORM models that define the database schema and
business logic for the application's core entities. The models establish relationships
between users, sites, and interactions to implement the site-scoped access control
and data management features of the system.

This __init__.py file re-exports all model classes to make them accessible through
a single import statement like `from backend.models import User, Site, Interaction`.
"""

# Import all model classes
from .base import Base
from .user import User
from .site import Site
from .user_site import UserSite
from .interaction import Interaction
from .interaction_history import InteractionHistory

# Define which symbols should be exported when using 'from models import *'
__all__ = [
    'Base',
    'User',
    'Site',
    'UserSite',
    'Interaction',
    'InteractionHistory'
]