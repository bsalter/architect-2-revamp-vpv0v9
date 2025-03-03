"""
This module initializes and configures Flask extensions used throughout the application.
Extensions are created here without binding to a Flask app instance, allowing them to be
imported anywhere and initialized later during app creation (application factory pattern).
"""

from flask_sqlalchemy import SQLAlchemy  # version 2.0.19
from flask_jwt_extended import JWTManager  # version 4.5.2
from flask_cors import CORS  # version 4.0.0
from flask_migrate import Migrate  # version 4.0.4
from flask_marshmallow import Marshmallow  # version 0.15.0
from redis import Redis  # version 7.0.12

# Database ORM instance
db = SQLAlchemy()

# JWT manager for authentication and authorization
jwt = JWTManager()

# CORS extension for handling cross-origin requests
cors = CORS()

# Database migration manager (uses Alembic)
migrate = Migrate()

# Serialization/deserialization library for data validation and formatting
ma = Marshmallow()

# Redis client for caching, session storage, and rate limiting
# Connection parameters will be configured during app initialization
redis_client = Redis(host=None, port=None, db=0, decode_responses=True)