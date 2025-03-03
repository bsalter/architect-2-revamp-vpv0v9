"""
Configuration module for the Interaction Management System backend.

This module provides configuration settings for different environments (development,
staging, production) and utilities for accessing environment variables. It uses
python-dotenv to load environment variables from a .env file if present.

Environment-specific configurations inherit from BaseConfig to ensure consistent
settings across environments while allowing for customization where needed.
"""

import os  # standard library
import logging
from typing import Dict, Any, Optional  # standard library
from datetime import timedelta

# python-dotenv v1.0.0
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# Global settings from environment variables
ENV = os.getenv('FLASK_ENV', 'development')
DEBUG = os.getenv('DEBUG', 'True') == 'True'
SECRET_KEY = os.getenv('SECRET_KEY', 'dev_secret_key_change_in_production')
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')


def get_env_var(name: str, default: Optional[str] = None) -> str:
    """
    Retrieves an environment variable with a fallback default value.

    Args:
        name: Name of the environment variable
        default: Default value to return if environment variable is not set

    Returns:
        Value of the environment variable or default if not set
    """
    value = os.getenv(name, default)
    if value is None:
        logging.warning(f"Required environment variable {name} is not set!")
    return value


def build_database_url() -> str:
    """
    Builds PostgreSQL database URL from individual environment variables.

    Returns:
        Complete database URL for SQLAlchemy connection
    """
    db_user = get_env_var('DB_USER', 'postgres')
    db_password = get_env_var('DB_PASSWORD', 'postgres')
    db_host = get_env_var('DB_HOST', 'localhost')
    db_port = get_env_var('DB_PORT', '5432')
    db_name = get_env_var('DB_NAME', 'interactions')
    
    return f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"


class BaseConfig:
    """Base configuration class with common settings for all environments."""
    
    # Flask settings
    DEBUG = DEBUG
    SECRET_KEY = SECRET_KEY
    LOG_LEVEL = LOG_LEVEL
    
    # SQLAlchemy settings
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # JWT settings
    JWT_COOKIE_SECURE = True
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=30)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=7)
    
    # Security settings
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # CSRF protection
    WTF_CSRF_ENABLED = True
    
    # Rate limiting
    RATELIMIT_DEFAULT = "300/minute"
    RATELIMIT_STRATEGY = "fixed-window"
    RATELIMIT_STORAGE_URL = get_env_var('REDIS_URL', 'redis://localhost:6379/0')


class DevelopmentConfig(BaseConfig):
    """Configuration settings for development environment."""
    
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = get_env_var('DATABASE_URL', build_database_url())
    JWT_COOKIE_SECURE = False  # Allow HTTP in development
    LOG_LEVEL = 'DEBUG'
    
    # Add development-specific settings
    SQLALCHEMY_ECHO = True  # Log SQL queries


class StagingConfig(BaseConfig):
    """Configuration settings for staging environment."""
    
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = get_env_var('DATABASE_URL', build_database_url())
    JWT_COOKIE_SECURE = True  # Require HTTPS
    LOG_LEVEL = 'INFO'


class ProductionConfig(BaseConfig):
    """Configuration settings for production environment."""
    
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = get_env_var('DATABASE_URL', build_database_url())
    JWT_COOKIE_SECURE = True  # Require HTTPS
    LOG_LEVEL = 'WARNING'
    
    # Stricter security settings for production
    RATELIMIT_DEFAULT = "100/minute"
    SESSION_COOKIE_SAMESITE = 'Strict'


class TestConfig(BaseConfig):
    """Configuration settings for testing environment."""
    
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = get_env_var(
        'TEST_DATABASE_URL', 
        'postgresql://postgres:postgres@localhost:5432/interactions_test'
    )
    JWT_COOKIE_SECURE = False  # Allow HTTP in testing
    WTF_CSRF_ENABLED = False  # Disable CSRF in testing


# Mapping of environment names to config classes
CONFIG = {
    'development': DevelopmentConfig,
    'staging': StagingConfig,
    'production': ProductionConfig,
    'testing': TestConfig,
}

# Database-specific configuration
DATABASE_CONFIG = {
    'pool_size': int(get_env_var('DB_POOL_SIZE', '10')),
    'max_overflow': int(get_env_var('DB_MAX_OVERFLOW', '20')),
    'pool_timeout': int(get_env_var('DB_POOL_TIMEOUT', '30')),
    'pool_recycle': int(get_env_var('DB_POOL_RECYCLE', '1800')),
    'echo': ENV == 'development',  # Log SQL queries in development
}

# Redis cache configuration
REDIS_CONFIG = {
    'host': get_env_var('REDIS_HOST', 'localhost'),
    'port': int(get_env_var('REDIS_PORT', '6379')),
    'db': int(get_env_var('REDIS_DB', '0')),
    'password': get_env_var('REDIS_PASSWORD', None),
    'ssl': get_env_var('REDIS_SSL', 'False') == 'True',
    'socket_timeout': int(get_env_var('REDIS_SOCKET_TIMEOUT', '5')),
    'socket_connect_timeout': int(get_env_var('REDIS_SOCKET_CONNECT_TIMEOUT', '5')),
    'retry_on_timeout': get_env_var('REDIS_RETRY_ON_TIMEOUT', 'True') == 'True',
}

# Auth0 configuration
AUTH0_CONFIG = {
    'domain': get_env_var('AUTH0_DOMAIN', 'your-domain.auth0.com'),
    'api_audience': get_env_var('AUTH0_API_AUDIENCE', 'your-audience'),
    'client_id': get_env_var('AUTH0_CLIENT_ID', 'your-client-id'),
    'client_secret': get_env_var('AUTH0_CLIENT_SECRET', 'your-client-secret'),
    'algorithms': ['RS256'],
}

# CORS configuration
CORS_CONFIG = {
    'origins': get_env_var('CORS_ORIGINS', '*').split(','),
    'methods': ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
    'allow_headers': [
        'Content-Type', 
        'Authorization', 
        'X-Requested-With',
        'X-CSRF-Token',
    ],
    'expose_headers': [
        'Content-Type',
        'X-RateLimit-Limit',
        'X-RateLimit-Remaining',
        'X-RateLimit-Reset',
    ],
    'supports_credentials': True,
    'max_age': 600,  # 10 minutes
}