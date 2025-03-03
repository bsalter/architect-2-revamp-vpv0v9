"""
Structured logging implementation for the Interaction Management System.

This module provides a structured logging framework that automatically enriches
log entries with contextual information including request IDs, user context, and
site information. It supports both JSON and human-readable log formats and seamlessly 
integrates with Flask applications through middleware.
"""

import logging
import uuid
import os
import sys
import threading
from typing import Dict, Any, Optional, Union

# Try to import Flask-specific modules - will fail gracefully if Flask is not available
try:
    from flask import request, g, has_request_context
except ImportError:
    # Create dummy functions for non-Flask environments
    def has_request_context(): return False
    request, g = None, None

from .formatters import JsonFormatter, ConsoleFormatter, format_exc_info
from ..utils.constants import LOG_LEVEL  # This will be handled with a fallback if not found

# Thread-local storage for request context
_request_context = threading.local()

# Default logging configuration
DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DEFAULT_LOG_LEVEL = logging.INFO


def configure_logger(config: Dict[str, Any]) -> None:
    """
    Configure the Python logging system with appropriate handlers and formatters.
    
    Args:
        config: Dictionary containing logging configuration options.
        
    Configuration options:
        level: Logging level (DEBUG, INFO, etc.)
        json_output: Whether to enable JSON output (True/False)
        console_output: Whether to enable console output (True/False)
        file_output: Whether to enable file output (True/False)
        file_path: Path to log file (required if file_output is True)
        format: Log format string (optional, defaults to DEFAULT_LOG_FORMAT)
    """
    # Get log level from config, constants, environment or use default
    log_level_name = config.get('level', os.environ.get('LOG_LEVEL', None))
    if log_level_name is not None:
        try:
            log_level = getattr(logging, log_level_name.upper())
        except (AttributeError, TypeError):
            log_level = DEFAULT_LOG_LEVEL
    else:
        # Try to use LOG_LEVEL from constants, if it fails use default
        try:
            log_level = LOG_LEVEL
        except NameError:
            log_level = DEFAULT_LOG_LEVEL
    
    # Get root logger and set its level
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove existing handlers to prevent duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Configure JSON logging handler
    if config.get('json_output', False):
        json_handler = logging.StreamHandler(sys.stdout)
        json_formatter = JsonFormatter(
            ensure_ascii=config.get('ensure_ascii', True),
            include_logger_name=config.get('include_logger_name', True),
            include_timestamp=config.get('include_timestamp', True)
        )
        json_handler.setFormatter(json_formatter)
        root_logger.addHandler(json_handler)
    
    # Configure console logging handler
    if config.get('console_output', True):
        console_handler = logging.StreamHandler(sys.stderr)
        console_formatter = ConsoleFormatter(
            include_timestamp=config.get('include_timestamp', True),
            colorize=config.get('colorize', True)
        )
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)
    
    # Configure file logging handler
    if config.get('file_output', False):
        file_path = config.get('file_path', 'application.log')
        try:
            file_handler = logging.FileHandler(file_path)
            file_format = config.get('format', DEFAULT_LOG_FORMAT)
            file_formatter = logging.Formatter(file_format)
            file_handler.setFormatter(file_formatter)
            root_logger.addHandler(file_handler)
        except Exception as e:
            # Log error to console since file handler couldn't be created
            logging.error(f"Failed to configure file logging: {str(e)}")
    
    # Log configuration completion at debug level
    logging.debug("Logging configuration completed")


def get_request_id() -> str:
    """
    Get the current request ID from thread-local storage or generate a new one.
    
    Returns:
        str: Current request ID for correlation
    """
    # Try to get request_id from thread-local storage
    try:
        return getattr(_request_context, 'request_id')
    except AttributeError:
        # If not in thread-local storage, check if in Flask request context
        if has_request_context():
            # Try to get from X-Request-ID header
            request_id = request.headers.get('X-Request-ID')
            if request_id:
                # Store in thread-local for future calls
                setattr(_request_context, 'request_id', request_id)
                return request_id
        
        # Generate new UUID if not found
        request_id = str(uuid.uuid4())
        setattr(_request_context, 'request_id', request_id)
        return request_id


def set_request_context(context: Dict[str, Any]) -> None:
    """
    Set the request context information in thread-local storage.
    
    Args:
        context: Dictionary containing context information
    """
    # Store all provided context values in thread-local storage
    for key, value in context.items():
        setattr(_request_context, key, value)
    
    # Ensure request_id is set
    if not hasattr(_request_context, 'request_id'):
        setattr(_request_context, 'request_id', get_request_id())


def clear_request_context() -> None:
    """
    Clear the request context from thread-local storage.
    """
    # Reset thread-local storage to empty state
    _request_context.__dict__.clear()


