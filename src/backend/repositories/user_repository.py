"""
User repository module for the Interaction Management System.

This module provides the UserRepository class for managing User entity data access operations
with site-scoping and transaction management. It handles all CRUD operations for user accounts,
enforces business rules, and maintains data integrity.
"""

from typing import Dict, List, Optional, Tuple, Any, Union

import sqlalchemy
from sqlalchemy import or_, func

from .base_repository import BaseRepository
from .connection_manager import ConnectionManager
from ..models.user import User, user_site_table
from ..utils.error_util import AuthenticationError, ValidationError, SiteContextError
from ..logging.structured_logger import StructuredLogger

# Configure structured logger
logger = StructuredLogger(__name__)


class UserRepository(BaseRepository):
    """
    Repository for User model providing CRUD operations with site-scoping and transaction management.
    
    This repository implements data access methods for User entities, ensuring site-scoping
    is properly enforced for all operations and providing transaction management for data integrity.
    """
    
    def __init__(self, connection_manager: ConnectionManager = None, site_context_service = None):
        """
        Initialize the user repository with necessary dependencies.
        
        Args:
            connection_manager: Optional connection manager for database operations
            site_context_service: Service providing site context for the current user
        """
        # Initialize base repository with User model
        super().__init__(
            User,
            connection_manager=connection_manager,
            get_current_site_id=None  # Users don't have site_id column, they're associated via M2M
        )
        
        # Store site context service for site-scoping
        self._site_context_service = site_context_service
        
        logger.debug("UserRepository initialized")
    
    def find_by_username(self, username: str) -> Optional[User]:
        """
        Find a user by username.
        
        Args:
            username: Username to search for
            
        Returns:
            User instance if found, None otherwise
        """
        # Create base query for User model
        query = self._session.query(User)
        
        # Filter by username using case-insensitive comparison
        query = query.filter(func.lower(User.username) == func.lower(username))
        
        # Execute query and return first result or None
        result = query.first()
        
        logger.debug(f"User lookup by username: {'found' if result else 'not found'}")
        
        return result
    
    def find_by_email(self, email: str) -> Optional[User]:
        """
        Find a user by email address.
        
        Args:
            email: Email address to search for
            
        Returns:
            User instance if found, None otherwise
        """
        # Create base query for User model
        query = self._session.query(User)
        
        # Filter by email using case-insensitive comparison
        query = query.filter(func.lower(User.email) == func.lower(email))
        
        # Execute query and return first result or None
        result = query.first()
        
        logger.debug(f"User lookup by email: {'found' if result else 'not found'}")
        
        return result
    
    def authenticate(self, username_or_email: str, password: str) -> User:
        """
        Authenticate a user with username/email and password.
        
        Args:
            username_or_email: Username or email address
            password: User's password
            
        Returns:
            Authenticated user or raises AuthenticationError
            
        Raises:
            AuthenticationError: If authentication fails
        """
        # Try to find user by username or email
        user = self.find_by_username(username_or_email)
        if not user:
            user = self.find_by_email(username_or_email)
        
        # If user not found, raise AuthenticationError
        if not user:
            logger.debug("Authentication failed: user not found")
            raise AuthenticationError("Invalid username or password")
        
        # Validate password using User.check_password method
        if not user.check_password(password):
            logger.debug(f"Authentication failed: invalid password for user {user.username}")
            raise AuthenticationError("Invalid username or password")
        
        # Update user's last login timestamp
        user.update_last_login()
        self._session.commit()
        
        logger.info(f"User authenticated successfully: {user.username}")
        
        return user
    
    def create_user(self, user_data: Dict[str, Any], site_ids: List[int] = None) -> User:
        """
        Create a new user with site association.
        
        Args:
            user_data: Dictionary containing user data
            site_ids: List of site IDs to associate the user with
            
        Returns:
            Newly created user instance
            
        Raises:
            ValidationError: If validation fails
            DatabaseError: If database operation fails
        """
        # Validate username and email don't already exist
        existing_username = self.find_by_username(user_data.get('username'))
        if existing_username:
            raise ValidationError("Username already exists", {"username": "Username is already taken"})
        
        existing_email = self.find_by_email(user_data.get('email'))
        if existing_email:
            raise ValidationError("Email already exists", {"email": "Email address is already in use"})
        
        # Validate required fields
        required_fields = ['username', 'email', 'password']
        missing_fields = [field for field in required_fields if field not in user_data]
        if missing_fields:
            raise ValidationError("Missing required fields", {"fields": missing_fields})
        
        # Prepare user data for creation
        username = user_data.get('username')
        email = user_data.get('email')
        password = user_data.get('password')
        
        # Use transaction context for atomic operation
        with self._connection_manager.transaction_context():
            # Create user with required fields
            user = User(username=username, email=email, password=password)
            self._session.add(user)
            self._session.flush()  # Flush to get user ID
            
            # Associate user with provided site IDs
            if site_ids:
                for site_id in site_ids:
                    # Add user-site association with default role ('viewer')
                    stmt = user_site_table.insert().values(
                        user_id=user.id,
                        site_id=site_id,
                        role='viewer'  # Default role
                    )
                    self._session.execute(stmt)
        
        logger.info(f"Created user: {username} with {len(site_ids) if site_ids else 0} site associations")
        
        return user
    
    def update_user(self, user_id: int, user_data: Dict[str, Any]) -> User:
        """
        Update an existing user.
        
        Args:
            user_id: ID of the user to update
            user_data: Dictionary containing updated user data
            
        Returns:
            Updated user instance
            
        Raises:
            ValidationError: If validation fails
            NotFoundError: If user not found
            SiteContextError: If user not in current site context
            DatabaseError: If database operation fails
        """
        # Find user by ID
        user = self.find_by_id(user_id)
        
        # Validate site access if site context service provided
        if self._site_context_service and not self._check_user_site_access(user):
            raise SiteContextError(
                "You don't have access to modify this user",
                user_sites=self._site_context_service.get_current_site_ids(),
                requested_site=None
            )
        
        # Check username uniqueness if updating username
        if 'username' in user_data and user_data['username'] != user.username:
            existing_user = self.find_by_username(user_data['username'])
            if existing_user and existing_user.id != user_id:
                raise ValidationError("Username already exists", {"username": "Username is already taken"})
        
        # Check email uniqueness if updating email
        if 'email' in user_data and user_data['email'] != user.email:
            existing_user = self.find_by_email(user_data['email'])
            if existing_user and existing_user.id != user_id:
                raise ValidationError("Email already exists", {"email": "Email address is already in use"})
        
        # Handle password update if included
        if 'password' in user_data:
            user.set_password(user_data['password'])
            # Remove password from data to avoid double-setting it
            del user_data['password']
        
        # Update user fields
        for key, value in user_data.items():
            if hasattr(user, key) and key not in ['id', 'password_hash', 'created_at']:
                setattr(user, key, value)
        
        # Update timestamp
        user.update_timestamp()
        
        # Commit changes
        self._session.commit()
        
        logger.info(f"Updated user: {user.username} (ID: {user.id})")
        
        return user
    
    def delete_user(self, user_id: int) -> bool:
        """
        Delete a user account.
        
        Args:
            user_id: ID of the user to delete
            
        Returns:
            True if deleted successfully
            
        Raises:
            NotFoundError: If user not found
            SiteContextError: If user not in current site context
            DatabaseError: If database operation fails
        """
        # Find user by ID
        user = self.find_by_id(user_id)
        
        # Validate site access if site context service provided
        if self._site_context_service and not self._check_user_site_access(user):
            raise SiteContextError(
                "You don't have access to delete this user",
                user_sites=self._site_context_service.get_current_site_ids(),
                requested_site=None
            )
        
        # Use transaction context for atomic operation
        with self._connection_manager.transaction_context():
            # Remove user's site associations
            self._session.execute(
                user_site_table.delete().where(user_site_table.c.user_id == user_id)
            )
            
            # Delete user
            self._session.delete(user)
        
        logger.info(f"Deleted user: {user.username} (ID: {user.id})")
        
        return True
    
    def add_user_to_site(self, user_id: int, site_id: int, role: str = 'viewer') -> bool:
        """
        Add a user to a site with specified role.
        
        Args:
            user_id: ID of the user
            site_id: ID of the site to add the user to
            role: Role for the user on this site (default: 'viewer')
            
        Returns:
            True if added successfully
            
        Raises:
            NotFoundError: If user or site not found
            SiteContextError: If current user doesn't have access to the site
            ValidationError: If role is invalid
            DatabaseError: If database operation fails
        """
        # Validate user exists
        user = self.find_by_id(user_id)
        
        # Validate site exists and current user has access to it
        if self._site_context_service:
            if not self._site_context_service.validate_site_access(site_id):
                raise SiteContextError(
                    "You don't have access to this site",
                    user_sites=self._site_context_service.get_current_site_ids(),
                    requested_site=site_id
                )
        
        # Check if user already has access to site
        if user.has_site_access(site_id):
            # Update role if user already has access
            self._session.execute(
                user_site_table.update()
                .where(
                    (user_site_table.c.user_id == user_id) & 
                    (user_site_table.c.site_id == site_id)
                )
                .values(role=role)
            )
        else:
            # Create user-site association with specified role
            self._session.execute(
                user_site_table.insert().values(
                    user_id=user_id,
                    site_id=site_id,
                    role=role
                )
            )
        
        # Commit changes
        self._session.commit()
        
        logger.info(f"Added user {user.username} (ID: {user_id}) to site {site_id} with role '{role}'")
        
        return True
    
    def remove_user_from_site(self, user_id: int, site_id: int) -> bool:
        """
        Remove a user from a site.
        
        Args:
            user_id: ID of the user
            site_id: ID of the site to remove the user from
            
        Returns:
            True if removed successfully
            
        Raises:
            NotFoundError: If user or site not found
            SiteContextError: If current user doesn't have access to the site
            DatabaseError: If database operation fails
        """
        # Validate user exists
        user = self.find_by_id(user_id)
        
        # Validate site exists and current user has access to it
        if self._site_context_service:
            if not self._site_context_service.validate_site_access(site_id):
                raise SiteContextError(
                    "You don't have access to this site",
                    user_sites=self._site_context_service.get_current_site_ids(),
                    requested_site=site_id
                )
        
        # Check if user has access to the site
        if not user.has_site_access(site_id):
            logger.warning(f"User {user.username} does not have access to site {site_id}")
            return False
        
        # Remove user-site association
        self._session.execute(
            user_site_table.delete().where(
                (user_site_table.c.user_id == user_id) & 
                (user_site_table.c.site_id == site_id)
            )
        )
        
        # Commit changes
        self._session.commit()
        
        logger.info(f"Removed user {user.username} (ID: {user_id}) from site {site_id}")
        
        return True
    
    def get_users_for_site(
        self, 
        site_id: int, 
        filters: Dict[str, Any] = None,
        page: int = 1,
        per_page: int = 20,
        sort_by: str = None,
        sort_desc: bool = False
    ) -> Tuple[List[User], int]:
        """
        Get all users associated with a specific site.
        
        Args:
            site_id: ID of the site
            filters: Optional dictionary of filter criteria
            page: Page number to retrieve (1-indexed)
            per_page: Number of items per page
            sort_by: Column name to sort by
            sort_desc: True for descending sort, False for ascending
            
        Returns:
            Tuple containing list of users and total count
            
        Raises:
            SiteContextError: If current user doesn't have access to the site
        """
        # Validate site exists and current user has access to it
        if self._site_context_service:
            if not self._site_context_service.validate_site_access(site_id):
                raise SiteContextError(
                    "You don't have access to this site",
                    user_sites=self._site_context_service.get_current_site_ids(),
                    requested_site=site_id
                )
        
        # Create query for users associated with the site
        query = self._session.query(User).join(
            user_site_table,
            User.id == user_site_table.c.user_id
        ).filter(user_site_table.c.site_id == site_id)
        
        # Apply additional filters if provided
        if filters:
            query = self.apply_filters(query, filters)
        
        # Apply sorting if specified
        if sort_by and hasattr(User, sort_by):
            sort_column = getattr(User, sort_by)
            if sort_desc:
                query = query.order_by(sort_column.desc())
            else:
                query = query.order_by(sort_column.asc())
        else:
            # Default sort by username
            query = query.order_by(User.username)
        
        # Get total count before pagination
        total_count = query.count()
        
        # Apply pagination
        query = query.offset((page - 1) * per_page).limit(per_page)
        
        # Execute query and return results with count
        users = query.all()
        
        logger.debug(f"Retrieved {len(users)} users for site {site_id} (page {page}, total {total_count})")
        
        return users, total_count
    
    def change_user_role(self, user_id: int, site_id: int, new_role: str) -> bool:
        """
        Change a user's role for a specific site.
        
        Args:
            user_id: ID of the user
            site_id: ID of the site
            new_role: New role to assign
            
        Returns:
            True if role updated successfully
            
        Raises:
            NotFoundError: If user not found
            SiteContextError: If current user doesn't have access to the site
            ValidationError: If role is invalid
            DatabaseError: If database operation fails
        """
        # Validate user exists
        user = self.find_by_id(user_id)
        
        # Validate site exists and current user has access to it
        if self._site_context_service:
            if not self._site_context_service.validate_site_access(site_id):
                raise SiteContextError(
                    "You don't have access to this site",
                    user_sites=self._site_context_service.get_current_site_ids(),
                    requested_site=site_id
                )
        
        # Validate the new role is valid
        from ..utils.enums import UserRole
        if not UserRole.is_valid(new_role):
            raise ValidationError(
                "Invalid role", 
                {"role": f"Role must be one of: {', '.join(UserRole.get_values())}"}
            )
        
        # Check if user has access to the site
        if not user.has_site_access(site_id):
            raise ValidationError(
                "User does not have access to this site",
                {"user_id": user_id, "site_id": site_id}
            )
        
        # Update user's role for the site
        self._session.execute(
            user_site_table.update()
            .where(
                (user_site_table.c.user_id == user_id) & 
                (user_site_table.c.site_id == site_id)
            )
            .values(role=new_role)
        )
        
        # Commit changes
        self._session.commit()
        
        logger.info(f"Changed role for user {user.username} (ID: {user_id}) on site {site_id} to '{new_role}'")
        
        return True
    
    def change_password(self, user_id: int, current_password: str, new_password: str) -> bool:
        """
        Change a user's password.
        
        Args:
            user_id: ID of the user
            current_password: Current password for verification
            new_password: New password to set
            
        Returns:
            True if password changed successfully
            
        Raises:
            NotFoundError: If user not found
            AuthenticationError: If current password is incorrect
            ValidationError: If new password doesn't meet requirements
            DatabaseError: If database operation fails
        """
        # Find user by ID
        user = self.find_by_id(user_id)
        
        # Verify current password
        if not user.check_password(current_password):
            raise AuthenticationError("Current password is incorrect")
        
        # Validate new password meets requirements
        if not new_password or len(new_password) < 8:
            raise ValidationError("Password must be at least 8 characters")
        
        # Set new password
        user.set_password(new_password)
        
        # Save changes
        self._session.commit()
        
        logger.info(f"Changed password for user {user.username} (ID: {user_id})")
        
        return True
    
    def reset_password(self, user_id: int, new_password: str) -> bool:
        """
        Reset a user's password (admin function).
        
        Args:
            user_id: ID of the user
            new_password: New password to set
            
        Returns:
            True if password reset successfully
            
        Raises:
            NotFoundError: If user not found
            ValidationError: If new password doesn't meet requirements
            SiteContextError: If user not in current site context
            DatabaseError: If database operation fails
        """
        # Find user by ID
        user = self.find_by_id(user_id)
        
        # Validate site access if site context service provided
        if self._site_context_service and not self._check_user_site_access(user):
            raise SiteContextError(
                "You don't have access to reset this user's password",
                user_sites=self._site_context_service.get_current_site_ids(),
                requested_site=None
            )
        
        # Validate new password meets requirements
        if not new_password or len(new_password) < 8:
            raise ValidationError("Password must be at least 8 characters")
        
        # Set new password
        user.set_password(new_password)
        
        # Save changes
        self._session.commit()
        
        logger.info(f"Reset password for user {user.username} (ID: {user_id})")
        
        return True
    
    def get_user_sites(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Get all sites a user has access to.
        
        Args:
            user_id: ID of the user
            
        Returns:
            List of site objects the user has access to
            
        Raises:
            NotFoundError: If user not found
            SiteContextError: If current user doesn't have access to view this user's sites
        """
        # Find user by ID
        user = self.find_by_id(user_id)
        
        # Check if the current user has permissions to view this user's sites
        if self._site_context_service and not self._check_user_site_access(user):
            raise SiteContextError(
                "You don't have access to view this user's sites",
                user_sites=self._site_context_service.get_current_site_ids(),
                requested_site=None
            )
        
        # Query user-site relationships
        query = self._session.query(
            user_site_table.c.site_id,
            user_site_table.c.role,
            # Join with sites table to get site name
            sqlalchemy.text('sites.name').label('name')
        ).join(
            sqlalchemy.text('sites'),
            user_site_table.c.site_id == sqlalchemy.text('sites.id')
        ).filter(
            user_site_table.c.user_id == user_id
        )
        
        # Execute query
        result = query.all()
        
        # Format sites into list of dictionaries
        sites = []
        for row in result:
            sites.append({
                'id': row.site_id,
                'name': row.name,
                'role': row.role
            })
        
        logger.debug(f"Retrieved {len(sites)} sites for user {user.username} (ID: {user_id})")
        
        return sites
    
    def _check_user_site_access(self, user: User) -> bool:
        """
        Check if the current user has access to the specified user through site association.
        
        Args:
            user: User to check access for
            
        Returns:
            True if current user has access to the user, False otherwise
        """
        if not self._site_context_service:
            return True
        
        # Get current user's site IDs
        current_site_ids = self._site_context_service.get_current_site_ids()
        
        # Get target user's site IDs
        user_site_ids = user.get_site_ids()
        
        # Check if there's any overlap between site IDs
        return any(site_id in user_site_ids for site_id in current_site_ids)