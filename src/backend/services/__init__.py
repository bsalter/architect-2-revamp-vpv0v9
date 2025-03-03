"""
Initialization file for the services package, exposing service classes and providing service factory functionality.
"""

from .validation_service import ValidationService  # Import validation service for form data validation
from .auth_service import AuthService  # Import authentication service for user authentication and authorization
from .user_service import UserService  # Import user service for user management
from .site_service import SiteService  # Import site service for site management and access control
from .interaction_service import InteractionService  # Import interaction service for managing interaction records
from .search_service import SearchService  # Import search service for advanced search functionality


def get_service(service_name: str) -> object:
    """
    Factory function to get a service instance with appropriate dependencies

    Args:
        service_name (str): Name of the service to retrieve

    Returns:
        object: Service instance of the requested type
    """
    if service_name == "ValidationService":
        # Initialize appropriate dependencies for the service
        service = ValidationService()
    elif service_name == "AuthService":
        # Initialize appropriate dependencies for the service
        service = AuthService()
    elif service_name == "UserService":
        # Initialize appropriate dependencies for the service
        service = UserService()
    elif service_name == "SiteService":
        # Initialize appropriate dependencies for the service
        service = SiteService()
    elif service_name == "InteractionService":
        # Initialize appropriate dependencies for the service
        service = InteractionService()
    elif service_name == "SearchService":
        # Initialize appropriate dependencies for the service
        service = SearchService()
    else:
        raise ValueError(f"Unknown service: {service_name}")

    # Return the service instance
    return service


__all__ = [
    "ValidationService",
    "AuthService",
    "UserService",
    "SiteService",
    "InteractionService",
    "SearchService",
    "get_service"
]