def get_context_data() -> Dict[str, Any]:
    """
    Get all available context data for the current request.
    
    Returns:
        dict: Combined context data from request, user, and site
    """
    # Initialize context with request ID
    context = {'request_id': get_request_id()}
    
    # Add all other thread-local context values
    for key, value in _request_context.__dict__.items():
        if key != 'request_id':  # Already added
            context[key] = value
    
    # Add Flask context if available
    if has_request_context():
        # Add request information
        context.update({
            'method': request.method,
            'path': request.path,
            'remote_addr': request.remote_addr
        })
        
        # Add user information if available in g
        if hasattr(g, 'user_id'):
            context['user_id'] = g.user_id
        
        # Add site information if available in g
        if hasattr(g, 'site_id'):
            context['site_id'] = g.site_id
        elif hasattr(g, 'site_ids') and g.site_ids:
            context['site_ids'] = g.site_ids
    
    return context


class RequestAdapter:
    """
    Flask middleware that sets and clears request context for logging.
    
    This adapter integrates with Flask to automatically extract and manage
    request context information for logging purposes throughout the request lifecycle.
    """
    
    def __init__(self, app):
        """
        Initialize a new RequestAdapter with a Flask application.
        
        Args:
            app: Flask application instance
        """
        self.app = app
        
        # Register Flask hooks for request handling
        app.before_request(self.before_request)
        app.teardown_request(self.teardown_request)
    
    def before_request(self):
        """
        Set up request context before handling the request.
        """
        # Extract request ID from headers or generate new one
        request_id = request.headers.get('X-Request-ID', str(uuid.uuid4()))
        
        # Create context dictionary with request information
        context = {
            'request_id': request_id,
            'method': request.method,
            'path': request.path,
            'remote_addr': request.remote_addr,
            'user_agent': request.headers.get('User-Agent', '')
        }
        
        # Set the request context
        set_request_context(context)
    
    def teardown_request(self, exception):
        """
        Clean up request context after request is handled.
        
        Args:
            exception: Exception that occurred during request handling, if any
        """
        # Clear thread-local request context
        clear_request_context()


class StructuredLogger:
    """
    Enhanced logger that automatically includes context information with every log entry.
    
    This logger wraps the standard Python logger to add contextual information
    to every log message, making logs more informative and traceable.
    """
    
    def __init__(self, name: str):
        """
        Initialize a structured logger for a specific module.
        
        Args:
            name: Logger name, typically __name__ of the calling module
        """
        # Get standard Python logger with given name
        self._logger = logging.getLogger(name)
        self.name = name
        
        # Initialize with default level if not already set
        if not self._logger.level:
            try:
                self._logger.setLevel(LOG_LEVEL)
            except NameError:
                self._logger.setLevel(DEFAULT_LOG_LEVEL)
    
    def debug(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """
        Log message at DEBUG level with context information.
        
        Args:
            message: Message to log
            extra: Additional contextual information
        """
        # Get context data
        context = get_context_data()
        
        # Merge extra data with context data
        if extra:
            context.update(extra)
        
        # Log message at DEBUG level with merged context
        self._logger.debug(message, extra=context)
    
    def info(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """
        Log message at INFO level with context information.
        
        Args:
            message: Message to log
            extra: Additional contextual information
        """
        # Get context data
        context = get_context_data()
        
        # Merge extra data with context data
        if extra:
            context.update(extra)
        
        # Log message at INFO level with merged context
        self._logger.info(message, extra=context)
    
    def warning(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """
        Log message at WARNING level with context information.
        
        Args:
            message: Message to log
            extra: Additional contextual information
        """
        # Get context data
        context = get_context_data()
        
        # Merge extra data with context data
        if extra:
            context.update(extra)
        
        # Log message at WARNING level with merged context
        self._logger.warning(message, extra=context)
    
    def error(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """
        Log message at ERROR level with context information.
        
        Args:
            message: Message to log
            extra: Additional contextual information
        """
        # Get context data
        context = get_context_data()
        
        # Merge extra data with context data
        if extra:
            context.update(extra)
        
        # Log message at ERROR level with merged context
        self._logger.error(message, extra=context)
    
    def critical(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """
        Log message at CRITICAL level with context information.
        
        Args:
            message: Message to log
            extra: Additional contextual information
        """
        # Get context data
        context = get_context_data()
        
        # Merge extra data with context data
        if extra:
            context.update(extra)
        
        # Log message at CRITICAL level with merged context
        self._logger.critical(message, extra=context)
    
    def exception(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """
        Log exception at ERROR level with context information and stack trace.
        
        Args:
            message: Message to log
            extra: Additional contextual information
        """
        # Get context data
        context = get_context_data()
        
        # Merge extra data with context data
        if extra:
            context.update(extra)
        
        # Format exception information using format_exc_info
        if sys.exc_info() != (None, None, None):
            exc_formatted = format_exc_info(sys.exc_info())
            context['exception'] = exc_formatted
        
        # Log message at ERROR level with merged context and exc_info=True
        self._logger.exception(message, extra=context)
    
    def set_level(self, level: int) -> None:
        """
        Set the logging level for this logger.
        
        Args:
            level: New logging level from logging module constants
        """
        self._logger.setLevel(level)
    
    def add_handler(self, handler: logging.Handler) -> None:
        """
        Add a handler to this logger.
        
        Args:
            handler: Handler instance to add
        """
        self._logger.addHandler(handler)
    
    def get_level(self) -> int:
        """
        Get the current logging level for this logger.
        
        Returns:
            int: Current logging level
        """
        return self._logger.level