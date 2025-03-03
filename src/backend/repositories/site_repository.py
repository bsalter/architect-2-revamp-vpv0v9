"""
Repository for the Site entity that provides data access operations with transaction management.
Handles CRUD operations for site records and manages relationships between sites, users, and interactions.
"""

from typing import List, Dict, Any, Tuple, Optional
import sqlalchemy
from sqlalchemy import func, or_

from .base_repository import BaseRepository
from ../models/site import Site
from ../models/user_site import UserSite
from .connection_manager import ConnectionManager
from ../utils/error_util import ValidationError, SiteContextError, NotFoundError
from ../logging/structured_logger import StructuredLogger

# Initialize logger
logger = StructuredLogger(__name__)

class SiteRepository(BaseRepository):
    """
    Repository for Site model providing CRUD operations with transaction management 
    and user-site relationship management.
    """
    
    _user_context_service = None
    
    def __init__(self, connection_manager=None, user_context_service=None):
        """
        Initialize the site repository with necessary dependencies.
        
        Args:
            connection_manager: Optional ConnectionManager for database transactions
            user_context_service: Optional service for user context and authorization
        """
        # Initialize base repository with Site model
        super().__init__(Site, connection_manager=connection_manager)
        # Store user_context_service for access control
        self._user_context_service = user_context_service
        logger.info("SiteRepository initialized")
    
    def find_by_name(self, name: str) -> Optional[Site]:
        """
        Find a site by name.
        
        Args:
            name: The name of the site to find
            
        Returns:
            Site: Site instance if found, None otherwise
        """
        # Create base query for Site model
        query = self.get_session().query(Site)
        
        # Filter by name using case-insensitive comparison
        site = query.filter(func.lower(Site.name) == func.lower(name)).first()
        
        if site:
            logger.debug(f"Found site with name: {name}")
        else:
            logger.debug(f"No site found with name: {name}")
            
        return site
    
    def create_site(self, site_data: Dict[str, Any], creator_user_id: int) -> Site:
        """
        Create a new site with initial user association.
        
        Args:
            site_data: Dictionary containing site information
            creator_user_id: User ID of the creator who will be associated as admin
            
        Returns:
            Site: Newly created site instance
            
        Raises:
            ValidationError: If site data is invalid or name already exists
        """
        # Check if site with same name already exists
        if 'name' in site_data and self.find_by_name(site_data['name']):
            error_msg = f"Site with name '{site_data['name']}' already exists"
            logger.error(error_msg)
            raise ValidationError(error_msg, {'name': 'Site name must be unique'})
        
        # Validate required fields
        if 'name' not in site_data or not site_data['name']:
            error_msg = "Site name is required"
            logger.error(error_msg)
            raise ValidationError(error_msg, {'name': 'Site name is required'})
        
        # Start transaction
        with self._connection_manager.transaction_context():
            # Create site using base repository create method
            # First prepare site data for creation
            site_create_data = {
                'name': site_data['name'],
                'description': site_data.get('description')
            }
            
            # Create the site
            site = self.create(site_create_data)
            
            # Create user-site association for creator as admin
            user_site = UserSite(
                user_id=creator_user_id,
                site_id=site.id,
                role='admin'  # Creator gets admin role
            )
            
            self.get_session().add(user_site)
        
        logger.info(f"Created site '{site.name}' (ID: {site.id}) with creator user ID: {creator_user_id}")
        return site
    
    def update_site(self, site_id: int, site_data: Dict[str, Any]) -> Site:
        """
        Update an existing site.
        
        Args:
            site_id: ID of the site to update
            site_data: Dictionary containing updated site information
            
        Returns:
            Site: Updated site instance
            
        Raises:
            NotFoundError: If site doesn't exist
            ValidationError: If site data is invalid
            SiteContextError: If current user doesn't have access to the site
        """
        # Get the site by ID (raises NotFoundError if not found)
        site = self.find_by_id(site_id)
        
        # Verify user has access to this site if user_context_service is available
        if self._user_context_service:
            current_user_id = self._user_context_service.get_current_user_id()
            if not self.user_has_site_access(current_user_id, site_id):
                error_msg = f"User {current_user_id} does not have access to site {site_id}"
                logger.error(error_msg)
                raise SiteContextError(error_msg)
        
        # Check if name is being updated and if it would conflict with an existing site
        if 'name' in site_data and site_data['name'] != site.name:
            existing_site = self.find_by_name(site_data['name'])
            if existing_site and existing_site.id != site_id:
                error_msg = f"Site with name '{site_data['name']}' already exists"
                logger.error(error_msg)
                raise ValidationError(error_msg, {'name': 'Site name must be unique'})
        
        # Update the site using BaseRepository.update
        updated_site = self.update(site_id, site_data)
        
        logger.info(f"Updated site ID: {site_id}")
        return updated_site
    
    def delete_site(self, site_id: int) -> bool:
        """
        Delete a site and all its associations.
        
        Args:
            site_id: ID of the site to delete
            
        Returns:
            bool: True if deleted successfully
            
        Raises:
            NotFoundError: If site doesn't exist
            SiteContextError: If current user doesn't have access to the site
        """
        # Get the site by ID (raises NotFoundError if not found)
        site = self.find_by_id(site_id)
        
        # Verify user has access to this site if user_context_service is available
        if self._user_context_service:
            current_user_id = self._user_context_service.get_current_user_id()
            if not self.user_has_site_access(current_user_id, site_id):
                error_msg = f"User {current_user_id} does not have access to site {site_id}"
                logger.error(error_msg)
                raise SiteContextError(error_msg)
        
        # Start transaction for atomic deletion
        with self._connection_manager.transaction_context():
            session = self.get_session()
            
            # Delete all user-site associations first
            session.query(UserSite).filter(UserSite.site_id == site_id).delete()
            
            # The interactions will be automatically deleted due to the cascade="all, delete-orphan" setting
            # in the relationship definition in the Site model
            
            # Delete the site itself using BaseRepository.delete
            self.delete(site_id)
        
        logger.info(f"Deleted site ID: {site_id}")
        return True
    
    def get_sites_for_user(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Get all sites a user has access to.
        
        Args:
            user_id: ID of the user
            
        Returns:
            List[Dict]: List of site objects with access role information
        """
        # Create query joining Site and UserSite
        query = self.get_session().query(
            Site, UserSite.role
        ).join(
            UserSite, UserSite.site_id == Site.id
        ).filter(
            UserSite.user_id == user_id
        )
        
        # Execute query
        results = query.all()
        
        # Format results as list of dictionaries with role information
        sites_with_roles = []
        for site, role in results:
            site_dict = site.to_dict()
            site_dict['role'] = role
            sites_with_roles.append(site_dict)
        
        logger.debug(f"Retrieved {len(sites_with_roles)} sites for user ID: {user_id}")
        return sites_with_roles
    
    def get_users_for_site(self, site_id: int, filters: Dict[str, Any] = None,
                          page: int = 1, per_page: int = 20) -> Tuple[List[Dict[str, Any]], int]:
        """
        Get all users associated with a site.
        
        Args:
            site_id: ID of the site
            filters: Optional filters to apply (e.g., role)
            page: Page number for pagination
            per_page: Number of results per page
            
        Returns:
            Tuple[List[Dict], int]: List of user info dicts and total count
            
        Raises:
            NotFoundError: If site doesn't exist
            SiteContextError: If current user doesn't have access to the site
        """
        # Get the site by ID (raises NotFoundError if not found)
        site = self.find_by_id(site_id)
        
        # Verify user has access to this site if user_context_service is available
        if self._user_context_service:
            current_user_id = self._user_context_service.get_current_user_id()
            if not self.user_has_site_access(current_user_id, site_id):
                error_msg = f"User {current_user_id} does not have access to site {site_id}"
                logger.error(error_msg)
                raise SiteContextError(error_msg)
        
        # Create query joining User and UserSite
        User = self.get_session().query(Site).get(site_id).users.entity
        
        query = self.get_session().query(
            User, UserSite.role
        ).join(
            UserSite, UserSite.user_id == User.id
        ).filter(
            UserSite.site_id == site_id
        )
        
        # Apply additional filters if provided
        if filters:
            if 'role' in filters:
                query = query.filter(UserSite.role == filters['role'])
            
            # Add additional filters as needed
        
        # Get total count before pagination
        total_count = query.count()
        
        # Apply pagination
        query = query.offset((page - 1) * per_page).limit(per_page)
        
        # Execute query
        results = query.all()
        
        # Format results as list of dictionaries with role information
        users_with_roles = []
        for user, role in results:
            user_dict = user.to_dict()
            user_dict['role'] = role
            users_with_roles.append(user_dict)
        
        logger.debug(f"Retrieved {len(users_with_roles)} users for site ID: {site_id}")
        return users_with_roles, total_count
    
    def user_has_site_access(self, user_id: int, site_id: int) -> bool:
        """
        Check if a user has access to a specific site.
        
        Args:
            user_id: ID of the user
            site_id: ID of the site
            
        Returns:
            bool: True if user has access, False otherwise
        """
        # Create query to check for user-site association
        query = self.get_session().query(UserSite).filter(
            UserSite.user_id == user_id,
            UserSite.site_id == site_id
        )
        
        # Check if any records exist
        has_access = query.count() > 0
        
        logger.debug(f"User {user_id} access to site {site_id}: {has_access}")
        return has_access
    
    def get_user_role_for_site(self, user_id: int, site_id: int) -> Optional[str]:
        """
        Get a user's role for a specific site.
        
        Args:
            user_id: ID of the user
            site_id: ID of the site
            
        Returns:
            str: Role string or None if no access
        """
        # Create query to get user's role for site
        query = self.get_session().query(UserSite).filter(
            UserSite.user_id == user_id,
            UserSite.site_id == site_id
        )
        
        # Get first record
        user_site = query.first()
        
        role = user_site.role if user_site else None
        
        logger.debug(f"User {user_id} role for site {site_id}: {role}")
        return role
    
    def get_site_stats(self, site_id: int) -> Dict[str, Any]:
        """
        Get statistics for a site (user count, interaction count).
        
        Args:
            site_id: ID of the site
            
        Returns:
            Dict: Dictionary with site statistics
            
        Raises:
            NotFoundError: If site doesn't exist
            SiteContextError: If current user doesn't have access to the site
        """
        # Get the site by ID (raises NotFoundError if not found)
        site = self.find_by_id(site_id)
        
        # Verify user has access to this site if user_context_service is available
        if self._user_context_service:
            current_user_id = self._user_context_service.get_current_user_id()
            if not self.user_has_site_access(current_user_id, site_id):
                error_msg = f"User {current_user_id} does not have access to site {site_id}"
                logger.error(error_msg)
                raise SiteContextError(error_msg)
        
        # Get user count
        user_count = site.get_user_count()
        
        # Get interaction count
        interaction_count = site.get_interaction_count()
        
        # Format results
        stats = {
            'site_id': site_id,
            'name': site.name,
            'user_count': user_count,
            'interaction_count': interaction_count,
            'created_at': site.created_at.isoformat() if hasattr(site, 'created_at') else None,
            'updated_at': site.updated_at.isoformat() if hasattr(site, 'updated_at') else None
        }
        
        logger.debug(f"Retrieved stats for site ID: {site_id}")
        return stats
    
    def search_sites(self, search_term: str, page: int = 1, per_page: int = 20) -> Tuple[List[Site], int]:
        """
        Search sites by name or description.
        
        Args:
            search_term: Search term to look for in name or description
            page: Page number for pagination
            per_page: Number of results per page
            
        Returns:
            Tuple[List[Site], int]: List of sites and total count
        """
        # Create base query for sites user has access to
        query = self.get_query()
        
        # If user_context_service is available, restrict to sites the user can access
        if self._user_context_service:
            current_user_id = self._user_context_service.get_current_user_id()
            site_ids = [site['id'] for site in self.get_sites_for_user(current_user_id)]
            
            query = query.filter(Site.id.in_(site_ids))
        
        # Add search filter for name or description
        if search_term:
            search_filter = or_(
                Site.name.ilike(f'%{search_term}%'),
                Site.description.ilike(f'%{search_term}%')
            )
            query = query.filter(search_filter)
        
        # Get total count before pagination
        total_count = query.count()
        
        # Apply pagination
        query = query.offset((page - 1) * per_page).limit(per_page)
        
        # Execute query
        results = query.all()
        
        logger.debug(f"Search for '{search_term}' returned {len(results)} sites")
        return results, total_count