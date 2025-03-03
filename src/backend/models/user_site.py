"""
UserSite model module for the Interaction Management System.

This module defines the UserSite model that implements the many-to-many relationship
between users and sites, including role information. This model is central to the 
site-scoped access control system, enabling users to have different roles across 
multiple organizational sites.
"""

from datetime import datetime
from .base import Base
from ..extensions import db
from ..utils.enums import UserRole
from ..utils.datetime_util import get_utc_datetime


class UserSite(Base):
    """
    SQLAlchemy model representing the many-to-many relationship between users and sites, with role information.
    """
    __tablename__ = 'user_sites'
    
    # This is a junction table with a composite primary key
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    site_id = db.Column(db.Integer, db.ForeignKey('sites.id', ondelete='CASCADE'), primary_key=True)
    
    # Role determines the user's permissions at this site
    role = db.Column(db.String(20), nullable=False, default=UserRole.VIEWER.value)
    
    # Add timestamps for tracking creation and updates
    created_at = db.Column(db.DateTime, nullable=False)
    updated_at = db.Column(db.DateTime, nullable=False)
    
    # Add a check constraint for valid roles
    __table_args__ = (
        db.CheckConstraint("role IN ('admin', 'editor', 'viewer')", name='valid_role'),
    )

    def __init__(self, user_id, site_id, role=None):
        """
        Initializes a new UserSite instance with the provided user_id, site_id, and role.
        
        Args:
            user_id (int): The ID of the user
            site_id (int): The ID of the site
            role (str, optional): The role of the user at this site. Defaults to UserRole.VIEWER.value.
        """
        # Initialize base class
        super().__init__()
        
        self.user_id = user_id
        self.site_id = site_id
        
        # Set default role if none provided
        self.role = role if role is not None else UserRole.VIEWER.value
        
        # Validate that the role is valid
        if not UserRole.is_valid(self.role):
            raise ValueError(f"Invalid role: {self.role}. Must be one of: {UserRole.get_values()}")
            
        # Set timestamps to current UTC time
        now = get_utc_datetime(datetime.utcnow())
        self.created_at = now
        self.updated_at = now

    def to_dict(self):
        """
        Converts the user_site model to a dictionary for serialization.
        
        Returns:
            dict: Dictionary representation of the user_site model
        """
        # Get base dictionary from parent class method if it exists
        base_dict = super().to_dict() if hasattr(super(), 'to_dict') else {}
        
        # If base to_dict doesn't exist, create our own
        if not base_dict:
            return {
                'user_id': self.user_id,
                'site_id': self.site_id,
                'role': self.role,
                'created_at': self.created_at.isoformat() if self.created_at else None,
                'updated_at': self.updated_at.isoformat() if self.updated_at else None
            }
        return base_dict

    def update_role(self, new_role):
        """
        Updates the role for this user-site association.
        
        Args:
            new_role (str): The new role to assign
            
        Returns:
            bool: True if role was updated, False if invalid role
        """
        if not UserRole.is_valid(new_role):
            return False
            
        self.role = new_role
        self.update_timestamp()
        return True
        
    def update_timestamp(self):
        """
        Updates the updated_at timestamp to the current time.
        """
        self.updated_at = get_utc_datetime(datetime.utcnow())