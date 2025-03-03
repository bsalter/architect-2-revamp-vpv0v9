"""
Interaction History Model Module

This module defines the InteractionHistory model which tracks changes to Interaction records.
It provides an audit trail for all create, update, and delete operations on interactions,
storing who made the change, when, and what the before and after states were.
"""

import json
from sqlalchemy.types import JSONB  # version 2.0.19

from .base import BaseModel
from ..extensions import db
from ..utils.datetime_util import get_utc_datetime

# Constants for change types
CHANGE_TYPE_CREATE = 'create'
CHANGE_TYPE_UPDATE = 'update'
CHANGE_TYPE_DELETE = 'delete'


class InteractionHistory(BaseModel):
    """
    SQLAlchemy model that tracks historical changes to Interaction records for auditing purposes.
    
    This model maintains a complete audit trail of all changes to interactions, including
    who made the change, when it was made, what type of change it was, and the before and
    after states of the interaction record. This enables detailed auditing and potentially
    restoration of previous states if needed.
    """
    
    __tablename__ = 'interaction_history'
    
    # Foreign key to the interaction being modified
    interaction_id = db.Column(db.Integer, db.ForeignKey('interaction.id', ondelete='CASCADE'), nullable=False)
    
    # User ID of who made the change
    changed_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Type of change (create, update, delete)
    change_type = db.Column(db.String(20), nullable=False)
    
    # JSON representation of the interaction before change
    # Null for create operations
    before_state = db.Column(JSONB, nullable=True)
    
    # JSON representation of the interaction after change
    # Null for delete operations
    after_state = db.Column(JSONB, nullable=True)
    
    def __init__(self, interaction_id, changed_by, change_type, before_state=None, after_state=None):
        """
        Initializes a new InteractionHistory instance.
        
        Args:
            interaction_id (int): ID of the interaction being changed
            changed_by (int): ID of the user making the change
            change_type (str): Type of change (create, update, delete)
            before_state (dict, optional): State of the interaction before the change
            after_state (dict, optional): State of the interaction after the change
        """
        if interaction_id is None:
            raise ValueError("interaction_id cannot be None")
        
        if changed_by is None:
            raise ValueError("changed_by cannot be None")
        
        if change_type not in [CHANGE_TYPE_CREATE, CHANGE_TYPE_UPDATE, CHANGE_TYPE_DELETE]:
            raise ValueError(f"Invalid change_type: {change_type}")
        
        # Call the parent class initializer
        super().__init__()
        
        # Set our attributes
        self.interaction_id = interaction_id
        self.changed_by = changed_by
        self.change_type = change_type
        self.before_state = before_state
        self.after_state = after_state
    
    def to_dict(self):
        """
        Converts the history record to a dictionary for serialization.
        
        Returns:
            dict: Dictionary representation of the history record
        """
        result = super().to_dict()
        
        # Add specific fields
        result.update({
            'interaction_id': self.interaction_id,
            'changed_by': self.changed_by,
            'change_type': self.change_type,
            'before_state': self.before_state,
            'after_state': self.after_state
        })
        
        return result
    
    def get_changes(self):
        """
        Computes the difference between before and after states.
        
        This method analyzes the before and after states to determine 
        exactly what fields were changed and how they changed.
        
        Returns:
            dict: Dictionary of changed fields with old and new values
        """
        changes = {}
        
        # For create operations, all fields in after_state are new
        if self.change_type == CHANGE_TYPE_CREATE and self.after_state:
            for key, value in self.after_state.items():
                changes[key] = {'old': None, 'new': value}
            return changes
        
        # For delete operations, all fields in before_state are removed
        if self.change_type == CHANGE_TYPE_DELETE and self.before_state:
            for key, value in self.before_state.items():
                changes[key] = {'old': value, 'new': None}
            return changes
        
        # For update operations, compare before and after states
        if self.change_type == CHANGE_TYPE_UPDATE and self.before_state and self.after_state:
            # Check for changed or added fields
            for key, new_value in self.after_state.items():
                old_value = self.before_state.get(key)
                if old_value != new_value:
                    changes[key] = {'old': old_value, 'new': new_value}
            
            # Check for removed fields
            for key in self.before_state:
                if key not in self.after_state:
                    changes[key] = {'old': self.before_state[key], 'new': None}
        
        return changes


def create_history_record(interaction, changed_by_id, change_type, before_state=None):
    """
    Utility function to create a history record for an interaction change.
    
    This helper function simplifies the creation of history records by
    automatically handling the conversion of an interaction object to
    its dictionary representation for the after_state.
    
    Args:
        interaction: The interaction instance being changed
        changed_by_id (int): ID of the user making the change
        change_type (str): Type of change (create, update, delete)
        before_state (dict, optional): State of the interaction before the change
            
    Returns:
        InteractionHistory: A new history record instance
    """
    # For create and update operations, we need the after state
    after_state = None
    if change_type != CHANGE_TYPE_DELETE:
        after_state = interaction.to_dict() if hasattr(interaction, 'to_dict') else None
    
    return InteractionHistory(
        interaction_id=interaction.id,
        changed_by=changed_by_id,
        change_type=change_type,
        before_state=before_state,
        after_state=after_state
    )