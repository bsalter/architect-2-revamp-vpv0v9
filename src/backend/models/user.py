"""
User model module for the Interaction Management System.

This module defines the User model which represents user accounts in the application,
including authentication information, profile data, and relationships to sites
through the UserSite association.
"""

from werkzeug.security import generate_password_hash, check_password_hash  # version 2.3.6
from datetime import datetime

from .base import Base
from ..extensions import db
from ..utils.datetime_util import get_utc_datetime
from ..utils.enums import UserRole

# Association table for many-to-many relationship between users and sites
user_site_table = db.Table(
    'user_sites',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('site_id', db.Integer, db.ForeignKey('sites.id'), primary_key=True),
    db.Column('role', db.String(20), nullable=False, default=UserRole.VIEWER.value)
)

class User(Base):
    """
    SQLAlchemy model representing a user account with authentication and profile information.
    """
    __tablename__ = 'users'
    
    # Identity and profile fields
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    last_login = db.Column(db.DateTime)
    
    # Relationships
    sites = db.relationship('Site', secondary=user_site_table, lazy='dynamic')
    interactions = db.relationship('Interaction', foreign_keys='Interaction.created_by', backref='created_by_user', lazy='dynamic')
    
    def __init__(self, username, email, password):
        """
        Initializes a new User instance.
        
        Args:
            username (str): Unique username for the user
            email (str): Email address of the user
            password (str): User's password (will be hashed)
        """
        super().__init__()
        self.username = username
        self.email = email
        self.set_password(password)
        self.last_login = None
    
    def to_dict(self):
        """
        Converts the user model to a dictionary for serialization.
        
        Returns:
            dict: Dictionary representation of the user model
        """
        data = super().to_dict()
        # Exclude password hash for security
        if 'password_hash' in data:
            del data['password_hash']
        return data
    
    def set_password(self, password):
        """
        Sets a hashed password for the user.
        
        Args:
            password (str): Plain text password to hash
        """
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """
        Verifies if the provided password matches the stored hash.
        
        Args:
            password (str): Password to verify
            
        Returns:
            bool: True if password matches, False otherwise
        """
        return check_password_hash(self.password_hash, password)
    
    def update_last_login(self):
        """
        Updates the last login timestamp to the current time.
        """
        self.last_login = get_utc_datetime(datetime.utcnow())
    
    def get_sites(self):
        """
        Gets all sites the user has access to.
        
        Returns:
            list: List of Site objects the user has access to
        """
        return self.sites
    
    def get_site_ids(self):
        """
        Gets IDs of all sites the user has access to.
        
        Returns:
            list: List of site IDs
        """
        return [site.id for site in self.sites]
    
    def has_site_access(self, site_id):
        """
        Checks if the user has access to a specific site.
        
        Args:
            site_id (int): ID of the site to check
            
        Returns:
            bool: True if user has access to the site, False otherwise
        """
        return site_id in self.get_site_ids()
    
    def get_role_for_site(self, site_id):
        """
        Gets the user's role for a specific site.
        
        Args:
            site_id (int): ID of the site to check
            
        Returns:
            str: Role name or None if no access
        """
        # Query the association table to get the role
        user_site = db.session.query(user_site_table).filter_by(
            user_id=self.id, site_id=site_id
        ).first()
        
        return user_site.role if user_site else None
    
    def has_role(self, site_id, required_role):
        """
        Checks if the user has a specific role or higher for a site.
        
        Args:
            site_id (int): ID of the site to check
            required_role (str): Role required for the operation
            
        Returns:
            bool: True if user has required role or higher, False otherwise
        """
        user_role = self.get_role_for_site(site_id)
        if not user_role:
            return False
            
        return UserRole.has_permission(user_role, required_role)
    
    def is_site_admin(self, site_id):
        """
        Checks if the user is an admin for a specific site.
        
        Args:
            site_id (int): ID of the site to check
            
        Returns:
            bool: True if user is a site admin, False otherwise
        """
        return self.has_role(site_id, UserRole.SITE_ADMIN)
    
    def is_editor(self, site_id):
        """
        Checks if the user is an editor or higher for a specific site.
        
        Args:
            site_id (int): ID of the site to check
            
        Returns:
            bool: True if user is an editor or admin, False otherwise
        """
        return self.has_role(site_id, UserRole.EDITOR)
    
    def is_viewer(self, site_id):
        """
        Checks if the user has at least viewer access to a specific site.
        
        Args:
            site_id (int): ID of the site to check
            
        Returns:
            bool: True if user has any role for the site, False otherwise
        """
        return self.has_role(site_id, UserRole.VIEWER)