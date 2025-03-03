"""
Base model module for the Interaction Management System.

This module defines the Base model class that all other database models inherit from,
providing common attributes and functionality like primary key, timestamps, and serialization methods.
"""

from datetime import datetime
from sqlalchemy.ext.declarative import declarative_base  # version 2.0.19

from ..extensions import db
from ..utils.datetime_util import get_utc_datetime

# Create a SQLAlchemy declarative base for models
Base = declarative_base()

class BaseModel(db.Model):
    """
    Base model class that all other models inherit from to ensure consistent structure and functionality.
    
    Provides common attributes and methods including:
    - Primary key (id)
    - Creation and update timestamps
    - Serialization method (to_dict)
    - Timestamp updating method
    """
    
    __abstract__ = True
    
    # Primary key present in all models
    id = db.Column(db.Integer, primary_key=True)
    
    # Timestamps for audit purposes
    created_at = db.Column(db.DateTime, nullable=False)
    updated_at = db.Column(db.DateTime, nullable=False)
    
    def __init__(self, **kwargs):
        """
        Initializes a new model instance with default timestamps.
        """
        super().__init__(**kwargs)
        
        # Set timestamps to current UTC time if not provided
        if not self.created_at:
            self.created_at = get_utc_datetime(datetime.utcnow())
        if not self.updated_at:
            self.updated_at = get_utc_datetime(datetime.utcnow())
    
    def to_dict(self):
        """
        Converts the model instance to a dictionary for serialization.
        
        Returns:
            dict: Dictionary representation of the model
        """
        result = {}
        
        # Add all column attributes to the dictionary
        for column in self.__table__.columns:
            attribute = getattr(self, column.name)
            
            # Format datetime fields as ISO format strings
            if isinstance(attribute, datetime):
                result[column.name] = attribute.isoformat()
            else:
                result[column.name] = attribute
                
        return result
    
    def update_timestamp(self):
        """
        Updates the updated_at timestamp to the current time.
        """
        self.updated_at = get_utc_datetime(datetime.utcnow())