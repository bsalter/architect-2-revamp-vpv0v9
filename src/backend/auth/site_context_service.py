"""
Service responsible for managing site context throughout the application lifecycle.

This module provides the SiteContext class and SiteContextService for handling
site-scoped data access control. It ensures users can only access interactions
and other data from sites they have permission to access, implementing a key part
of the multi-tenant architecture.
"""

from flask import g
from typing import Dict, List, Optional, Any, Union
from functools import wraps

from .user_context_service import UserContextService
from ..repositories.site_repository import SiteRepository
from ..models.site import Site
from ..utils.error_util import SiteContextError
from ..logging.structured_logger import StructuredLogger
from ..cache.cache_keys import get_site_context_key
from ..cache.cache_service import get_cache_service

# Initialize logger
logger = StructuredLogger(__name__)


class SiteContext:
    """Class representing the current site context information"""
    
    def __init__(self, site_id: int, site_name: str, is_default: bool = False):
        """
        Initialize site context with site information
        
        Args:
            site_id: ID of the current site
            site_name: Name of the current site
            is_default: Whether this is the default site context
        """
        self.site_id = site_id
        self.site_name = site_name
        self.is_default = is_default
        logger.debug(f"Created site context for site {site_name} (ID: {site_id}, default: {is_default})")
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the site context to a dictionary for serialization
        
        Returns:
            Dictionary representation of site context
        """
        return {
            'site_id': self.site_id,
            'site_name': self.site_name,
            'is_default': self.is_default
        }


class SiteContextService:
    """Service responsible for managing site context throughout the application"""
    
    def __init__(self, user_context_service: UserContextService, site_repository: SiteRepository):
        """
        Initialize the site context service with required dependencies
        
        Args:
            user_context_service: Service for accessing user context information
            site_repository: Repository for retrieving site information
        """
        self._user_context_service = user_context_service
        self._site_repository = site_repository
        self._cache_service = get_cache_service()
        logger.info("SiteContextService initialized")
    
    def get_current_site_context(self) -> Optional[SiteContext]:
        """
        Get the current site context from Flask request context
        
        Returns:
            Current site context or None if not set
        """
        if hasattr(g, 'site_id') and g.site_id:
            site_context = SiteContext(
                site_id=g.site_id,
                site_name=g.site_name,
                is_default=g.is_default if hasattr(g, 'is_default') else False
            )
            logger.debug(f"Retrieved site context for site {g.site_name} (ID: {g.site_id})")
            return site_context
        
        logger.debug("No site context found in request")
        return None
    
    def set_site_context(self, site_id: int) -> SiteContext:
        """
        Set site context with a specific site ID
        
        Args:
            site_id: ID of the site to set as current context
            
        Returns:
            Created site context object
            
        Raises:
            SiteContextError: If user doesn't have access to the site
        """
        # Verify user is authenticated
        self._user_context_service.require_authentication()
        
        # Verify user has access to the site
        if not self._user_context_service.has_site_access(site_id):
            user_id = self._user_context_service.get_current_user_id()
            error_msg = f"User {user_id} does not have access to site {site_id}"
            logger.warning(error_msg)
            raise SiteContextError(error_msg)
        
        # Get site information
        site = self._site_repository.find_by_id(site_id)
        if not site:
            error_msg = f"Site with ID {site_id} not found"
            logger.error(error_msg)
            raise SiteContextError(error_msg)
        
        # Create site context
        site_context = SiteContext(
            site_id=site.id,
            site_name=site.name,
            is_default=False
        )
        
        # Store in Flask g object
        g.site_id = site.id
        g.site_name = site.name
        g.is_default = False
        
        # Cache site context
        user_id = self._user_context_service.get_current_user_id()
        if user_id:
            cache_key = get_site_context_key(user_id)
            self._cache_service.set(cache_key, site_context.to_dict())
        
        logger.info(f"Set site context to site {site.name} (ID: {site.id})")
        return site_context
    
    def set_default_site_context(self) -> Optional[SiteContext]:
        """
        Set site context to the user's default site or first available site
        
        Returns:
            Created site context object or None if no sites available
            
        Raises:
            SiteContextError: If user is not authenticated
        """
        # Verify user is authenticated
        self._user_context_service.require_authentication()
        
        # Get user's available sites
        user_id = self._user_context_service.get_current_user_id()
        site_ids = self._user_context_service.get_current_user_site_ids()
        
        if not site_ids:
            logger.warning(f"User {user_id} has no site access")
            return None
        
        # Get default site or first available site
        # For now, we'll use the first available site
        site_id = site_ids[0]
        
        # Get site information
        site = self._site_repository.find_by_id(site_id)
        if not site:
            error_msg = f"Site with ID {site_id} not found"
            logger.error(error_msg)
            raise SiteContextError(error_msg)
        
        # Create site context
        site_context = SiteContext(
            site_id=site.id,
            site_name=site.name,
            is_default=True
        )
        
        # Store in Flask g object
        g.site_id = site.id
        g.site_name = site.name
        g.is_default = True
        
        # Cache site context
        cache_key = get_site_context_key(user_id)
        self._cache_service.set(cache_key, site_context.to_dict())
        
        logger.info(f"Set default site context to site {site.name} (ID: {site.id})")
        return site_context
    
    def clear_site_context(self) -> None:
        """
        Clear site context from Flask request context
        """
        if hasattr(g, 'site_id'):
            logger.info(f"Clearing site context for site {g.site_name} (ID: {g.site_id})")
            for attr in ['site_id', 'site_name', 'is_default']:
                if hasattr(g, attr):
                    delattr(g, attr)
    
    def get_current_site_id(self) -> Optional[int]:
        """
        Get the ID of the current active site
        
        Returns:
            Current site ID or None if no site context
        """
        context = self.get_current_site_context()
        if context:
            logger.debug(f"Retrieved current site ID: {context.site_id}")
            return context.site_id
        
        logger.debug("No active site context")
        return None
    
    def get_current_site(self) -> Optional[Site]:
        """
        Get the current site model from the database
        
        Returns:
            Current site model or None if no site context
        """
        site_id = self.get_current_site_id()
        if not site_id:
            logger.debug("Cannot get current site - no site ID in context")
            return None
        
        site = self._site_repository.find_by_id(site_id)
        if site:
            logger.debug(f"Retrieved current site: {site.name} (ID: {site_id})")
        else:
            logger.warning(f"Site with ID {site_id} not found despite being in context")
        
        return site
    
    def verify_site_access(self, site_id: int) -> bool:
        """
        Verify that current user has access to a specific site
        
        Args:
            site_id: ID of the site to check access for
            
        Returns:
            True if user has access to the site
            
        Raises:
            SiteContextError: If user doesn't have access to the site
        """
        if not self._user_context_service.has_site_access(site_id):
            user_id = self._user_context_service.get_current_user_id()
            error_msg = f"User {user_id} does not have access to site {site_id}"
            logger.warning(error_msg)
            raise SiteContextError(error_msg)
        
        logger.debug(f"Verified site access for site ID: {site_id}")
        return True
    
    def get_available_sites(self) -> List[Dict[str, Any]]:
        """
        Get all sites available to the current user
        
        Returns:
            List of site information dictionaries with ID, name, and role
        """
        user_id = self._user_context_service.get_current_user_id()
        if not user_id:
            logger.debug("Cannot get available sites - user not authenticated")
            return []
        
        sites = self._site_repository.get_sites_for_user(user_id)
        logger.debug(f"Retrieved {len(sites)} available sites for user {user_id}")
        return sites
    
    def requires_site_context(self, func):
        """
        Decorator to require valid site context for a function
        
        Args:
            func: Function to wrap with site context verification
            
        Returns:
            Wrapped function that verifies site context
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not self.get_current_site_context():
                logger.warning("Function requires site context but none is set")
                raise SiteContextError("Site context required for this operation")
            
            logger.debug("Site context verified for function call")
            return func(*args, **kwargs)
        
        return wrapper
    
    def switch_site_context(self, site_id: int) -> SiteContext:
        """
        Switch the current site context to a different site
        
        Args:
            site_id: ID of the site to switch to
            
        Returns:
            New site context after switching
            
        Raises:
            SiteContextError: If user doesn't have access to the site
        """
        # Clear existing site context
        self.clear_site_context()
        
        # Set new site context
        new_context = self.set_site_context(site_id)
        
        logger.info(f"Switched site context to site {new_context.site_name} (ID: {new_context.site_id})")
        return new_context