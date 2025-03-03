"""
Scripts package for the Interaction Management System.

This package provides utility scripts for database operations and system maintenance, including:

- Database migrations using Alembic to manage schema versions and upgrades
- Data seeding utilities for development and testing environments
- API documentation generation

The package implements the migration strategy defined in the system's schema design, 
supporting versioned migrations with forward and backward capability.

Available functions:
- create_migration: Create a new Alembic migration script
- run_upgrade: Upgrade the database schema to a specific revision
- run_downgrade: Downgrade the database schema to a specific revision
- check_migrations: Verify the status of database migrations
- get_alembic_config: Get Alembic configuration object
"""

import logging  # standard library

# Import functions from script modules
from .create_migration import create_migration
from .run_migrations import run_upgrade, run_downgrade, check_migrations, get_alembic_config

# Configure logger for the scripts package
logger = logging.getLogger(__name__)

# Define the symbols to export from this package
__all__ = ['create_migration', 'run_upgrade', 'run_downgrade', 'check_migrations', 'get_alembic_config']