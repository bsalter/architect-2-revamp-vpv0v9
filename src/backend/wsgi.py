"""
WSGI entry point script that creates and exposes the Flask application instance for production deployment.
This file serves as the interface between the WSGI server (like Gunicorn) and the Flask application.
"""

import os  # Standard library import for accessing environment variables

from app import create_app  # Import the application factory function from the app module

# Determine the environment from the FLASK_ENV environment variable, defaulting to 'production'
environment = os.getenv('FLASK_ENV', 'production')

# Create the Flask application instance using the application factory
application = create_app(environment)

# The 'application' object is now ready to be served by a WSGI server like Gunicorn
# Example Gunicorn command: gunicorn --bind 0.0.0.0:8000 wsgi:application