"""
Interaction Management System Backend
=====================================

This package contains the backend implementation for the Interaction Management System,
a web application for managing and viewing interaction records through a searchable
table interface and a dedicated add/edit form.

The backend provides RESTful API services for authentication, interaction management,
and search functionality with site-scoped access control.
"""

import os  # version: standard library

# Version information
__version__ = '1.0.0'

# Application name
__app_name__ = 'Interaction Management System Backend'

# Current execution environment
# Default to 'development' if FLASK_ENV is not set
__environment__ = os.getenv('FLASK_ENV', 'development')

# Validate environment to ensure it's one of the expected values
if __environment__ not in ['development', 'testing', 'staging', 'production']:
    import warnings
    warnings.warn(
        f"Unexpected environment '{__environment__}'. "
        f"Expected one of: development, testing, staging, production."
    )