"""
Error Tracking module for the Interaction Management System.

This module provides a centralized error tracking system for capturing,
analyzing, and reporting application errors. It tracks error frequency,
stores contextual information for debugging, and optionally integrates
with external error monitoring services.
"""

import json
import threading
import traceback
from collections import Counter, defaultdict
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple, Union

try:
    from flask import request, g, has_request_context
except ImportError:
    # Dummy functions for environments without Flask
    def has_request_context(): return False
    request, g = None, None

from .structured_logger import StructuredLogger, get_context_data
from .formatters import format_exc_info
from ..utils.enums import ErrorType
from ..utils.error_util import BaseAppException
from ..config import get_env_var, LOGGING_CONFIG

# Initialize logger
logger = StructuredLogger(__name__)

# Configuration from environment
ERROR_TRACKER_ENABLED = get_env_var('ERROR_TRACKER_ENABLED', 'true').lower() == 'true'
ERROR_TRACKER_MAX_ITEMS = int(get_env_var('ERROR_TRACKER_MAX_ITEMS', '1000'))
EXTERNAL_ERROR_SERVICE_ENABLED = get_env_var('EXTERNAL_ERROR_SERVICE_ENABLED', 'false').lower() == 'true'


def get_error_fingerprint(exception: Exception, error_type: str = None) -> str:
    """
    Generate a unique fingerprint for an error based on error type, message and location.
    
    Args:
        exception: The exception to generate a fingerprint for
        error_type: Optional error type classification
        
    Returns:
        A unique string fingerprint for grouping similar errors
    """
    # Extract exception class name and module
    exc_type = exception.__class__.__name__
    exc_module = exception.__class__.__module__
    
    # Get message and normalize it (remove variable parts like IDs, timestamps)
    message = str(exception)
    
    # Extract error location from traceback
    tb = traceback.extract_tb(exception.__traceback__) if exception.__traceback__ else []
    location = ""
    if tb:
        frame = tb[-1]  # Last frame is where the error occurred
        location = f"{frame.filename}:{frame.lineno}"
    
    # Combine components into a unique fingerprint
    components = [exc_module, exc_type, message, location]
    
    # Add error_type if provided
    if error_type:
        components.insert(0, error_type)
        
    # Create fingerprint
    fingerprint = ":".join(components)
    
    # Hash long fingerprints to maintain reasonable length
    if len(fingerprint) > 256:
        import hashlib
        return hashlib.md5(fingerprint.encode()).hexdigest()
    
    return fingerprint


