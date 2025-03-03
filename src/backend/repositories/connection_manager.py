"""
Database connection management for the Interaction Management System.

This module provides classes and utilities for managing database connections,
sessions, and transactions. It ensures consistent handling of database operations
with proper error handling, connection pooling, and transaction boundaries.
"""

from sqlalchemy.orm import Session  # sqlalchemy version 2.0.19
import sqlalchemy.exc  # sqlalchemy version 2.0.19
from typing import Any, Callable, Dict, List, Optional, TypeVar, cast  # standard library
from contextlib import contextmanager  # standard library
from functools import wraps  # standard library

from ..extensions import db
from ..config import DATABASE_CONFIG
from ..utils.error_util import DatabaseError
from ..logging.structured_logger import StructuredLogger

# Configure logger for database operations
logger = StructuredLogger('database')

# Type variable for the transaction decorator
T = TypeVar('T', bound=Callable[..., Any])


def transaction(func: T) -> T:
    """
    Decorator that wraps a function in a database transaction.
    
    This decorator provides transaction management for repository operations,
    handling commit/rollback automatically based on function execution result.
    
    Args:
        func: The function to wrap with transaction management
        
    Returns:
        Wrapped function with transaction management
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Create or get ConnectionManager instance
        # Check if the first argument is a class instance with a connection_manager
        connection_manager = None
        if args and hasattr(args[0], 'connection_manager'):
            connection_manager = args[0].connection_manager
        else:
            connection_manager = ConnectionManager()
            
        # Begin a transaction
        connection_manager.begin_transaction()
        
        try:
            # Execute the wrapped function
            result = func(*args, **kwargs)
            
            # Commit the transaction if no exception occurred
            connection_manager.commit()
            
            return result
        except Exception as e:
            # Rollback the transaction if an exception occurred
            connection_manager.rollback()
            
            # Re-raise the exception
            raise e
            
    return cast(T, wrapper)


class ConnectionManager:
    """
    Manages database connections and transactions for the application.
    
    This class provides methods for obtaining database sessions, executing transactions,
    and handling database connection pooling. It also includes error handling and logging
    for database operations.
    """
    
    def __init__(self, session: Optional[Session] = None):
        """
        Initializes the connection manager with optional custom session.
        
        Args:
            session: Optional SQLAlchemy session to use instead of default
        """
        self._session = session or db.session
        self._in_transaction = False
        logger.debug("ConnectionManager initialized")
        
    def get_session(self) -> Session:
        """
        Returns a database session for repository operations.
        
        Returns:
            Active database session
        """
        logger.debug("Retrieving database session")
        return self._session
        
    def begin_transaction(self) -> None:
        """
        Begin a new database transaction.
        
        Raises:
            DatabaseError: If there's an error starting the transaction
        """
        if self._in_transaction:
            logger.warning("Transaction already in progress")
            return
            
        try:
            self._session.begin()
            self._in_transaction = True
            logger.debug("Transaction started")
        except sqlalchemy.exc.SQLAlchemyError as e:
            logger.error(f"Error starting transaction: {str(e)}")
            raise DatabaseError("Failed to start database transaction", 
                               original_exception=e)
    
    def commit(self) -> None:
        """
        Commit the current transaction.
        
        Raises:
            DatabaseError: If there's an error committing the transaction
        """
        if not self._in_transaction:
            logger.warning("No transaction in progress to commit")
            return
            
        try:
            self._session.commit()
            self._in_transaction = False
            logger.debug("Transaction committed")
        except sqlalchemy.exc.SQLAlchemyError as e:
            logger.error(f"Error committing transaction: {str(e)}")
            raise DatabaseError("Failed to commit database transaction", 
                               original_exception=e)
    
    def rollback(self) -> None:
        """
        Rollback the current transaction.
        
        Raises:
            DatabaseError: If there's an error rolling back the transaction
        """
        if not self._in_transaction:
            logger.warning("No transaction in progress to rollback")
            return
            
        try:
            self._session.rollback()
            self._in_transaction = False
            logger.debug("Transaction rolled back")
        except sqlalchemy.exc.SQLAlchemyError as e:
            logger.error(f"Error rolling back transaction: {str(e)}")
            raise DatabaseError("Failed to rollback database transaction", 
                               original_exception=e)
    
    def close(self) -> None:
        """
        Close the database session.
        
        Raises:
            DatabaseError: If there's an error closing the session
        """
        # Rollback any active transaction first
        if self._in_transaction:
            self.rollback()
            
        try:
            self._session.close()
            logger.debug("Session closed")
        except sqlalchemy.exc.SQLAlchemyError as e:
            logger.error(f"Error closing session: {str(e)}")
            raise DatabaseError("Failed to close database session", 
                               original_exception=e)
    
    @contextmanager
    def transaction_context(self):
        """
        Context manager for database transactions.
        
        Provides a convenient way to wrap code in a transaction using a with statement.
        
        Example:
            with connection_manager.transaction_context():
                # Code that needs transactional behavior
        
        Yields:
            None
            
        Raises:
            Any exception that occurs during the transaction
        """
        self.begin_transaction()
        try:
            yield
            self.commit()
        except Exception as e:
            self.rollback()
            raise e
    
    def is_active(self) -> bool:
        """
        Check if the database session is active.
        
        Returns:
            True if session is active, False otherwise
        """
        return self._session is not None and bool(self._session.is_active)
    
    def is_in_transaction(self) -> bool:
        """
        Check if currently in an active transaction.
        
        Returns:
            True if in transaction, False otherwise
        """
        return self._in_transaction
    
    def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Execute a raw SQL query against the database.
        
        Allows execution of custom SQL queries when the ORM is not sufficient.
        
        Args:
            query: SQL query string
            params: Optional parameters for the query
            
        Returns:
            Query result as a list of dictionaries
            
        Raises:
            DatabaseError: If there's an error executing the query
        """
        try:
            # Execute the query with parameters
            result = self._session.execute(query, params or {})
            
            # Format result into a list of dictionaries
            columns = result.keys()
            formatted_result = [dict(zip(columns, row)) for row in result.fetchall()]
            
            return formatted_result
        except sqlalchemy.exc.SQLAlchemyError as e:
            logger.error(f"Error executing query: {str(e)}")
            raise DatabaseError("Failed to execute database query", 
                               original_exception=e)
    
    def ping(self) -> bool:
        """
        Check database connectivity with a simple query.
        
        Returns:
            True if connected, False otherwise
        """
        try:
            # Execute a simple SELECT 1 query to check connectivity
            self._session.execute("SELECT 1")
            return True
        except sqlalchemy.exc.SQLAlchemyError as e:
            logger.error(f"Database connectivity check failed: {str(e)}")
            return False