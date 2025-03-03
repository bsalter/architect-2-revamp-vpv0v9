"""
Site model module for the Interaction Management System.

This module defines the Site model representing organizational sites that contain
interactions. The Site entity serves as a boundary for data access control in the
multi-tenant architecture of the system.
"""

from .base import Base
from ..extensions import db
from ..utils.datetime_util import get_utc_datetime

class Site(Base):
    """
    SQLAlchemy model representing an organizational site which serves as a boundary
    for data access control and contains interaction records.
    
    Sites are fundamental to the multi-tenant architecture, separating data between
    different organizational units while allowing users with appropriate permissions
    to access multiple sites.
    """
    
    __tablename__ = 'sites'
    
    # Basic site information
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    
    # Relationships
    # Many-to-many relationship with users through user_sites junction table
    users = db.relationship(
        'User',
        secondary='user_sites',
        backref=db.backref('sites', lazy='dynamic'),
        lazy='dynamic'
    )
    
    # One-to-many relationship with interactions
    interactions = db.relationship(
        'Interaction',
        backref='site',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    
    def __init__(self, name, description=None):
        """
        Initializes a new Site instance with the provided attributes.
        
        Args:
            name (str): The name of the site
            description (str, optional): A description of the site
        """
        super().__init__()
        self.name = name
        self.description = description
    
    def to_dict(self):
        """
        Converts the site model to a dictionary for serialization.
        
        Returns:
            dict: Dictionary representation of the site model
        """
        # Get base dictionary from parent class method
        site_dict = super().to_dict()
        # Return the dictionary with site properties
        return site_dict
    
    def update(self, data):
        """
        Updates the site with new values.
        
        Args:
            data (dict): Dictionary containing updated site values
                - name (str, optional): Updated site name
                - description (str, optional): Updated site description
                
        Returns:
            Site: Updated site instance
        """
        if 'name' in data:
            self.name = data['name']
        if 'description' in data:
            self.description = data['description']
        
        self.update_timestamp()
        return self
    
    def get_users(self):
        """
        Gets all users who have access to this site.
        
        Returns:
            list: List of User objects with access to this site
        """
        return self.users.all()
    
    def get_interactions(self):
        """
        Gets all interactions that belong to this site.
        
        Returns:
            list: List of Interaction objects for this site
        """
        return self.interactions.all()
    
    def get_user_count(self):
        """
        Gets the number of users associated with this site.
        
        Returns:
            int: Count of users with access to this site
        """
        return self.users.count()
    
    def get_interaction_count(self):
        """
        Gets the number of interactions associated with this site.
        
        Returns:
            int: Count of interactions for this site
        """
        return self.interactions.count()