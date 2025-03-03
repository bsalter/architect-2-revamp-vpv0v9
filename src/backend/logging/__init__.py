"""
Initializes and exposes the logging package functionality for the Interaction Management System.

This module serves as the central entry point for all logging capabilities including structured logging,
audit logging, performance monitoring, and error tracking.
"""

import logging  # standard library
import os  # standard library

# Internal imports
from .formatters import JsonFormatter, ConsoleFormatter, format_exc_info  # src/backend/logging/formatters.py
from .structured_logger import StructuredLogger, RequestAdapter, get_request_id, set_request_context, clear_request_context, configure_logger  # src/backend/logging/structured_logger.py
from .audit_logger import AuditLogger, AUTH_CATEGORY, AUTHZ_CATEGORY, DATA_ACCESS_CATEGORY, DATA_MODIFY_CATEGORY  # src/backend/logging/audit_logger.py
from .performance_monitor import PerformanceMonitor, Timer, time_function, METRIC_CATEGORIES  # src/backend/logging/performance_monitor.py
from .error_tracker import ErrorTracker  # src/backend/logging/error_tracker.py
from ..utils.constants import LOG_LEVEL  # src/backend/utils/constants.py

# Initialize root logger
logger = logging.getLogger(__name__)

# Default configuration for logging
DEFAULT_CONFIG = {
    "level": LOG_LEVEL,
    "json_output": True,
    "console_output": True,
    "file_output": False,
    "log_path": "logs/application.log"
}

# Initialize AuditLogger instance
audit_logger = AuditLogger()

# Initialize PerformanceMonitor instance
performance_monitor = PerformanceMonitor()

# Initialize ErrorTracker instance
error_tracker = ErrorTracker({})


def configure_logging(config: Dict[str, Any]) -> None:
    """
    Configure the logging system with application-specific settings.

    Args:
        config: Dictionary containing logging configuration options.
    """
    # Merge provided config with DEFAULT_CONFIG
    merged_config = DEFAULT_CONFIG.copy()
    merged_config.update(config)

    # Set up root logger with appropriate level
    log_level_name = merged_config.get('level', os.environ.get('LOG_LEVEL', 'INFO'))
    try:
        log_level = getattr(logging, log_level_name.upper())
    except AttributeError:
        log_level = logging.INFO
    logger.setLevel(log_level)

    # Configure structured logging with formatters
    json_output = merged_config.get('json_output', True)
    console_output = merged_config.get('console_output', True)
    file_output = merged_config.get('file_output', False)
    log_path = merged_config.get('log_path', 'application.log')

    # Configure structured logging with formatters
    configure_logger(merged_config)

    # Set up audit logger with configuration
    # The AuditLogger class is already initialized, so no further configuration is needed here

    # Set up performance monitor with configuration
    # The PerformanceMonitor class is already initialized, so no further configuration is needed here

    # Set up error tracker with configuration
    # The ErrorTracker class is already initialized, so no further configuration is needed here

    # Log successful initialization of logging system
    logger.info("Logging configuration initialized successfully")


def get_logger(name: str) -> StructuredLogger:
    """
    Get a configured structured logger for a specific module.

    Args:
        name: Name of the module requesting the logger

    Returns:
        Configured logger instance for the specified module
    """
    # Create a new StructuredLogger instance with the given name
    structured_logger = StructuredLogger(name)

    # Configure the logger with application defaults
    # The StructuredLogger class handles its own configuration

    # Return the configured logger instance
    return structured_logger


__all__ = [
    "configure_logging",
    "get_logger",
    "StructuredLogger",
    "RequestAdapter",
    "AuditLogger",
    "PerformanceMonitor",
    "Timer",
    "ErrorTracker",
    "audit_logger",
    "performance_monitor",
    "error_tracker",
    "time_function",
    "get_request_id",
    "set_request_context",
    "clear_request_context"
]