"""
Logging formatters for the Interaction Management System.

This module provides custom logging formatters that generate consistently
structured logs in both JSON and human-readable formats. These formatters
ensure logs contain all necessary context while enabling both machine
processing and human readability.
"""

import json
import logging
import traceback
from datetime import datetime

from ..utils.datetime_util import format_datetime

# Reserved attributes from LogRecord that should be handled specially
RESERVED_ATTRS = [
    'args', 'asctime', 'created', 'exc_info', 'exc_text', 'filename',
    'funcName', 'levelname', 'levelno', 'lineno', 'module', 'msecs',
    'message', 'msg', 'name', 'pathname', 'process', 'processName',
    'relativeCreated', 'stack_info', 'thread', 'threadName'
]


def format_exc_info(exc_info):
    """
    Format exception information into a structured dictionary.
    
    Args:
        exc_info (tuple): Exception information tuple (type, value, traceback)
        
    Returns:
        dict: Structured exception information including type, message, and traceback
    """
    if not exc_info:
        return None
        
    exc_type, exc_value, exc_tb = exc_info
    
    # Format exception details
    formatted_exception = {
        'type': exc_type.__name__ if exc_type else None,
        'message': str(exc_value) if exc_value else None,
        'traceback': traceback.format_tb(exc_tb) if exc_tb else None
    }
    
    return formatted_exception


def sanitize_log_record(record_dict):
    """
    Sanitize log record by removing sensitive data and formatting complex objects.
    
    Args:
        record_dict (dict): Log record dictionary to sanitize
        
    Returns:
        dict: Sanitized log record safe for persistence
    """
    sanitized = record_dict.copy()
    
    # List of sensitive field names to redact
    sensitive_fields = [
        'password', 'token', 'secret', 'key', 'auth', 'jwt', 'credential'
    ]
    
    # Redact sensitive data
    for key in sanitized:
        if any(sensitive in key.lower() for sensitive in sensitive_fields):
            sanitized[key] = '[REDACTED]'
    
    # Ensure all values are JSON serializable
    for key, value in list(sanitized.items()):
        # Handle non-serializable objects
        if not isinstance(value, (str, int, float, bool, list, dict, type(None))):
            try:
                # Try to convert to string representation
                sanitized[key] = str(value)
            except:
                # If conversion fails, remove the field
                del sanitized[key]
                
    return sanitized


class JsonFormatter(logging.Formatter):
    """
    Log formatter that outputs logs in JSON format for machine processing.
    """
    
    def __init__(self, ensure_ascii=True, include_logger_name=True, include_timestamp=True):
        """
        Initialize JSON formatter with configuration options.
        
        Args:
            ensure_ascii (bool): Ensure the output contains only ASCII characters
            include_logger_name (bool): Include logger name in output
            include_timestamp (bool): Include formatted timestamp in output
        """
        super().__init__('')
        self.ensure_ascii = ensure_ascii
        self.include_logger_name = include_logger_name
        self.include_timestamp = include_timestamp
    
    def format(self, record):
        """
        Format log record as JSON string.
        
        Args:
            record (logging.LogRecord): The log record to format
            
        Returns:
            str: JSON string representation of the log record
        """
        # Create base log dictionary
        log_dict = self.to_dict(record)
        
        # Add timestamp if configured
        if self.include_timestamp:
            log_dict['timestamp'] = format_datetime(datetime.fromtimestamp(record.created))
        
        # Add logger name if configured
        if self.include_logger_name and record.name:
            log_dict['logger'] = record.name
            
        # Process exception info if present
        if record.exc_info:
            log_dict['exception'] = format_exc_info(record.exc_info)
            
        # Sanitize the log dictionary
        log_dict = sanitize_log_record(log_dict)
        
        # Convert to JSON
        return json.dumps(log_dict, ensure_ascii=self.ensure_ascii)
    
    def to_dict(self, record):
        """
        Convert log record to dictionary before JSON serialization.
        
        Args:
            record (logging.LogRecord): The log record to convert
            
        Returns:
            dict: Dictionary representation of log record
        """
        # Create base dictionary with standard fields
        log_dict = {
            'level': record.levelname,
            'message': record.getMessage()
        }
        
        # Add all non-reserved attributes from record
        for key, value in record.__dict__.items():
            if key not in RESERVED_ATTRS and key != 'message':
                log_dict[key] = value
                
        return log_dict


class ConsoleFormatter(logging.Formatter):
    """
    Log formatter that outputs human-readable logs for console display.
    """
    
    def __init__(self, include_timestamp=True, colorize=True):
        """
        Initialize console formatter with configuration options.
        
        Args:
            include_timestamp (bool): Include formatted timestamp in output
            colorize (bool): Apply ANSI color codes to output based on log level
        """
        super().__init__('')
        self.include_timestamp = include_timestamp
        self.colorize = colorize
        
        # ANSI color codes for different log levels
        self.colors = {
            logging.DEBUG: '\033[36m',      # Cyan
            logging.INFO: '\033[32m',       # Green
            logging.WARNING: '\033[33m',    # Yellow
            logging.ERROR: '\033[31m',      # Red
            logging.CRITICAL: '\033[41;37m' # White on Red background
        }
        self.reset_color = '\033[0m'
        
    def format(self, record):
        """
        Format log record as human-readable string.
        
        Args:
            record (logging.LogRecord): The log record to format
            
        Returns:
            str: Formatted log string for console output
        """
        # Create base components list
        components = []
        
        # Add timestamp if configured
        if self.include_timestamp:
            timestamp = format_datetime(datetime.fromtimestamp(record.created))
            components.append(f"[{timestamp}]")
            
        # Add log level
        level_str = f"[{record.levelname}]"
        components.append(self._colorize(level_str, record.levelno))
        
        # Add logger name
        components.append(f"[{record.name}]")
        
        # Add message
        components.append(record.getMessage())
        
        # Add any extra attributes
        extras = []
        for key, value in record.__dict__.items():
            if key not in RESERVED_ATTRS and key != 'message' and value is not None:
                extras.append(f"{key}={value}")
                
        if extras:
            components.append('(' + ', '.join(extras) + ')')
            
        # Join components
        formatted = ' '.join(components)
        
        # Add exception info if present
        if record.exc_info:
            formatted += '\n' + self.formatException(record.exc_info)
            
        return formatted
        
    def formatException(self, exc_info):
        """
        Format exception information for human readability.
        
        Args:
            exc_info (tuple): Exception information tuple (type, value, traceback)
            
        Returns:
            str: Formatted exception string
        """
        formatted = traceback.format_exception(*exc_info)
        formatted_str = ''.join(formatted)
        
        if self.colorize:
            formatted_str = self.colors.get(logging.ERROR, '') + formatted_str + self.reset_color
            
        return formatted_str
        
    def _colorize(self, text, level):
        """
        Apply ANSI color codes based on log level.
        
        Args:
            text (str): Text to colorize
            level (int): Log level (from logging module constants)
            
        Returns:
            str: Color-coded text string
        """
        if not self.colorize:
            return text
            
        color_code = self.colors.get(level, '')
        if not color_code:
            return text
            
        return color_code + text + self.reset_color