def format_error_context(exception: Exception, additional_context: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Format context information for an error to provide debugging details.
    
    Args:
        exception: The exception that occurred
        additional_context: Additional context to include in the error report
        
    Returns:
        Formatted error context with exception details and environment information
    """
    # Get basic exception information
    exc_type = exception.__class__.__name__
    exc_module = exception.__class__.__module__
    exc_message = str(exception)
    
    # Format traceback
    tb_formatted = format_exc_info((exception.__class__, exception, exception.__traceback__))
    
    # Get request context
    context_data = get_context_data()
    
    # Build error context
    error_context = {
        'exception': {
            'type': exc_type,
            'module': exc_module,
            'message': exc_message,
            'traceback': tb_formatted
        },
        'timestamp': datetime.utcnow().isoformat(),
        'context': context_data
    }
    
    # Add environment information
    error_context['environment'] = {
        'app_version': get_env_var('APP_VERSION', 'unknown'),
        'environment': get_env_var('FLASK_ENV', 'development')
    }
    
    # Add additional context if provided
    if additional_context:
        error_context.update(additional_context)
    
    # Sanitize the context before returning
    return sanitize_error_data(error_context)


def sanitize_error_data(error_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitize error data to remove sensitive information before storage or transmission.
    
    Args:
        error_data: Error data dictionary to sanitize
        
    Returns:
        Sanitized error data with sensitive information removed
    """
    import copy
    
    # Create a deep copy to avoid modifying the original
    sanitized = copy.deepcopy(error_data)
    
    # Sensitive keys that should be redacted
    sensitive_keys = [
        'password', 'token', 'secret', 'key', 'auth', 'jwt', 'credential',
        'apikey', 'api_key', 'access_token', 'refresh_token'
    ]
    
    # Function to recursively sanitize dictionaries
    def _sanitize_dict(d):
        for key, value in list(d.items()):
            # Check if key name contains sensitive information
            if any(s in key.lower() for s in sensitive_keys):
                d[key] = '[REDACTED]'
            # Recursively sanitize nested dictionaries
            elif isinstance(value, dict):
                _sanitize_dict(value)
            # Sanitize items in lists
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    if isinstance(item, dict):
                        _sanitize_dict(item)
            # Ensure values are JSON serializable
            elif not isinstance(value, (str, int, float, bool, list, dict, type(None))):
                try:
                    d[key] = str(value)
                except:
                    d[key] = '[UNSERIALIZABLE]'
    
    # Apply sanitization
    _sanitize_dict(sanitized)
    
    return sanitized


class ErrorTracker:
    """
    Tracks application errors, their frequency, and context for debugging and monitoring.
    
    This class maintains in-memory error tracking with count, context, and timestamp
    information to help identify and diagnose recurring issues in the application.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the error tracker with configuration options.
        
        Args:
            config: Configuration dictionary with options like enabled, max_items, etc.
        """
        # Initialize data structures for tracking errors
        self._error_counts = Counter()  # Count occurrences by fingerprint
        self._error_contexts = {}  # Store last context by fingerprint
        self._error_timestamps = {}  # Store first and last occurrence timestamps
        
        # Thread safety
        self._lock = threading.Lock()
        
        # Configure from provided config or environment
        self._enabled = ERROR_TRACKER_ENABLED
        self._max_items = ERROR_TRACKER_MAX_ITEMS
        
        # Override with config if provided
        if config:
            self._enabled = config.get('enabled', self._enabled)
            self._max_items = config.get('max_items', self._max_items)
        
        logger.info(f"Error tracker initialized. Enabled: {self._enabled}, Max items: {self._max_items}")
    
    def track_exception(self, exception: Exception, context: Dict[str, Any] = None,
                       error_type: str = None, notify: bool = False) -> str:
        """
        Track an exception with its context and update error metrics.
        
        Args:
            exception: The exception to track
            context: Additional context for the error
            error_type: Optional error type classification
            notify: Whether to send to external service (if enabled)
            
        Returns:
            Error fingerprint generated for the exception
        """
        if not self._enabled:
            logger.debug("Error tracker is disabled, skipping tracking")
            return ""
        
        # Generate error fingerprint
        fingerprint = get_error_fingerprint(exception, error_type)
        
        # Format error context
        error_context = format_error_context(exception, context)
        
        # Update error tracking data
        with self._lock:
            # Increment error count
            self._error_counts[fingerprint] += 1
            
            # Store most recent context
            self._error_contexts[fingerprint] = error_context
            
            # Update timestamps
            current_time = datetime.utcnow()
            if fingerprint not in self._error_timestamps:
                self._error_timestamps[fingerprint] = {
                    'first_seen': current_time,
                    'last_seen': current_time
                }
            else:
                self._error_timestamps[fingerprint]['last_seen'] = current_time
            
            # Prune old errors if needed
            self._prune_old_errors()
        
        # Send to external service if enabled and notify flag is set
        if EXTERNAL_ERROR_SERVICE_ENABLED and notify:
            self.send_to_external_service(exception, error_context, fingerprint)
        
        logger.error(f"Tracked exception: {str(exception)}", extra={
            'fingerprint': fingerprint,
            'error_type': error_type or getattr(exception, 'error_type', ErrorType.SERVER.value),
            'count': self._error_counts[fingerprint]
        })
        
        return fingerprint
    
    def get_error_metrics(self) -> Dict[str, Any]:
        """
        Retrieve current error metrics and statistics.
        
        Returns:
            Error metrics including counts, timestamps, and trends
        """
        with self._lock:
            # Calculate error frequency (per hour) for each error
            current_time = datetime.utcnow()
            error_frequency = {}
            
            for fingerprint, timestamps in self._error_timestamps.items():
                first_seen = timestamps['first_seen']
                last_seen = timestamps['last_seen']
                count = self._error_counts[fingerprint]
                
                # Calculate hours between first and last occurrence
                hours_diff = max(1, (last_seen - first_seen).total_seconds() / 3600)
                
                # Calculate frequency (occurrences per hour)
                frequency = count / hours_diff
                error_frequency[fingerprint] = frequency
            
            # Get most frequent errors
            most_frequent = {}
            for fingerprint, freq in sorted(error_frequency.items(), 
                                           key=lambda x: x[1], reverse=True)[:10]:
                most_frequent[fingerprint] = {
                    'count': self._error_counts[fingerprint],
                    'frequency': freq,
                    'last_seen': self._error_timestamps[fingerprint]['last_seen'].isoformat()
                }
            
            # Get most recent errors
            most_recent = {}
            for fingerprint, timestamps in sorted(self._error_timestamps.items(), 
                                                key=lambda x: x[1]['last_seen'], reverse=True)[:10]:
                most_recent[fingerprint] = {
                    'count': self._error_counts[fingerprint],
                    'first_seen': timestamps['first_seen'].isoformat(),
                    'last_seen': timestamps['last_seen'].isoformat()
                }
            
            # Calculate overall metrics
            total_errors = sum(self._error_counts.values())
            unique_errors = len(self._error_counts)
            
            # Return complete metrics
            return {
                'total_errors': total_errors,
                'unique_errors': unique_errors,
                'most_frequent': most_frequent,
                'most_recent': most_recent,
                'timestamp': current_time.isoformat()
            }
    
    def get_error_details(self, fingerprint: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific error by fingerprint.
        
        Args:
            fingerprint: The error fingerprint to get details for
            
        Returns:
            Complete error information including context and occurrences
        """
        with self._lock:
            if fingerprint not in self._error_counts:
                return None
            
            return {
                'fingerprint': fingerprint,
                'count': self._error_counts[fingerprint],
                'first_seen': self._error_timestamps[fingerprint]['first_seen'].isoformat(),
                'last_seen': self._error_timestamps[fingerprint]['last_seen'].isoformat(),
                'context': self._error_contexts[fingerprint]
            }
    
    def clear_errors(self, fingerprint: str = None) -> bool:
        """
        Clear all tracked errors or a specific error by fingerprint.
        
        Args:
            fingerprint: Optional specific error fingerprint to clear
            
        Returns:
            True if errors were cleared, False otherwise
        """
        with self._lock:
            if fingerprint:
                # Clear specific error
                if fingerprint in self._error_counts:
                    del self._error_counts[fingerprint]
                    del self._error_contexts[fingerprint]
                    del self._error_timestamps[fingerprint]
                    logger.info(f"Cleared error with fingerprint: {fingerprint}")
                    return True
                return False
            else:
                # Clear all errors
                self._error_counts.clear()
                self._error_contexts.clear()
                self._error_timestamps.clear()
                logger.info("Cleared all tracked errors")
                return True
    
    def send_to_external_service(self, exception: Exception, context: Dict[str, Any],
                               fingerprint: str) -> bool:
        """
        Send error information to an external error monitoring service.
        
        Args:
            exception: The exception that occurred
            context: Error context information
            fingerprint: Error fingerprint
            
        Returns:
            True if successfully sent, False otherwise
        """
        if not EXTERNAL_ERROR_SERVICE_ENABLED:
            return False
        
        try:
            # This implementation is a placeholder for real external service integration
            # In a real implementation, we would send to Sentry, LogRocket, New Relic, etc.
            
            # Format data for the external service
            error_data = {
                'fingerprint': fingerprint,
                'exception': {
                    'type': exception.__class__.__name__,
                    'message': str(exception),
                },
                'context': context,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Mock sending to external service
            logger.info(f"Would send error to external service: {fingerprint}")
            
            # In a real implementation, use requests library to send to service:
            # import requests
            # response = requests.post(
            #     'https://external-error-service.example.com/api/errors',
            #     json=error_data,
            #     headers={'Authorization': f'Bearer {API_KEY}'}
            # )
            # return response.status_code == 200
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send error to external service: {str(e)}")
            return False
    
    def is_enabled(self) -> bool:
        """
        Check if error tracking is currently enabled.
        
        Returns:
            True if error tracking is enabled, False otherwise
        """
        return self._enabled
    
    def set_enabled(self, enabled: bool) -> None:
        """
        Enable or disable error tracking.
        
        Args:
            enabled: Whether error tracking should be enabled
        """
        self._enabled = enabled
        logger.info(f"Error tracking {'enabled' if enabled else 'disabled'}")
    
    def set_max_items(self, max_items: int) -> None:
        """
        Set the maximum number of distinct errors to track.
        
        Args:
            max_items: Maximum number of errors to track
        """
        if max_items < 1:
            raise ValueError("max_items must be at least 1")
        
        self._max_items = max_items
        logger.info(f"Error tracker max items set to: {max_items}")
        
        # Prune if current count exceeds new limit
        self._prune_old_errors()
    
    def _prune_old_errors(self) -> int:
        """
        Private method to remove oldest errors when limit is reached.
        
        Returns:
            Number of errors removed
        """
        current_count = len(self._error_counts)
        if current_count <= self._max_items:
            return 0
        
        # Calculate how many to remove
        to_remove = current_count - self._max_items
        
        # Get oldest errors
        oldest_errors = sorted(
            self._error_timestamps.items(),
            key=lambda x: x[1]['last_seen']
        )[:to_remove]
        
        # Remove oldest errors
        for fingerprint, _ in oldest_errors:
            del self._error_counts[fingerprint]
            del self._error_contexts[fingerprint]
            del self._error_timestamps[fingerprint]
        
        logger.info(f"Pruned {to_remove} old errors to stay within limit")
        return to_remove