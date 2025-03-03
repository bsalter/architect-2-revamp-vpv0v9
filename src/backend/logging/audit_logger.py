"""
Specialized audit logging system for the Interaction Management System.

This module provides a comprehensive audit logging service that records security-relevant
events and data modifications for compliance, security monitoring, and troubleshooting.
It maintains detailed audit trails with user and site context for authentication,
authorization, data access, and data modification actions.
"""

import datetime
from typing import Dict, Any, Optional, List, Union

import flask  # version 2.3.2

from .structured_logger import StructuredLogger, get_context_data
from ..auth.user_context_service import UserContextService
from ..auth.site_context_service import SiteContextService
from ..models.interaction_history import (
    create_history_record,
    CHANGE_TYPE_CREATE,
    CHANGE_TYPE_UPDATE,
    CHANGE_TYPE_DELETE
)
from ..utils.datetime_util import get_utc_datetime

# Initialize structured logger
logger = StructuredLogger(__name__)

# Audit categories
AUTH_CATEGORY = 'authentication'
AUTHZ_CATEGORY = 'authorization'
DATA_ACCESS_CATEGORY = 'data_access'
DATA_MODIFY_CATEGORY = 'data_modification'


class AuditLogger:
    """Specialized logger for recording audit events related to security and data operations in the system."""
    
    def __init__(self, user_context_service: UserContextService, site_context_service: SiteContextService):
        """
        Initialize a new AuditLogger with dependencies.
        
        Args:
            user_context_service: Service for accessing current user information
            site_context_service: Service for accessing current site information
        """
        self._logger = StructuredLogger(__name__)
        self._user_context_service = user_context_service
        self._site_context_service = site_context_service
        
        logger.info("AuditLogger initialized")
    
    def log_authentication(self, action: str, username: str, success: bool, details: Dict = None) -> None:
        """
        Log authentication-related events such as login attempts and token operations.
        
        Args:
            action: The authentication action (e.g., 'login', 'token_refresh')
            username: Username attempting authentication
            success: Whether the authentication was successful
            details: Additional contextual details about the authentication event
        """
        # Create the audit event object
        audit_event = {
            'category': AUTH_CATEGORY,
            'action': action,
            'timestamp': get_utc_datetime(datetime.datetime.utcnow()).isoformat(),
            'username': username,
            'success': success
        }
        
        # Add IP address from request context if available
        ip_address = self._get_request_ip()
        if ip_address:
            audit_event['ip_address'] = ip_address
        
        # Add additional details if provided
        if details:
            audit_event.update(details)
        
        # Log at appropriate level based on success
        if success:
            self._logger.info(f"Authentication {action} succeeded for user {username}", audit_event)
        else:
            self._logger.warning(f"Authentication {action} failed for user {username}", audit_event)
    
    def log_authorization(self, action: str, resource_type: str, resource_id: str, 
                          success: bool, details: Dict = None) -> None:
        """
        Log authorization-related events such as permission checks and site access attempts.
        
        Args:
            action: The authorization action (e.g., 'access_site', 'edit_interaction')
            resource_type: Type of resource being accessed (e.g., 'site', 'interaction')
            resource_id: Identifier of the resource being accessed
            success: Whether the authorization was successful
            details: Additional contextual details about the authorization event
        """
        # Get the current user from the context service
        user_id = self._user_context_service.get_current_user_id()
        
        # Get the current site from the context service
        site_id = self._site_context_service.get_current_site_id()
        
        # Create the audit event object
        audit_event = {
            'category': AUTHZ_CATEGORY,
            'action': action,
            'timestamp': get_utc_datetime(datetime.datetime.utcnow()).isoformat(),
            'user_id': user_id,
            'site_id': site_id,
            'resource_type': resource_type,
            'resource_id': resource_id,
            'success': success
        }
        
        # Add IP address from request context if available
        ip_address = self._get_request_ip()
        if ip_address:
            audit_event['ip_address'] = ip_address
        
        # Add additional details if provided
        if details:
            audit_event.update(details)
        
        # Log at appropriate level based on success
        if success:
            self._logger.info(
                f"Authorization {action} granted for {resource_type} {resource_id}", 
                audit_event
            )
        else:
            self._logger.warning(
                f"Authorization {action} denied for {resource_type} {resource_id}", 
                audit_event
            )
    
    def log_data_access(self, action: str, resource_type: str, resource_id: str, 
                        details: Dict = None) -> None:
        """
        Log data access events such as viewing or querying sensitive information.
        
        Args:
            action: The data access action (e.g., 'view', 'search', 'export')
            resource_type: Type of resource being accessed (e.g., 'interaction', 'user')
            resource_id: Identifier of the resource being accessed
            details: Additional contextual details about the data access event
        """
        # Get the current user from the context service
        user_id = self._user_context_service.get_current_user_id()
        
        # Get the current site from the context service
        site_id = self._site_context_service.get_current_site_id()
        
        # Create the audit event object
        audit_event = {
            'category': DATA_ACCESS_CATEGORY,
            'action': action,
            'timestamp': get_utc_datetime(datetime.datetime.utcnow()).isoformat(),
            'user_id': user_id,
            'site_id': site_id,
            'resource_type': resource_type,
            'resource_id': resource_id
        }
        
        # Add IP address from request context if available
        ip_address = self._get_request_ip()
        if ip_address:
            audit_event['ip_address'] = ip_address
        
        # Add additional details if provided
        if details:
            audit_event.update(details)
        
        # Log data access events at info level
        self._logger.info(
            f"Data access {action} for {resource_type} {resource_id}", 
            audit_event
        )
    
    def log_data_modification(self, action: str, resource_type: str, resource_id: str, 
                             before_state: Dict = None, after_state: Dict = None, 
                             details: Dict = None) -> None:
        """
        Log data modification events such as create, update, or delete operations.
        
        Args:
            action: The modification action (e.g., 'create', 'update', 'delete')
            resource_type: Type of resource being modified (e.g., 'interaction', 'user')
            resource_id: Identifier of the resource being modified
            before_state: State of the resource before modification
            after_state: State of the resource after modification
            details: Additional contextual details about the modification event
        """
        # Get the current user from the context service
        user_id = self._user_context_service.get_current_user_id()
        
        # Get the current site from the context service
        site_id = self._site_context_service.get_current_site_id()
        
        # Create the audit event object
        audit_event = {
            'category': DATA_MODIFY_CATEGORY,
            'action': action,
            'timestamp': get_utc_datetime(datetime.datetime.utcnow()).isoformat(),
            'user_id': user_id,
            'site_id': site_id,
            'resource_type': resource_type,
            'resource_id': resource_id
        }
        
        # Add before/after state for change comparison
        if before_state:
            audit_event['before_state'] = before_state
        if after_state:
            audit_event['after_state'] = after_state
        
        # Add IP address from request context if available
        ip_address = self._get_request_ip()
        if ip_address:
            audit_event['ip_address'] = ip_address
        
        # Add additional details if provided
        if details:
            audit_event.update(details)
        
        # Log data modification events at info level
        self._logger.info(
            f"Data modification {action} for {resource_type} {resource_id}", 
            audit_event
        )
    
    def log_interaction_history(self, interaction: object, change_type: str, 
                               before_state: Dict = None) -> object:
        """
        Create a historical record of interaction changes and log the audit event.
        
        Args:
            interaction: The interaction object being modified
            change_type: Type of change (create, update, delete)
            before_state: State of the interaction before modification (for updates/deletes)
            
        Returns:
            Created history record object
        """
        # Get the current user from the context service
        user_id = self._user_context_service.get_current_user_id()
        
        # Verify change type is valid
        if change_type not in [CHANGE_TYPE_CREATE, CHANGE_TYPE_UPDATE, CHANGE_TYPE_DELETE]:
            raise ValueError(f"Invalid change_type: {change_type}")
        
        # Create history record
        history_record = create_history_record(
            interaction=interaction,
            changed_by_id=user_id,
            change_type=change_type,
            before_state=before_state
        )
        
        # Determine appropriate action name for the log entry
        action_names = {
            CHANGE_TYPE_CREATE: 'create',
            CHANGE_TYPE_UPDATE: 'update',
            CHANGE_TYPE_DELETE: 'delete'
        }
        action = action_names.get(change_type, change_type)
        
        # Log the data modification event
        self.log_data_modification(
            action=action,
            resource_type='interaction',
            resource_id=str(interaction.id),
            before_state=before_state,
            after_state=history_record.after_state if hasattr(history_record, 'after_state') else None,
            details={'history_record_id': history_record.id if hasattr(history_record, 'id') else None}
        )
        
        return history_record
    
    def _get_request_ip(self) -> Optional[str]:
        """
        Private helper method to extract client IP address from request.
        
        Returns:
            Client IP address or None if not available
        """
        if not flask.has_request_context():
            return None
        
        # Try to get X-Forwarded-For header first (for clients behind proxies)
        if flask.request.headers.get('X-Forwarded-For'):
            # Get the first IP in the chain (original client)
            return flask.request.headers.get('X-Forwarded-For').split(',')[0].strip()
        
        # Fall back to remote_addr
        return flask.request.remote_addr