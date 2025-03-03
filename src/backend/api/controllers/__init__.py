"""
Initialization file for the controllers package that imports and exposes controller blueprints to the application.
This file makes the controller blueprints accessible from the controllers package level to simplify imports in the route registration process.
"""

from flask import Blueprint

from .auth_controller import auth_blueprint  # auth_blueprint: Authentication routes blueprint
from .user_controller import user_blueprint  # user_blueprint: User management routes blueprint
from .site_controller import site_blueprint as site_bp  # site_bp: Site management routes blueprint
from .interaction_controller import interaction_blueprint  # interaction_blueprint: Interaction management routes blueprint
from .search_controller import search_blueprint  # search_blueprint: Search functionality routes blueprint

__all__ = [
    'auth_blueprint',
    'user_blueprint',
    'site_bp',
    'interaction_blueprint',
    'search_blueprint'
]