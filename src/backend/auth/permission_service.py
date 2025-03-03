"""
Permission Service Module for the Interaction Management System.

This service is responsible for managing role-based authorization with site-scoping
to ensure users can only perform actions they're authorized for within their assigned sites.
It implements the permission matrix that defines what actions each role can perform
on different resource types.
"""

from typing import Dict, List, Optional, Union, Any

from ..repositories.user_repository import UserRepository
from ..utils.enums import UserRole
from ..utils.error_util import AuthorizationError, SiteContextError
from ..logging.structured_logger import StructuredLogger

# Configure structured logger
logger = StructuredLogger(__name__)

# Default role for users without explicit site assignments
DEFAULT_SITE_ROLE = UserRole.VIEWER.value


class PermissionService:
    """
    Service that handles authorization and permission checking throughout the application.
    
    This service manages the permission matrix that defines what actions each role can perform
    on different resource types and enforces site-scoped data access to maintain data isolation
    between organizational sites.
    """
    
    def __init__(self, user_repository: UserRepository):
        """
        Initialize the permission service with required dependencies.
        
        Args:
            user_repository: Repository for accessing user and site relationship data
        """
        self._user_repository = user_repository
        
        # Initialize permission matrix defining permissions for each role
        self._permission_matrix: Dict[str, Dict[str, List[str]]] = {
            'interaction': {
                # Site admins can perform all operations on interactions
                UserRole.SITE_ADMIN.value: ['create', 'read', 'update', 'delete'],
                # Editors can create, read, and update interactions
                UserRole.EDITOR.value: ['create', 'read', 'update'],
                # Viewers can only read interactions
                UserRole.VIEWER.value: ['read']
            },
            'user': {
                # Site admins can manage users for their site
                UserRole.SITE_ADMIN.value: ['read', 'create', 'update', 'delete', 'manage_roles', 'manage_users'],
                # Editors can read user information
                UserRole.EDITOR.value: ['read'],
                # Viewers can read limited user information
                UserRole.VIEWER.value: ['read']
            }
        }
        
        logger.info("PermissionService initialized with permission matrix")
    
    def get_user_role_for_site(self, user_id: int, site_id: int) -> Optional[str]:
        """
        Get a user's role for a specific site.
        
        Args:
            user_id: ID of the user
            site_id: ID of the site
            
        Returns:
            User's role for the site or None if no access
        """
        # Get user's sites from repository
        sites = self._user_repository.get_user_sites(user_id)
        
        # Find the site in the user's site list
        for site in sites:
            if site['id'] == site_id:
                role = site['role']
                logger.debug(f"User {user_id} has role '{role}' for site {site_id}")
                return role
        
        logger.debug(f"User {user_id} has no access to site {site_id}")
        return None
    
    def get_highest_site_role(self, user_id: int) -> str:
        """
        Get the highest role a user has across all their accessible sites.
        
        Args:
            user_id: ID of the user
            
        Returns:
            Highest role the user has across sites
        """
        # Get user's sites
        sites = self._user_repository.get_user_sites(user_id)
        
        if not sites:
            logger.debug(f"User {user_id} has no site access, returning default role")
            return DEFAULT_SITE_ROLE
        
        # Define role hierarchy (higher value = higher privilege)
        role_hierarchy = {
            UserRole.SITE_ADMIN.value: 3,
            UserRole.EDITOR.value: 2,
            UserRole.VIEWER.value: 1
        }
        
        # Find highest role based on hierarchy
        highest_role = DEFAULT_SITE_ROLE
        highest_value = 0
        
        for site in sites:
            role = site['role']
            if role in role_hierarchy and role_hierarchy[role] > highest_value:
                highest_role = role
                highest_value = role_hierarchy[role]
        
        logger.debug(f"User {user_id} has highest role '{highest_role}' across all sites")
        return highest_role
    
    def has_permission(self, user_id: int, site_id: int, resource_type: str, permission: str) -> bool:
        """
        Check if user has a specific permission for a resource type.
        
        Args:
            user_id: ID of the user
            site_id: ID of the site
            resource_type: Type of resource (e.g., 'interaction', 'user')
            permission: Permission to check (e.g., 'create', 'read', 'update', 'delete')
            
        Returns:
            True if user has permission, False otherwise
        """
        # Get user's role for the site
        role = self.get_user_role_for_site(user_id, site_id)
        
        # If user has no access to the site, deny permission
        if role is None:
            logger.debug(f"User {user_id} has no access to site {site_id}, permission denied")
            return False
        
        # Check if the resource_type exists in the permission matrix
        if resource_type not in self._permission_matrix:
            logger.warning(f"Resource type '{resource_type}' not found in permission matrix")
            return False
        
        # Check if the role exists in the permission matrix for the resource
        if role not in self._permission_matrix[resource_type]:
            logger.warning(f"Role '{role}' not found in permission matrix for '{resource_type}'")
            return False
        
        # Check if the permission is in the list of allowed permissions for the role
        has_permission = permission in self._permission_matrix[resource_type][role]
        
        logger.debug(
            f"User {user_id} with role '{role}' {'' if has_permission else 'does not '}have '{permission}' "
            f"permission for '{resource_type}' in site {site_id}"
        )
        
        return has_permission
    
    def require_permission(self, user_id: int, site_id: int, resource_type: str, 
                          permission: str, error_message: str = None) -> bool:
        """
        Require a specific permission or raise AuthorizationError.
        
        Args:
            user_id: ID of the user
            site_id: ID of the site
            resource_type: Type of resource
            permission: Permission to check
            error_message: Custom error message
            
        Returns:
            True if user has permission, otherwise raises exception
            
        Raises:
            AuthorizationError: If user does not have the required permission
        """
        # Check permission
        if not self.has_permission(user_id, site_id, resource_type, permission):
            # Use default error message if none provided
            if error_message is None:
                error_message = f"You don't have permission to {permission} this {resource_type}"
            
            logger.warning(
                f"Authorization error: User {user_id} tried to {permission} {resource_type} "
                f"in site {site_id} without permission"
            )
            
            raise AuthorizationError(error_message, {
                "user_id": user_id,
                "site_id": site_id,
                "resource_type": resource_type,
                "permission": permission
            })
        
        return True
    
    def can_access_site(self, user_id: int, site_id: int) -> bool:
        """
        Check if user has access to a specific site.
        
        Args:
            user_id: ID of the user
            site_id: ID of the site
            
        Returns:
            True if user has access to the site, False otherwise
        """
        # Get user's role for the site
        role = self.get_user_role_for_site(user_id, site_id)
        
        # If role is not None, user has access
        has_access = role is not None
        
        logger.debug(f"User {user_id} {'' if has_access else 'does not '}have access to site {site_id}")
        
        return has_access
    
    def require_site_access(self, user_id: int, site_id: int, error_message: str = None) -> bool:
        """
        Require site access or raise SiteContextError.
        
        Args:
            user_id: ID of the user
            site_id: ID of the site
            error_message: Custom error message
            
        Returns:
            True if user has site access, otherwise raises exception
            
        Raises:
            SiteContextError: If user does not have access to the site
        """
        # Check site access
        if not self.can_access_site(user_id, site_id):
            # Get user's sites for context
            sites = self._user_repository.get_user_sites(user_id)
            user_site_ids = [site['id'] for site in sites]
            
            # Use default error message if none provided
            if error_message is None:
                error_message = f"You don't have access to site {site_id}"
            
            logger.warning(
                f"Site context error: User {user_id} tried to access site {site_id} "
                f"but only has access to sites {user_site_ids}"
            )
            
            raise SiteContextError(
                error_message,
                user_sites=user_site_ids,
                requested_site=site_id
            )
        
        return True
    
    def can_manage_site_users(self, user_id: int, site_id: int) -> bool:
        """
        Check if user can manage users for a specific site.
        
        Args:
            user_id: ID of the user
            site_id: ID of the site
            
        Returns:
            True if user can manage users for the site, False otherwise
        """
        # Check if user has 'manage_users' permission
        has_permission = self.has_permission(user_id, site_id, 'user', 'manage_users')
        
        logger.debug(
            f"User {user_id} {'' if has_permission else 'cannot '}manage users for site {site_id}"
        )
        
        return has_permission
    
    def can_create_interaction(self, user_id: int, site_id: int) -> bool:
        """
        Check if user can create interactions for a specific site.
        
        Args:
            user_id: ID of the user
            site_id: ID of the site
            
        Returns:
            True if user can create interactions, False otherwise
        """
        # Check if user has 'create' permission for 'interaction' resource
        has_permission = self.has_permission(user_id, site_id, 'interaction', 'create')
        
        logger.debug(
            f"User {user_id} {'' if has_permission else 'cannot '}create interactions for site {site_id}"
        )
        
        return has_permission
    
    def can_edit_interaction(self, user_id: int, site_id: int, interaction_data: dict) -> bool:
        """
        Check if user can edit a specific interaction.
        
        Args:
            user_id: ID of the user
            site_id: ID of the site
            interaction_data: Data of the interaction to edit
            
        Returns:
            True if user can edit the interaction, False otherwise
        """
        # Check if interaction belongs to the specified site
        interaction_site_id = interaction_data.get('site_id')
        if interaction_site_id != site_id:
            logger.warning(
                f"Cross-site access attempt: User {user_id} from site {site_id} "
                f"tried to edit interaction from site {interaction_site_id}"
            )
            return False
        
        # Check if user has 'update' permission for 'interaction' resource
        has_permission = self.has_permission(user_id, site_id, 'interaction', 'update')
        
        logger.debug(
            f"User {user_id} {'' if has_permission else 'cannot '}edit interaction "
            f"{interaction_data.get('id')} in site {site_id}"
        )
        
        return has_permission
    
    def can_delete_interaction(self, user_id: int, site_id: int, interaction_data: dict) -> bool:
        """
        Check if user can delete a specific interaction.
        
        Args:
            user_id: ID of the user
            site_id: ID of the site
            interaction_data: Data of the interaction to delete
            
        Returns:
            True if user can delete the interaction, False otherwise
        """
        # Check if interaction belongs to the specified site
        interaction_site_id = interaction_data.get('site_id')
        if interaction_site_id != site_id:
            logger.warning(
                f"Cross-site access attempt: User {user_id} from site {site_id} "
                f"tried to delete interaction from site {interaction_site_id}"
            )
            return False
        
        # Check if user has 'delete' permission for 'interaction' resource
        has_permission = self.has_permission(user_id, site_id, 'interaction', 'delete')
        
        logger.debug(
            f"User {user_id} {'' if has_permission else 'cannot '}delete interaction "
            f"{interaction_data.get('id')} in site {site_id}"
        )
        
        return has_permission
    
    def has_role(self, user_id: int, site_id: int, required_role: str) -> bool:
        """
        Check if user has a specific role or higher for a site.
        
        Args:
            user_id: ID of the user
            site_id: ID of the site
            required_role: Required role (SITE_ADMIN, EDITOR, VIEWER)
            
        Returns:
            True if user has the required role or higher, False otherwise
        """
        # Get user's role for the site
        user_role = self.get_user_role_for_site(user_id, site_id)
        
        # If user has no access to the site, deny permission
        if user_role is None:
            logger.debug(f"User {user_id} has no access to site {site_id}, role check failed")
            return False
        
        # Use UserRole.has_permission to check role hierarchy
        has_required_role = UserRole.has_permission(user_role, required_role)
        
        logger.debug(
            f"User {user_id} with role '{user_role}' {'' if has_required_role else 'does not '}"
            f"meet required role '{required_role}' for site {site_id}"
        )
        
        return has_required_role