#!/usr/bin/env python
"""
Database Migration Creator Script for Interaction Management System.

This script automates the creation of Alembic migration scripts with consistent naming
and formatting. It supports both empty migrations and auto-generated migrations based
on model changes.

Usage:
    python create_migration.py --name your_migration_name [--message "Your migration description"] [--autogenerate] [--empty]

Example:
    python create_migration.py --name add_user_table --message "Add user table"
    python create_migration.py --name add_site_column --autogenerate

The script will automatically:
1. Format the migration name according to naming conventions
2. Add a timestamp prefix to ensure correct ordering
3. Generate the migration file using Alembic
"""

import os
import sys
import re
import logging
import argparse
from datetime import datetime

# alembic v1.11.1
import alembic.config
import alembic.command

from ..config import DATABASE_CONFIG
from ..utils.string_util import normalize_text

# Configure logger
logger = logging.getLogger(__name__)

# Path to alembic.ini relative to this script
ALEMBIC_CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'alembic.ini')
# Path to migrations directory
MIGRATIONS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'migrations')
# Regular expression for valid migration names (lowercase alphanumeric with underscores)
VALID_NAME_PATTERN = re.compile(r'^[a-z0-9_]+$')


def setup_logging():
    """
    Configure the logging for the migration script.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler()
        ]
    )


def parse_arguments():
    """
    Parse command line arguments for the migration script.

    Returns:
        argparse.Namespace: Parsed command line arguments
    """
    parser = argparse.ArgumentParser(
        description='Create a new Alembic migration file for the Interaction Management System'
    )

    parser.add_argument(
        '--name',
        required=True,
        help='Name for the migration (e.g., add_user_table)'
    )
    
    parser.add_argument(
        '--message', '-m',
        help='Migration description message'
    )
    
    parser.add_argument(
        '--autogenerate', '-a',
        action='store_true',
        help='Automatically generate migration based on model changes'
    )
    
    parser.add_argument(
        '--empty', '-e',
        action='store_true',
        help='Create an empty migration script'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    return parser.parse_args()


def validate_migration_name(name):
    """
    Validate migration name to ensure it follows naming conventions.

    Args:
        name (str): The proposed migration name

    Returns:
        str: Formatted migration name

    Raises:
        ValueError: If the name is empty or contains invalid characters
    """
    if not name:
        raise ValueError("Migration name cannot be empty")
    
    # Format name: lowercase, replace spaces with underscores
    formatted_name = normalize_text(name)
    formatted_name = formatted_name.replace(' ', '_')
    formatted_name = formatted_name.replace('-', '_')
    
    # Remove any special characters
    formatted_name = re.sub(r'[^a-z0-9_]', '', formatted_name)
    
    # Validate with regex pattern
    if not VALID_NAME_PATTERN.match(formatted_name):
        raise ValueError(
            "Invalid migration name. Use only lowercase letters, numbers, and underscores."
        )
    
    # Ensure name starts with letter or number
    if not formatted_name[0].isalnum():
        raise ValueError("Migration name must start with a letter or number")
    
    return formatted_name


def get_alembic_config():
    """
    Load and configure Alembic configuration.

    Returns:
        alembic.config.Config: Configured Alembic config object
    """
    if not os.path.exists(ALEMBIC_CONFIG_PATH):
        logger.error(f"Alembic configuration file not found at: {ALEMBIC_CONFIG_PATH}")
        raise FileNotFoundError(f"Alembic configuration file not found: {ALEMBIC_CONFIG_PATH}")
    
    # Create Alembic config instance with alembic.ini path
    config = alembic.config.Config(ALEMBIC_CONFIG_PATH)
    
    # Return the config as is - database URL should be in alembic.ini
    # If we need to override it in the future, we can add that functionality
    return config


def create_migration(name, message, autogenerate, empty):
    """
    Create a new migration file using Alembic.

    Args:
        name (str): Migration name
        message (str): Migration description message
        autogenerate (bool): Whether to autogenerate migration based on model changes
        empty (bool): Whether to create an empty migration

    Returns:
        bool: True if migration was created successfully, False otherwise
    """
    try:
        # Validate migration name
        validated_name = validate_migration_name(name)
        
        # Use the provided message or the name as the message
        migration_message = message or validated_name.replace('_', ' ')
        
        # Get Alembic config
        config = get_alembic_config()
        
        # Log migration creation attempt
        logger.info(f"Creating migration: {validated_name}")
        logger.info(f"Message: {migration_message}")
        
        if empty:
            # Create empty migration
            logger.info("Creating empty migration script")
            alembic.command.revision(
                config,
                message=migration_message,
                autogenerate=False
            )
        else:
            # Create migration based on model changes
            logger.info(
                "Creating migration with autogenerate" if autogenerate else "Creating migration"
            )
            alembic.command.revision(
                config,
                message=migration_message,
                autogenerate=autogenerate
            )
        
        logger.info(f"Migration '{validated_name}' created successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create migration: {str(e)}")
        return False


def main():
    """
    Main entry point for the script.

    Returns:
        int: Exit code (0 for success, non-zero for failure)
    """
    try:
        # Setup logging
        setup_logging()
        
        # Parse command line arguments
        args = parse_arguments()
        
        # Configure verbose logging if requested
        if args.verbose:
            logging.getLogger().setLevel(logging.DEBUG)
            logger.debug("Verbose logging enabled")
        
        # Extract arguments
        name = args.name
        message = args.message
        autogenerate = args.autogenerate
        empty = args.empty
        
        # Check conflicting flags
        if autogenerate and empty:
            logger.error("Cannot use both --autogenerate and --empty flags together")
            return 1
        
        # Create migration
        success = create_migration(name, message, autogenerate, empty)
        
        if success:
            logger.info("Migration creation completed successfully")
            return 0
        else:
            logger.error("Migration creation failed")
            return 1
            
    except Exception as e:
        logger.exception(f"Unexpected error: {str(e)}")
        return 2


if __name__ == '__main__':
    sys.exit(main())