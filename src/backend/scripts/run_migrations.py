#!/usr/bin/env python
"""
Database Migration Script

This script executes database migrations for the Interaction Management System using Alembic.
It automates the execution of existing migrations to update the database schema to the
latest version, handling both online and offline migration modes with appropriate error
handling and logging.
"""

import os
import sys
import logging
import argparse
from alembic.config import Config  # alembic version 1.11.1
from alembic import command  # alembic version 1.11.1

from ..config import DATABASE_CONFIG
from ..migrations.env import run_migrations_online, run_migrations_offline
from ..utils.error_util import DatabaseError, log_error

# Configure logger for the migration script
logger = logging.getLogger(__name__)

# Define paths relative to the script location
ALEMBIC_CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'alembic.ini')
MIGRATIONS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'migrations')


def setup_logging():
    """Configure the logging for the migration script."""
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


def parse_arguments():
    """Parse command line arguments for the migration script."""
    parser = argparse.ArgumentParser(
        description='Run database migrations for the Interaction Management System.'
    )
    parser.add_argument(
        '--revision', '-r',
        default='head',
        help='Revision identifier to migrate to (default: head)'
    )
    parser.add_argument(
        '--sql',
        action='store_true',
        help='Generate SQL statements instead of executing migrations'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )
    parser.add_argument(
        '--downgrade',
        action='store_true',
        help='Downgrade instead of upgrade'
    )
    return parser.parse_args()


def get_alembic_config():
    """Load and configure Alembic configuration."""
    if not os.path.exists(ALEMBIC_CONFIG_PATH):
        raise FileNotFoundError(f"Alembic configuration file not found at: {ALEMBIC_CONFIG_PATH}")
    
    config = Config(ALEMBIC_CONFIG_PATH)
    
    # Override SQLAlchemy URL if specified in application config
    if 'SQLALCHEMY_DATABASE_URI' in DATABASE_CONFIG:
        config.set_main_option('sqlalchemy.url', DATABASE_CONFIG['SQLALCHEMY_DATABASE_URI'])
    
    return config


def run_migrations(revision, sql=False, downgrade=False):
    """
    Execute database migrations using Alembic.
    
    Args:
        revision (str): Revision identifier to migrate to
        sql (bool): If True, generate SQL statements instead of executing migrations
        downgrade (bool): If True, downgrade instead of upgrade
    
    Returns:
        bool: True if migrations executed successfully, False otherwise
    """
    try:
        config = get_alembic_config()
        
        logger.info(f"{'Downgrading' if downgrade else 'Upgrading'} database to revision: {revision}")
        
        if sql:
            # Generate SQL statements without executing migrations
            logger.info("Generating SQL statements (offline mode)")
            # For SQL generation, we use offline mode
            run_migrations_offline()
        else:
            # Execute migrations directly against the database
            if downgrade:
                command.downgrade(config, revision)
            else:
                command.upgrade(config, revision)
                
            # Online migrations are handled by Alembic command which internally
            # uses the run_migrations_online function from env.py
        
        logger.info("Migration completed successfully")
        return True
    
    except Exception as e:
        log_error(e, f"Migration failed: {str(e)}")
        return False


def main():
    """Main entry point for the script."""
    try:
        setup_logging()
        args = parse_arguments()
        
        if args.verbose:
            logger.setLevel(logging.DEBUG)
            logger.debug("Verbose mode enabled")
        
        logger.info("Starting database migration")
        success = run_migrations(args.revision, args.sql, args.downgrade)
        
        if not success:
            logger.error("Migration failed")
            return 1
        
        return 0
    
    except Exception as e:
        log_error(e, f"Unexpected error during migration: {str(e)}")
        return 1


if __name__ == '__main__':
    sys.exit(main())