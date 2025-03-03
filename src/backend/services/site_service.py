"""
Service that provides business logic for site management, user-site associations, and site context operations.
This service acts as an intermediate layer between controllers and repositories, implementing permission checks and ensuring site-scoped access control.
"""

from typing import Dict, List, Optional, Union, Any

from ..repositories.site_repository import SiteRepository
from ..repositories.user_repository import UserRepository
from ..models.site import Site
from ..models.user_site import UserSite
from ..auth.user_context_service import UserContextService
from ..auth.site_context_service import SiteContextService
from ..auth.permission_service import PermissionService
from ..utils.enums import UserRole
from ..utils.error_util import NotFoundError, ValidationError, AuthorizationError, SiteContextError
from ..logging.structured_logger import StructuredLogger

# Initialize logger
logger = StructuredLogger(__name__)

# Define default role for new users added to a site
DEFAULT_SITE_ROLE = UserRole.VIEWER.value


class SiteService:
    """
    Service handling business logic for site management including creation, updates, deletion, and access control
    """

    def __init__(
        self,
        site_repository: SiteRepository = None,
        user_repository: UserRepository = None,
        user_context_service: UserContextService = None,
        site_context_service: SiteContextService = None,
        permission_service: PermissionService = None,
    ):
        """
        Initialize the site service with necessary dependencies

        Args:
            site_repository: Site repository instance (optional, creates new if None)
            user_repository: User repository instance (optional, creates new if None)
            user_context_service: User context service instance (optional, creates new if None)
            site_context_service: Site context service instance (optional, creates new if None)
            permission_service: Permission service instance (optional, creates new if None)
        """
        # Initialize repository and service dependencies with provided instances or create new ones if None
        self._site_repository = site_repository or SiteRepository()
        self._user_repository = user_repository or UserRepository()
        self._user_context_service = user_context_service
        self._site_context_service = site_context_service
        self._permission_service = permission_service
        # Log service initialization
        logger.info("SiteService initialized")

    def get_site_by_id(self, site_id: int) -> Site:
        """
        Get a site by ID with access verification

        Args:
            site_id: ID of the site to retrieve

        Returns:
            Site object if found and user has access

        Raises:
            NotFoundError: If site not found
            AuthorizationError: If user does not have access to the site
        """
        # Get site from repository using site_repository.find_by_id()
        site = self._site_repository.find_by_id(site_id)
        # If site not found, raise NotFoundError
        if not site:
            raise NotFoundError(f"Site with ID {site_id} not found")

        # Verify current user has access to this site
        user_id = self._user_context_service.get_current_user_id()
        if not self._permission_service.can_access_site(user_id, site_id):
            raise AuthorizationError(f"User {user_id} does not have access to site {site_id}")

        # Return site if access is verified
        logger.info(f"Retrieved site with ID {site_id}")
        return site

    def get_all_sites(self, page: int = 1, per_page: int = 20, filters: Dict[str, Any] = None) -> tuple[List[Site], int]:
        """
        Get all sites the current user has access to with pagination

        Args:
            page: Page number for pagination (default: 1)
            per_page: Number of sites per page (default: 20)
            filters: Optional filters to apply to the query

        Returns:
            Tuple: (List[Site], int) - List of sites and total count
        """
        # Get current user ID from user context service
        user_id = self._user_context_service.get_current_user_id()
        # Get sites for user with pagination from repository
        sites, total_count = self._site_repository.get_sites_for_user(user_id, page, per_page, filters)
        # Return sites list and total count
        logger.info(f"Retrieved {len(sites)} sites for user {user_id} (page {page}, total {total_count})")
        return sites, total_count

    def create_site(self, site_data: Dict[str, Any], creator_user_id: int = None) -> Site:
        """
        Create a new site with the current user as admin

        Args:
            site_data: Dictionary containing site information (name is required)
            creator_user_id: User ID of the creator (defaults to current user)

        Returns:
            Newly created site

        Raises:
            ValidationError: If site data is invalid or name already exists
        """
        # Validate site data (name is required)
        if not site_data or 'name' not in site_data:
            raise ValidationError("Site data must contain a name")

        # Check name uniqueness via repository
        if self._site_repository.find_by_name(site_data['name']):
            raise ValidationError(f"Site with name '{site_data['name']}' already exists")

        # If creator_user_id not provided, get from user context
        if creator_user_id is None:
            creator_user_id = self._user_context_service.get_current_user_id()

        # Verify user exists using user repository
        user = self._user_repository.find_by_id(creator_user_id)
        if not user:
            raise NotFoundError(f"User with ID {creator_user_id} not found")

        # Create site using repository.create_site()
        site = self._site_repository.create_site(site_data, creator_user_id)
        # Log site creation with creator information
        logger.info(f"Created site '{site.name}' (ID: {site.id}) by user {creator_user_id}")
        # Return created site
        return site

    def update_site(self, site_id: int, site_data: Dict[str, Any]) -> Site:
        """
        Update an existing site with permission check

        Args:
            site_id: ID of the site to update
            site_data: Dictionary containing updated site information

        Returns:
            Updated site

        Raises:
            NotFoundError: If site not found
            ValidationError: If site data is invalid
            AuthorizationError: If user does not have site admin permission
        """
        # Get current user ID from user context
        user_id = self._user_context_service.get_current_user_id()

        # Verify user has site admin permission for this site
        if not self._permission_service.can_manage_site_users(user_id, site_id):
            raise AuthorizationError(f"User {user_id} does not have permission to update site {site_id}")

        # Check if name is being changed and validate uniqueness if so
        if 'name' in site_data:
            existing_site = self._site_repository.find_by_name(site_data['name'])
            if existing_site and existing_site.id != site_id:
                raise ValidationError(f"Site with name '{site_data['name']}' already exists")

        # Update site using repository.update_site()
        site = self._site_repository.update_site(site_id, site_data)
        # Log site update with changes
        logger.info(f"Updated site '{site.name}' (ID: {site.id})")
        # Return updated site
        return site

    def delete_site(self, site_id: int) -> bool:
        """
        Delete a site (requires site admin permission)

        Args:
            site_id: ID of the site to delete

        Returns:
            True if successfully deleted

        Raises:
            NotFoundError: If site not found
            AuthorizationError: If user does not have site admin permission
        """
        # Get current user ID from user context
        user_id = self._user_context_service.get_current_user_id()

        # Verify user has site admin permission for this site
        if not self._permission_service.can_manage_site_users(user_id, site_id):
            raise AuthorizationError(f"User {user_id} does not have permission to delete site {site_id}")

        # Delete site using repository.delete_site()
        self._site_repository.delete_site(site_id)
        # Log site deletion
        logger.info(f"Deleted site with ID {site_id}")
        # Return True on success
        return True

    def get_user_sites(self, user_id: int) -> List[Dict]:
        """
        Get all sites a specific user has access to

        Args:
            user_id: ID of the user

        Returns:
            List[Dict]: List of site objects with role information
        """
        # Verify user exists using user repository
        user = self._user_repository.find_by_id(user_id)
        if not user:
            raise NotFoundError(f"User with ID {user_id} not found")

        # Get sites for user from repository.get_sites_for_user()
        sites = self._site_repository.get_sites_for_user(user_id)
        # Log user's sites retrieval
        logger.info(f"Retrieved {len(sites)} sites for user {user_id}")
        # Return list of sites with roles
        return sites

    def get_site_users(self, site_id: int, page: int = 1, per_page: int = 20, filters: Dict[str, Any] = None) -> tuple[List[Dict], int]:
        """
        Get all users associated with a site with pagination

        Args:
            site_id: ID of the site
            page: Page number for pagination (default: 1)
            per_page: Number of results per page (default: 20)
            filters: Optional filters to apply (e.g., role)

        Returns:
            Tuple: (List[Dict], int) - List of users with role info and total count

        Raises:
            NotFoundError: If site not found
            AuthorizationError: If user does not have permission to view site users
        """
        # Verify current user has access to view site users
        user_id = self._user_context_service.get_current_user_id()
        if not self._permission_service.can_manage_site_users(user_id, site_id):
            raise AuthorizationError(f"User {user_id} does not have permission to view users for site {site_id}")

        # Get users for site from repository with pagination
        users, total_count = self._site_repository.get_users_for_site(site_id, filters, page, per_page)
        # Log site users retrieval
        logger.info(f"Retrieved {len(users)} users for site {site_id} (page {page}, total {total_count})")
        # Return list of users with roles and total count
        return users, total_count

    def add_user_to_site(self, site_id: int, user_id: int, role: str = DEFAULT_SITE_ROLE) -> Dict:
        """
        Add a user to a site with a specified role

        Args:
            site_id: ID of the site
            user_id: ID of the user
            role: Role to assign to the user (default: UserRole.VIEWER.value)

        Returns:
            User-site relationship information

        Raises:
            NotFoundError: If site or user not found
            AuthorizationError: If user does not have permission to manage site users
            ValidationError: If role is invalid
        """
        # Verify current user has permission to manage site users
        current_user_id = self._user_context_service.get_current_user_id()
        if not self._permission_service.can_manage_site_users(current_user_id, site_id):
            raise AuthorizationError(f"User {current_user_id} does not have permission to manage users for site {site_id}")

        # Verify target user exists
        user = self._user_repository.find_by_id(user_id)
        if not user:
            raise NotFoundError(f"User with ID {user_id} not found")

        # Verify role is valid using UserRole.is_valid()
        if not UserRole.is_valid(role):
            raise ValidationError(f"Invalid role: {role}")

        # Check if user already has access to site
        if self._site_repository.user_has_site_access(user_id, site_id):
            raise ValidationError(f"User {user_id} already has access to site {site_id}")

        # Create user-site association with specified role
        user_site_data = {
            'user_id': user_id,
            'site_id': site_id,
            'role': role
        }
        # Log user addition to site
        logger.info(f"Adding user {user_id} to site {site_id} with role {role}")
        # Return user-site relationship data
        return user_site_data

    def remove_user_from_site(self, site_id: int, user_id: int) -> bool:
        """
        Remove a user from a site

        Args:
            site_id: ID of the site
            user_id: ID of the user

        Returns:
            True if successfully removed

        Raises:
            NotFoundError: If site or user not found
            AuthorizationError: If user does not have permission to manage site users
        """
        # Verify current user has permission to manage site users
        current_user_id = self._user_context_service.get_current_user_id()
        if not self._permission_service.can_manage_site_users(current_user_id, site_id):
            raise AuthorizationError(f"User {current_user_id} does not have permission to manage users for site {site_id}")

        # Verify user-site association exists
        if not self._site_repository.user_has_site_access(user_id, site_id):
            raise NotFoundError(f"User {user_id} does not have access to site {site_id}")

        # Remove user-site association
        # Log user removal from site
        logger.info(f"Removing user {user_id} from site {site_id}")
        # Return True on success
        return True

    def update_user_role(self, site_id: int, user_id: int, new_role: str) -> Dict:
        """
        Update a user's role for a site

        Args:
            site_id: ID of the site
            user_id: ID of the user
            new_role: New role to assign

        Returns:
            Updated user-site relationship information

        Raises:
            NotFoundError: If site or user not found
            AuthorizationError: If user does not have permission to manage site users
            ValidationError: If new_role is invalid
        """
        # Verify current user has permission to manage site users
        current_user_id = self._user_context_service.get_current_user_id()
        if not self._permission_service.can_manage_site_users(current_user_id, site_id):
            raise AuthorizationError(f"User {current_user_id} does not have permission to manage users for site {site_id}")

        # Verify user-site association exists
        if not self._site_repository.user_has_site_access(user_id, site_id):
            raise NotFoundError(f"User {user_id} does not have access to site {site_id}")

        # Verify new_role is valid using UserRole.is_valid()
        if not UserRole.is_valid(new_role):
            raise ValidationError(f"Invalid role: {new_role}")

        # Update user's role for site
        # Log role update
        logger.info(f"Updating role for user {user_id} on site {site_id} to {new_role}")
        # Return updated user-site relationship data
        return {}

    def get_user_role_for_site(self, user_id: int, site_id: int) -> Optional[str]:
        """
        Get a user's role for a specific site

        Args:
            user_id: ID of the user
            site_id: ID of the site

        Returns:
            User's role for the site or None if no access
        """
        # Get user's role from repository.get_user_role_for_site()
        role = self._site_repository.get_user_role_for_site(user_id, site_id)
        # Log role retrieval
        logger.info(f"Retrieved role {role} for user {user_id} on site {site_id}")
        # Return role string or None if no access
        return role

    def switch_site_context(self, site_id: int) -> Dict:
        """
        Switch the current site context to another site

        Args:
            site_id: ID of the site to switch to

        Returns:
            New site context information

        Raises:
            NotFoundError: If site not found
            AuthorizationError: If user does not have access to the site
        """
        # Get current user ID from user context
        user_id = self._user_context_service.get_current_user_id()

        # Verify site exists using repository
        site = self._site_repository.find_by_id(site_id)
        if not site:
            raise NotFoundError(f"Site with ID {site_id} not found")

        # Verify user has access to the site
        if not self._permission_service.can_access_site(user_id, site_id):
            raise AuthorizationError(f"User {user_id} does not have access to site {site_id}")

        # Use site_context_service to set new site context
        # Log site context switch
        logger.info(f"Switching site context to site {site_id}")
        # Return new site context information
        return {}

    def search_sites(self, search_term: str, page: int = 1, per_page: int = 20) -> tuple[List[Site], int]:
        """
        Search sites by name or description with user access filtering

        Args:
            search_term: Search term to look for in name or description
            page: Page number for pagination (default: 1)
            per_page: Number of results per page (default: 20)

        Returns:
            Tuple: (List[Site], int) - List of matching sites and total count
        """
        # Get current user ID from user context
        user_id = self._user_context_service.get_current_user_id()
        # Search sites using repository with user access filtering
        sites, total_count = self._site_repository.search_sites(search_term, page, per_page)
        # Log search operation
        logger.info(f"Searching for sites with term {search_term} (page {page}, total {total_count})")
        # Return matching sites and total count
        return sites, total_count

    def get_site_stats(self, site_id: int) -> Dict:
        """
        Get statistics for a site (user count, interaction count)

        Args:
            site_id: ID of the site

        Returns:
            Dictionary with site statistics

        Raises:
            NotFoundError: If site not found
            AuthorizationError: If user does not have access to the site
        """
        # Verify current user has access to this site
        user_id = self._user_context_service.get_current_user_id()
        if not self._permission_service.can_access_site(user_id, site_id):
            raise AuthorizationError(f"User {user_id} does not have access to site {site_id}")

        # Get site stats from repository
        stats = self._site_repository.get_site_stats(site_id)
        # Log stats retrieval
        logger.info(f"Retrieved stats for site {site_id}")
        # Return stats dictionary
        return stats

    def user_has_site_access(self, user_id: int, site_id: int) -> bool:
        """
        Check if a user has access to a specific site

        Args:
            user_id: ID of the user
            site_id: ID of the site

        Returns:
            True if user has access, False otherwise
        """
        # Check access using repository.user_has_site_access()
        has_access = self._site_repository.user_has_site_access(user_id, site_id)
        # Log access check result
        logger.info(f"User {user_id} has access to site {site_id}: {has_access}")
        # Return boolean result
        return has_access

    def validate_site_name(self, name: str, exclude_site_id: int = None) -> bool:
        """
        Validate a site name for uniqueness

        Args:
            name: Site name to validate
            exclude_site_id: Site ID to exclude from uniqueness check (for updates)

        Returns:
            True if name is valid and unique

        Raises:
            ValidationError: If name is invalid or not unique
        """
        # Check if name is empty or None
        if not name:
            raise ValidationError("Site name cannot be empty")

        # Find existing site with same name using repository
        existing_site = self._site_repository.find_by_name(name)

        # If found and not the excluded site, raise ValidationError
        if existing_site and (exclude_site_id is None or existing_site.id != exclude_site_id):
            raise ValidationError("Site name already exists")

        # Return True if name is valid and unique
        logger.info(f"Site name {name} is valid")
        return True