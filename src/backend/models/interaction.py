"""
Interaction model module for the Interaction Management System.

This module defines the Interaction model representing interaction records that track
various forms of communication (meetings, calls, emails) within the system. Each interaction
belongs to a site and includes metadata about the interaction such as title, type,
participants, dates, location, and notes.
"""

from datetime import datetime

from .base import BaseModel
from ..extensions import db
from ..utils.enums import InteractionType, Timezone
from ..utils.datetime_util import validate_datetime_range, get_utc_datetime


class Interaction(BaseModel):
    """
    SQLAlchemy model representing an interaction record containing information about
    meetings, calls, emails, or other types of communication events.
    """

    __tablename__ = 'interactions'

    # Foreign key to Site model
    site_id = db.Column(db.Integer, db.ForeignKey('sites.id'), nullable=False)
    
    # Basic interaction information
    title = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(50), nullable=False)
    lead = db.Column(db.String(100), nullable=False)
    
    # Date and time information
    start_datetime = db.Column(db.DateTime, nullable=False)
    end_datetime = db.Column(db.DateTime, nullable=False)
    timezone = db.Column(db.String(50), nullable=False)
    
    # Optional fields
    location = db.Column(db.String(200), nullable=True)
    description = db.Column(db.Text, nullable=False)
    notes = db.Column(db.Text, nullable=True)
    
    # Creator information
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Add constraint to ensure end datetime is after start datetime
    __table_args__ = (
        db.CheckConstraint('end_datetime > start_datetime', name='valid_datetime_range'),
    )

    def __init__(self, site_id, title, type, lead, start_datetime, end_datetime, timezone, 
                 created_by, location=None, description=None, notes=None):
        """
        Initializes a new Interaction instance with the provided attributes.
        
        Args:
            site_id (int): ID of the site the interaction belongs to
            title (str): Title of the interaction
            type (str): Type of interaction (must be a valid InteractionType)
            lead (str): Person leading the interaction
            start_datetime (datetime): Start date and time
            end_datetime (datetime): End date and time
            timezone (str): Timezone identifier
            created_by (int): ID of the user creating the interaction
            location (str, optional): Location of the interaction
            description (str, optional): Detailed description
            notes (str, optional): Additional notes
        """
        # Validate required fields
        if site_id is None:
            raise ValueError("Site ID is required")
        
        if not title or not isinstance(title, str):
            raise ValueError("Title is required and must be a string")
        
        if not InteractionType.is_valid(type):
            raise ValueError(f"Invalid interaction type. Must be one of: {', '.join(InteractionType.get_values())}")
        
        if not lead or not isinstance(lead, str):
            raise ValueError("Lead is required and must be a string")
        
        if not isinstance(start_datetime, datetime) or not isinstance(end_datetime, datetime):
            raise ValueError("Start and end dates must be datetime objects")
        
        if not validate_datetime_range(start_datetime, end_datetime):
            raise ValueError("End datetime must be after start datetime")
        
        if not timezone or not Timezone.is_valid(timezone):
            raise ValueError("Valid timezone identifier is required")
        
        if created_by is None:
            raise ValueError("Created by user ID is required")
        
        # Set instance attributes
        self.site_id = site_id
        self.title = title
        self.type = type
        self.lead = lead
        self.start_datetime = start_datetime
        self.end_datetime = end_datetime
        self.timezone = timezone
        self.created_by = created_by
        self.location = location or ""
        self.description = description or ""
        self.notes = notes or ""
        
        # Call parent constructor for common fields (id, timestamps)
        super().__init__()

    def to_dict(self):
        """
        Converts the interaction model to a dictionary for serialization.
        
        Returns:
            dict: Dictionary representation of the interaction model
        """
        # Get base dictionary from parent class method
        result = super().to_dict()
        
        # No need to manually format datetime fields as the parent method already does this
        # Add any additional processing specific to Interaction if needed
        
        return result

    def update(self, data):
        """
        Updates the interaction with new values.
        
        Args:
            data (dict): Dictionary containing fields to update
            
        Returns:
            Interaction: Updated interaction instance
        """
        if 'title' in data and data['title']:
            self.title = data['title']
        
        if 'type' in data and data['type']:
            if not InteractionType.is_valid(data['type']):
                raise ValueError(f"Invalid interaction type. Must be one of: {', '.join(InteractionType.get_values())}")
            self.type = data['type']
        
        if 'lead' in data and data['lead']:
            self.lead = data['lead']
        
        if 'start_datetime' in data and data['start_datetime']:
            self.start_datetime = data['start_datetime']
        
        if 'end_datetime' in data and data['end_datetime']:
            self.end_datetime = data['end_datetime']
        
        # Validate datetime range if both start and end are updated
        if ('start_datetime' in data or 'end_datetime' in data) and not validate_datetime_range(self.start_datetime, self.end_datetime):
            raise ValueError("End datetime must be after start datetime")
        
        if 'timezone' in data and data['timezone']:
            if not Timezone.is_valid(data['timezone']):
                raise ValueError("Invalid timezone identifier")
            self.timezone = data['timezone']
        
        if 'location' in data:
            self.location = data['location'] if data['location'] else ""
        
        if 'description' in data and data['description']:
            self.description = data['description']
        
        if 'notes' in data:
            self.notes = data['notes'] if data['notes'] else ""
        
        # Update the timestamp
        self.update_timestamp()
        
        return self

    def validate(self):
        """
        Validates the interaction data for consistency and business rules.
        
        Returns:
            tuple: (bool, str) - Success flag and error message if any
        """
        # Title validation
        if not self.title:
            return False, "Title is required"
        
        # Type validation
        if not InteractionType.is_valid(self.type):
            return False, f"Invalid interaction type. Must be one of: {', '.join(InteractionType.get_values())}"
        
        # Lead validation
        if not self.lead:
            return False, "Lead is required"
        
        # Date/time validation
        if not isinstance(self.start_datetime, datetime) or not isinstance(self.end_datetime, datetime):
            return False, "Start and end dates must be valid datetime objects"
        
        if not validate_datetime_range(self.start_datetime, self.end_datetime):
            return False, "End datetime must be after start datetime"
        
        # Timezone validation
        if not self.timezone or not Timezone.is_valid(self.timezone):
            return False, "Valid timezone identifier is required"
        
        # Description validation
        if not self.description:
            return False, "Description is required"
        
        return True, ""

    def get_duration_minutes(self):
        """
        Calculates the duration of the interaction in minutes.
        
        Returns:
            int: Duration in minutes
        """
        if not self.start_datetime or not self.end_datetime:
            return 0
        
        # Ensure both datetimes are timezone-aware and in the same timezone
        start_utc = get_utc_datetime(self.start_datetime)
        end_utc = get_utc_datetime(self.end_datetime)
        
        if not start_utc or not end_utc:
            return 0
        
        # Calculate duration in minutes
        delta = end_utc - start_utc
        return int(delta.total_seconds() / 60)