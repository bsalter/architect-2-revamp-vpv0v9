"""
Alembic migration environment configuration for the Interaction Management System.

This file configures the migration environment for Alembic, establishing the connection
to the database, providing access to models for schema migration, and defining how migrations
should be run (online or offline). It serves as the bridge between SQLAlchemy models and
the Alembic migration tool.
"""

import logging
from alembic import context  # alembic version 1.11.1
from sqlalchemy import engine_from_config, pool  # sqlalchemy version 2.0.19
from sqlalchemy.engine.url import make_url  # sqlalchemy version 2.0.19

# Import Base declarative model for metadata
from ..models.base import Base
# Import db instance for model information
from ..extensions import db
# Import database configuration
from ..config import DATABASE_CONFIG
# Import all models to ensure they're discovered by Alembic
from .. import models

# Alembic configuration object
config = context.config

# Logger for migration operations
logger = logging.getLogger('alembic.env')

# Target metadata for the migrations - use the Base declarative metadata
target_metadata = Base.metadata

# Parse the database URL from the configuration
db_url = make_url(DATABASE_CONFIG['SQLALCHEMY_DATABASE_URI'])

def include_object(object_, name, type_, reflected, compare_to):
    """
    Filter function to determine which database objects should be included in
    migration operations.
    
    Args:
        object_: The database object
        name: Name of the object
        type_: Type of object (table, column, index, etc.)
        reflected: Whether the object was reflected from the database
        compare_to: Object being compared against, if any
        
    Returns:
        bool: True if object should be included, False otherwise
    """
    # Skip Alembic's own version table
    if type_ == 'table' and name == 'alembic_version':
        return False
    
    # Skip temporary or internal tables
    if type_ == 'table' and name.startswith('_'):
        return False
    
    # Include all other objects
    return True

def run_migrations_offline():
    """
    Run migrations in 'offline' mode, generating SQL scripts instead of
    executing them directly against the database.
    """
    # Get database URL from config or application
    url = config.get_main_option("sqlalchemy.url")
    if not url:
        url = str(db_url)
    
    # Configure migration context
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,
        compare_type=True,
    )
    
    # Generate SQL script
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    """
    Run migrations directly against the database in 'online' mode.
    """
    # Get engine configuration
    engine_config = config.get_section(config.config_ini_section)
    if engine_config is None:
        engine_config = {}
    
    # Set URL if not provided in Alembic config
    if 'sqlalchemy.url' not in engine_config:
        engine_config['sqlalchemy.url'] = str(db_url)
    
    # Create engine
    connectable = engine_from_config(
        engine_config,
        prefix='sqlalchemy.',
        poolclass=pool.NullPool,
    )
    
    # Connect to the database
    with connectable.connect() as connection:
        # Configure migration context with the connection
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_object=include_object,
            compare_type=True,
        )
        
        # Run migrations in a transaction
        with context.begin_transaction():
            context.run_migrations()

# Determine which migration function to run
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()