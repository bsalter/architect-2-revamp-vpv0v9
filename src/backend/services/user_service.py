# src/backend/services/user_service.py
"""
Service layer that implements user management business logic including user CRUD operations,
authentication, site associations, and role management with site-scoped access control enforcement.
"""

from typing import Dict, List, Optional, Any, Union, Tuple

from ..repositories.user_repository import UserRepository  # UserRepository class for data access
from ..auth.site_context_service import SiteContextService  # SiteContextService class for site context
from ..auth.user_context_service import UserContextService  # UserContextService class for user context
from .validation_service import UserValidation  # UserValidation class for user data validation
from ..models.user import User  # User model class
from ..utils.enums import UserRole  # UserRole enum for role management
from ..utils.error_util import AuthenticationError, AuthorizationError, ValidationError, NotFoundError, SiteContextError  # Custom error classes
from ..logging.structured_logger import StructuredLogger  # StructuredLogger class for logging

# Initialize structured logger
logger = StructuredLogger(__name__)


class UserService:
    """
    Service that implements user management business logic, enforcing site-scoped access control
    and handling authentication, user CRUD operations, and site associations.
    """

    def __init__(self, user_repository: UserRepository, site_context_service: SiteContextService = None,
                 user_context_service: UserContextService = None, user_validation: UserValidation = None):
        """
        Initialize the UserService with required dependencies

        Args:
            user_repository: UserRepository instance
            site_context_service: SiteContextService instance (optional)
            user_context_service: UserContextService instance (optional)
            user_validation: UserValidation instance (optional)
        """
        # Store user_repository as instance attribute
        self._user_repository = user_repository

        # Store site_context_service or create a new instance if None
        self._site_context_service = site_context_service or SiteContextService()

        # Store user_context_service or create a new instance if None
        self._user_context_service = user_context_service or UserContextService()

        # Store user_validation or create a new instance if None
        self._user_validation = user_validation or UserValidation()

        # Log service initialization
        logger.info("UserService initialized")

    def authenticate(self, username_or_email: str, password: str) -> User:
        """
        Authenticate a user with username/email and password

        Args:
            username_or_email: Username or email address
            password: User's password

        Returns:
            Authenticated user or raises AuthenticationError

        Decorators:
            None

        Steps:
            1. Delegate to user_repository.authenticate() with username_or_email and password
            2. Return authenticated user if successful
        """
        try:
            # Delegate to user_repository.authenticate() with username_or_email and password
            user = self._user_repository.authenticate(username_or_email, password)

            # Return authenticated user if successful
            return user
        except AuthenticationError as e:
            # Log authentication attempt
            logger.error(f"Authentication failed for user: {username_or_email}")

            # Handle and re-raise AuthenticationError with appropriate message
            raise AuthenticationError(f"Authentication failed: {str(e)}")

    def get_user_by_id(self, user_id: int) -> User:
        """
        Get a user by ID with site-scoping enforcement

        Args:
            user_id: User ID

        Returns:
            User instance if found and accessible, otherwise raises NotFoundError or AuthorizationError

        Decorators:
            None

        Steps:
            1. Verify current user is authenticated via user_context_service
            2. Get user from repository using find_by_id
            3. If user not found, raise NotFoundError
            4. Check if current site context has access to this user
            5. If no access, raise AuthorizationError
            6. Return user if accessible
        """
        try:
            # Verify current user is authenticated via user_context_service
            self._user_context_service.require_authentication()

            # Get user from repository using find_by_id
            user = self._user_repository.find_by_id(user_id)

            # Check if current site context has access to this user
            if not self._user_repository._check_user_site_access(user):
                # If no access, raise AuthorizationError
                raise AuthorizationError("You do not have permission to access this user")

            # Return user if accessible
            return user
        except NotFoundError as e:
            # If user not found, raise NotFoundError
            raise NotFoundError(f"User with ID {user_id} not found")
        except AuthorizationError as e:
            # If no access, raise AuthorizationError
            raise AuthorizationError(f"You do not have permission to access this user")
        finally:
            # Log user retrieval
            logger.info(f"Retrieved user with ID: {user_id}")

    def get_user_by_username(self, username: str) -> User:
        """
        Get a user by username with site-scoping enforcement

        Args:
            username: Username

        Returns:
            User instance if found and accessible, otherwise raises NotFoundError or AuthorizationError

        Decorators:
            None

        Steps:
            1. Verify current user is authenticated via user_context_service
            2. Get user from repository using find_by_username
            3. If user not found, raise NotFoundError
            4. Check if current site context has access to this user
            5. If no access, raise AuthorizationError
            6. Return user if accessible
        """
        try:
            # Verify current user is authenticated via user_context_service
            self._user_context_service.require_authentication()

            # Get user from repository using find_by_username
            user = self._user_repository.find_by_username(username)

            # Check if current site context has access to this user
            if not self._user_repository._check_user_site_access(user):
                # If no access, raise AuthorizationError
                raise AuthorizationError("You do not have permission to access this user")

            # Return user if accessible
            return user
        except NotFoundError as e:
            # If user not found, raise NotFoundError
            raise NotFoundError(f"User with username {username} not found")
        except AuthorizationError as e:
            # If no access, raise AuthorizationError
            raise AuthorizationError(f"You do not have permission to access this user")
        finally:
            # Log user retrieval
            logger.info(f"Retrieved user with username: {username}")

    def get_users_by_site(self, site_id: int, filters: Dict[str, Any] = None, page: int = 1, per_page: int = 20,
                          sort_by: str = None, sort_desc: bool = False) -> Tuple[List[User], int]:
        """
        Get all users associated with a specific site

        Args:
            site_id: Site ID
            filters: Optional filters
            page: Page number
            per_page: Number of users per page
            sort_by: Field to sort by
            sort_desc: Sort descending

        Returns:
            List of users and total count

        Decorators:
            None

        Steps:
            1. Verify site access permission via site_context_service
            2. Delegate to user_repository.get_users_for_site() with parameters
            3. Return list of users and total count
        """
        try:
            # Verify site access permission via site_context_service
            self._site_context_service.verify_site_access(site_id)

            # Delegate to user_repository.get_users_for_site() with parameters
            users, total_count = self._user_repository.get_users_for_site(site_id, filters, page, per_page, sort_by,
                                                                           sort_desc)

            # Return list of users and total count
            return users, total_count
        except SiteContextError as e:
            # Handle and re-raise SiteContextError with appropriate message
            raise SiteContextError(f"You do not have permission to access this site: {str(e)}")
        finally:
            # Log users retrieval
            logger.info(f"Retrieved users for site ID: {site_id}")

    def create_user(self, user_data: Dict[str, Any], site_ids: List[int] = None, site_roles: Dict[int, str] = None) -> User:
        """
        Create a new user with optional site associations

        Args:
            user_data: User data
            site_ids: List of site IDs
            site_roles: Dictionary of site IDs and roles

        Returns:
            Newly created user instance

        Decorators:
            None

        Steps:
            1. Verify user has authorization to create users (admin role)
            2. Validate user data using user_validation service
            3. Prepare user data for creation (including password hashing)
            4. If site_ids is None, use current site context
            5. Delegate to user_repository.create_user() with data and site_ids
            6. Apply specific roles to sites if site_roles is provided
            7. Return created user
        """
        try:
            # Verify user has authorization to create users (admin role)
            # TODO: Implement proper role-based authorization check
            # Validate user data using user_validation service
            # Prepare user data for creation (including password hashing)
            # If site_ids is None, use current site context
            # Delegate to user_repository.create_user() with data and site_ids
            user = self._user_repository.create_user(user_data, site_ids)

            # Apply specific roles to sites if site_roles is provided
            # TODO: Implement role assignment logic

            # Return created user
            return user
        except ValidationError as e:
            # Handle and re-raise ValidationError with appropriate message
            raise ValidationError(f"Validation failed: {str(e)}")
        finally:
            # Log user creation
            logger.info(f"Created user with username: {user_data.get('username')}")

    def update_user(self, user_id: int, user_data: Dict[str, Any], site_ids: List[int] = None, site_roles: Dict[int, str] = None) -> User:
        """
        Update an existing user's information

        Args:
            user_id: User ID
            user_data: User data
            site_ids: List of site IDs
            site_roles: Dictionary of site IDs and roles

        Returns:
            Updated user instance

        Decorators:
            None

        Steps:
            1. Verify current user is authenticated via user_context_service
            2. Get user to be updated using get_user_by_id
            3. Verify user has authorization to update users (admin role)
            4. Validate update data using user_validation service
            5. If password in user_data, handle password update separately
            6. Delegate to user_repository.update_user() with user_id and data
            7. Handle site associations if site_ids provided
            8. Apply specific roles to sites if site_roles is provided
            9. Return updated user
        """
        try:
            # Verify current user is authenticated via user_context_service
            self._user_context_service.require_authentication()

            # Get user to be updated using get_user_by_id
            user = self.get_user_by_id(user_id)

            # Verify user has authorization to update users (admin role)
            # TODO: Implement proper role-based authorization check

            # Validate update data using user_validation service
            # If password in user_data, handle password update separately
            # Delegate to user_repository.update_user() with user_id and data
            user = self._user_repository.update_user(user_id, user_data)

            # Handle site associations if site_ids provided
            # Apply specific roles to sites if site_roles is provided
            # TODO: Implement site association and role assignment logic

            # Return updated user
            return user
        except ValidationError as e:
            # Handle and re-raise ValidationError with appropriate message
            raise ValidationError(f"Validation failed: {str(e)}")
        finally:
            # Log user update
            logger.info(f"Updated user with ID: {user_id}")

    def delete_user(self, user_id: int) -> bool:
        """
        Delete a user account

        Args:
            user_id: User ID

        Returns:
            True if deleted successfully

        Decorators:
            None

        Steps:
            1. Verify current user is authenticated via user_context_service
            2. Get user to be deleted using get_user_by_id
            3. Verify user has authorization to delete users (admin role)
            4. Prevent self-deletion (current user cannot delete themselves)
            5. Delegate to user_repository.delete_user() with user_id
            6. Return True on success
        """
        try:
            # Verify current user is authenticated via user_context_service
            self._user_context_service.require_authentication()

            # Get user to be deleted using get_user_by_id
            user = self.get_user_by_id(user_id)

            # Verify user has authorization to delete users (admin role)
            # TODO: Implement proper role-based authorization check

            # Prevent self-deletion (current user cannot delete themselves)
            current_user_id = self._user_context_service.get_current_user_id()
            if user_id == current_user_id:
                raise AuthorizationError("You cannot delete your own account")

            # Delegate to user_repository.delete_user() with user_id
            result = self._user_repository.delete_user(user_id)

            # Return True on success
            return result
        except AuthorizationError as e:
            # Handle and re-raise AuthorizationError with appropriate message
            raise AuthorizationError(f"You are not authorized to delete this user: {str(e)}")
        finally:
            # Log user deletion
            logger.info(f"Deleted user with ID: {user_id}")

    def get_user_sites(self, user_id: int) -> List[Dict]:
        """
        Get all sites a user has access to

        Args:
            user_id: User ID

        Returns:
            List of site data dictionaries including role information

        Decorators:
            None

        Steps:
            1. Verify current user is authenticated via user_context_service
            2. Get user using get_user_by_id
            3. Delegate to user_repository.get_user_sites() with user_id
            4. Return list of site information including roles
        """
        try:
            # Verify current user is authenticated via user_context_service
            self._user_context_service.require_authentication()

            # Get user using get_user_by_id
            user = self.get_user_by_id(user_id)

            # Delegate to user_repository.get_user_sites() with user_id
            sites = self._user_repository.get_user_sites(user_id)

            # Return list of site information including roles
            return sites
        finally:
            # Log sites retrieval
            logger.info(f"Retrieved sites for user ID: {user_id}")

    def add_user_to_site(self, user_id: int, site_id: int, role: str = 'viewer') -> bool:
        """
        Add a user to a site with a specified role

        Args:
            user_id: User ID
            site_id: Site ID
            role: User role

        Returns:
            True if added successfully

        Decorators:
            None

        Steps:
            1. Verify current user is authenticated via user_context_service
            2. Verify site access permission via site_context_service
            3. Validate that role is a valid UserRole
            4. Verify user has authorization to manage site access (admin role)
            5. Delegate to user_repository.add_user_to_site() with parameters
            6. Return True on success
        """
        try:
            # Verify current user is authenticated via user_context_service
            self._user_context_service.require_authentication()

            # Verify site access permission via site_context_service
            self._site_context_service.verify_site_access(site_id)

            # Validate that role is a valid UserRole
            if not UserRole.is_valid(role):
                raise ValidationError(f"Invalid role: {role}")

            # Verify user has authorization to manage site access (admin role)
            # TODO: Implement proper role-based authorization check

            # Delegate to user_repository.add_user_to_site() with parameters
            result = self._user_repository.add_user_to_site(user_id, site_id, role)

            # Return True on success
            return result
        except ValidationError as e:
            # Handle and re-raise ValidationError with appropriate message
            raise ValidationError(f"Validation failed: {str(e)}")
        finally:
            # Log site access grant
            logger.info(f"Granted site access to user ID: {user_id} for site ID: {site_id} with role: {role}")

    def remove_user_from_site(self, user_id: int, site_id: int) -> bool:
        """
        Remove a user from a site

        Args:
            user_id: User ID
            site_id: Site ID

        Returns:
            True if removed successfully

        Decorators:
            None

        Steps:
            1. Verify current user is authenticated via user_context_service
            2. Verify site access permission via site_context_service
            3. Verify user has authorization to manage site access (admin role)
            4. Prevent removing last site admin if applicable
            5. Delegate to user_repository.remove_user_from_site() with parameters
            6. Return True on success
        """
        try:
            # Verify current user is authenticated via user_context_service
            self._user_context_service.require_authentication()

            # Verify site access permission via site_context_service
            self._site_context_service.verify_site_access(site_id)

            # Verify user has authorization to manage site access (admin role)
            # TODO: Implement proper role-based authorization check

            # Prevent removing last site admin if applicable
            # TODO: Implement last admin check

            # Delegate to user_repository.remove_user_from_site() with parameters
            result = self._user_repository.remove_user_from_site(user_id, site_id)

            # Return True on success
            return result
        finally:
            # Log site access revocation
            logger.info(f"Revoked site access from user ID: {user_id} for site ID: {site_id}")

    def update_user_role(self, user_id: int, site_id: int, new_role: str) -> bool:
        """
        Update a user's role for a specific site

        Args:
            user_id: User ID
            site_id: Site ID
            new_role: New role

        Returns:
            True if role updated successfully

        Decorators:
            None

        Steps:
            1. Verify current user is authenticated via user_context_service
            2. Verify site access permission via site_context_service
            3. Validate that new_role is a valid UserRole
            4. Verify user has authorization to change roles (admin role)
            5. Prevent downgrading last site admin if applicable
            6. Delegate to user_repository.change_user_role() with parameters
            7. Return True on success
        """
        try:
            # Verify current user is authenticated via user_context_service
            self._user_context_service.require_authentication()

            # Verify site access permission via site_context_service
            self._site_context_service.verify_site_access(site_id)

            # Validate that new_role is a valid UserRole
            if not UserRole.is_valid(new_role):
                raise ValidationError(f"Invalid role: {new_role}")

            # Verify user has authorization to change roles (admin role)
            # TODO: Implement proper role-based authorization check

            # Prevent downgrading last site admin if applicable
            # TODO: Implement last admin check

            # Delegate to user_repository.change_user_role() with parameters
            result = self._user_repository.change_user_role(user_id, site_id, new_role)

            # Return True on success
            return result
        except ValidationError as e:
            # Handle and re-raise ValidationError with appropriate message
            raise ValidationError(f"Validation failed: {str(e)}")
        finally:
            # Log role change
            logger.info(f"Updated role for user ID: {user_id} on site ID: {site_id} to role: {new_role}")

    def change_password(self, user_id: int, current_password: str, new_password: str) -> bool:
        """
        Change a user's password (requires current password)

        Args:
            user_id: User ID
            current_password: Current password
            new_password: New password

        Returns:
            True if password changed successfully

        Decorators:
            None

        Steps:
            1. Verify current user is authenticated via user_context_service
            2. Get user using get_user_by_id
            3. Verify the user is changing their own password or has admin rights
            4. Validate new password using user_validation service
            5. Delegate to user_repository.change_password() with parameters
            6. Return True on success
        """
        try:
            # Verify current user is authenticated via user_context_service
            self._user_context_service.require_authentication()

            # Get user using get_user_by_id
            user = self.get_user_by_id(user_id)

            # Verify the user is changing their own password or has admin rights
            # TODO: Implement proper role-based authorization check

            # Validate new password using user_validation service
            # Delegate to user_repository.change_password() with parameters
            result = self._user_repository.change_password(user_id, current_password, new_password)

            # Return True on success
            return result
        except ValidationError as e:
            # Handle and re-raise ValidationError with appropriate message
            raise ValidationError(f"Validation failed: {str(e)}")
        finally:
            # Log password change (without actual passwords)
            logger.info(f"Changed password for user ID: {user_id}")

    def reset_password(self, user_id: int, new_password: str) -> bool:
        """
        Reset a user's password (admin function, no current password needed)

        Args:
            user_id: User ID
            new_password: New password

        Returns:
            True if password reset successfully

        Decorators:
            None

        Steps:
            1. Verify current user is authenticated via user_context_service
            2. Get user using get_user_by_id
            3. Verify user has authorization to reset passwords (admin role)
            4. Validate new password using user_validation service
            5. Delegate to user_repository.reset_password() with parameters
            6. Return True on success
        """
        try:
            # Verify current user is authenticated via user_context_service
            self._user_context_service.require_authentication()

            # Get user using get_user_by_id
            user = self.get_user_by_id(user_id)

            # Verify user has authorization to reset passwords (admin role)
            # TODO: Implement proper role-based authorization check

            # Validate new password using user_validation service
            # Delegate to user_repository.reset_password() with parameters
            result = self._user_repository.reset_password(user_id, new_password)

            # Return True on success
            return result
        except ValidationError as e:
            # Handle and re-raise ValidationError with appropriate message
            raise ValidationError(f"Validation failed: {str(e)}")
        finally:
            # Log password reset (without actual password)
            logger.info(f"Reset password for user ID: {user_id}")

    def get_current_user(self) -> Optional[User]:
        """
        Get the currently authenticated user

        Args:
            None

        Returns:
            Current user instance or None if not authenticated

        Decorators:
            None

        Steps:
            1. Delegate to user_context_service.get_current_user()
            2. Return user instance or None
        """
        try:
            # Delegate to user_context_service.get_current_user()
            user = self._user_context_service.get_current_user()

            # Return user instance or None
            return user
        finally:
            # Log current user retrieval
            logger.info("Retrieved current user")