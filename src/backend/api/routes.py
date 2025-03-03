"""Centralizes route registration for the Interaction Management System API, connecting controller blueprints to the Flask application. This file serves as the routing hub that organizes API endpoints by their functional domain and ensures proper middleware application."""

from flask import Flask, Blueprint  # flask: version 2.3.2
from .controllers.auth_controller import auth_bp  # src/backend/api/controllers/auth_controller.py
from .controllers.user_controller import user_bp  # src/backend/api/controllers/user_controller.py
from .controllers.site_controller import site_blueprint  # src/backend/api/controllers/site_controller.py
from .controllers.interaction_controller import interaction_blueprint  # src/backend/api/controllers/interaction_controller.py
from .controllers.search_controller import search_blueprint  # src/backend/api/controllers/search_controller.py
from ..logging.structured_logger import StructuredLogger  # src/backend/logging/structured_logger.py

# Initialize structured logger
logger = StructuredLogger(__name__)

# Define API version
API_VERSION = 'v1'


def register_routes(api_blueprint: Blueprint) -> None:
    """Registers all API controller blueprints with the main API blueprint"""
    logger.info("Starting route registration process")

    # Register authentication routes
    logger.info("Registering auth_bp from auth_controller")
    api_blueprint.register_blueprint(auth_bp)

    # Register user management routes
    logger.info("Registering user_bp from user_controller")
    api_blueprint.register_blueprint(user_bp)

    # Register site management routes
    logger.info("Registering site_blueprint from site_controller")
    api_blueprint.register_blueprint(site_blueprint)

    # Register interaction routes
    logger.info("Registering interaction_blueprint from interaction_controller")
    api_blueprint.register_blueprint(interaction_blueprint)

    # Register search routes
    logger.info("Registering search_blueprint from search_controller")
    api_blueprint.register_blueprint(search_blueprint)

    # Apply version prefix to all blueprints
    logger.info(f"Applying version prefix '{API_VERSION}' to all registered blueprints")
    for blueprint in get_blueprints():
        apply_url_prefix(blueprint, API_VERSION)

    logger.info(f"Route registration completed successfully with {len(get_blueprints())} blueprints registered")


def get_blueprints() -> List[Blueprint]:
    """Returns all available API controller blueprints"""
    return [auth_bp, user_bp, site_blueprint, interaction_blueprint, search_blueprint]


def apply_url_prefix(blueprint: Blueprint, version: str) -> None:
    """Applies version prefix to blueprint URL rules"""
    if blueprint.url_prefix:
        blueprint.url_prefix = f"/{version}{blueprint.url_prefix}"
    else:
        blueprint.url_prefix = f"/{version}"
    logger.info(f"Applied version prefix '{version}' to blueprint '{blueprint.name}'")