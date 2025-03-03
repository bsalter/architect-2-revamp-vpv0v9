"""
Base repository implementation for the Interaction Management System.

This module provides a BaseRepository class that all specific repositories inherit from,
offering common functionality for database operations with site-scoping, error handling,
and transaction management.
"""

from typing import Any, Dict, List, Optional, Type, Callable, Tuple, Union
import sqlalchemy
from sqlalchemy.orm import Query
from sqlalchemy import exc as sql_exc

from ..extensions import db, session, Model
from .connection_manager import ConnectionManager
from ..utils.error_util import DatabaseError, NotFoundError, SiteContextError
from ..logging.structured_logger import StructuredLogger

# Configure logger
logger = StructuredLogger(__name__)

class BaseRepository:
    """
    Abstract base repository class that provides common database operation functionality with site-scoping.
    
    This class serves as a foundation for all repository implementations, providing standard
    CRUD operations with automatic site-scoping to maintain data isolation between sites.
    """
    
    def __init__(
        self, 
        model_class: Type[Model],
        site_column_name: str = 'site_id',
        connection_manager: Optional[ConnectionManager] = None,
        get_current_site_id: Optional[Callable[[], int]] = None,
        apply_site_scope_to_query: Optional[Callable[[Query], Query]] = None
    ):
        """
        Initialize the repository with model class, site column, and dependencies.
        
        Args:
            model_class: SQLAlchemy model class this repository handles
            site_column_name: Column name used for site association
            connection_manager: Optional ConnectionManager instance
            get_current_site_id: Optional function to get current site ID
            apply_site_scope_to_query: Optional function to apply site scope to query
        """
        self._model_class = model_class
        self._site_column_name = site_column_name
        
        # Use provided connection manager or create a new one
        self._connection_manager = connection_manager or ConnectionManager()
        
        # Use provided site ID function or use default that raises NotImplementedError
        self._get_current_site_id = get_current_site_id or (lambda: None)
        
        # Use provided site scope filter or use default implementation
        self._apply_site_scope_to_query = apply_site_scope_to_query or self._default_site_scope_filter
        
        # Get database session from connection manager
        self._session = self._connection_manager.get_session()
        
        logger.debug(f"Initialized repository for {model_class.__name__}")
    
    def get_session(self):
        """
        Get the current database session.
        
        Returns:
            SQLAlchemy session object
        """
        return self._connection_manager.get_session()
    
    def _default_site_scope_filter(self, query: Query) -> Query:
        """
        Default implementation for site scope filtering when no custom implementation is provided.
        
        Args:
            query: SQLAlchemy query object
            
        Returns:
            Query with site scope filter applied
        """
        site_id = self._get_current_site_id()
        
        # If site_id is None, return query unchanged
        if site_id is None:
            return query
        
        # Apply site filter
        return query.filter(getattr(self._model_class, self._site_column_name) == site_id)
    
    def get_query(self) -> Query:
        """
        Get a query object with site-scoping applied.
        
        Returns:
            SQLAlchemy query object with site-scoping filter applied
        """
        query = self._session.query(self._model_class)
        return self._apply_site_scope_to_query(query)
    
    def get_by_id(self, id: int) -> Optional[Model]:
        """
        Get a model instance by ID with site-scoping.
        
        Args:
            id: Primary key of the model to retrieve
            
        Returns:
            Model instance or None if not found or not in user's site scope
        """
        query = self.get_query()
        result = query.filter(self._model_class.id == id).first()
        
        if result:
            logger.debug(f"Found {self._model_class.__name__} with ID {id}")
        else:
            logger.debug(f"{self._model_class.__name__} with ID {id} not found")
            
        return result
    
    def find_by_id(self, id: int) -> Model:
        """
        Find a model instance by ID with site-scoping, raising NotFoundError if not found.
        
        Args:
            id: Primary key of the model to retrieve
            
        Returns:
            Model instance
            
        Raises:
            NotFoundError: If the entity is not found or not in user's site scope
        """
        result = self.get_by_id(id)
        
        if not result:
            raise NotFoundError(
                f"{self._model_class.__name__} with ID {id} not found",
                resource_type=self._model_class.__name__,
                resource_id=id
            )
            
        return result
    
    def get_all(
        self, 
        filters: Optional[Dict[str, Any]] = None,
        page: int = 1,
        per_page: int = 20,
        sort_by: Optional[str] = None,
        sort_desc: bool = False
    ) -> Tuple[List[Model], int]:
        """
        Get all model instances within user's site scope with optional filtering.
        
        Args:
            filters: Optional dictionary of filter criteria
            page: Page number to retrieve (1-indexed)
            per_page: Number of items per page
            sort_by: Column name to sort by
            sort_desc: True for descending sort, False for ascending
            
        Returns:
            Tuple containing list of model instances and total count
        """
        query = self.get_query()
        
        # Apply any additional filters
        if filters:
            query = self.apply_filters(query, filters)
        
        # Apply sorting if specified
        if sort_by and hasattr(self._model_class, sort_by):
            sort_column = getattr(self._model_class, sort_by)
            if sort_desc:
                query = query.order_by(sort_column.desc())
            else:
                query = query.order_by(sort_column.asc())
        
        # Get total count before pagination
        total_count = query.count()
        
        # Apply pagination
        query = query.offset((page - 1) * per_page).limit(per_page)
        
        # Execute query
        results = query.all()
        
        logger.debug(f"Retrieved {len(results)} {self._model_class.__name__} records (page {page}, total {total_count})")
        
        return results, total_count
    
    def create(self, data: Dict[str, Any]) -> Model:
        """
        Create a new model instance with automatic site association.
        
        Args:
            data: Dictionary of model attributes
            
        Returns:
            Newly created model instance
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            # Get current site ID
            site_id = self._get_current_site_id()
            
            # Add site ID to data
            data[self._site_column_name] = site_id
            
            # Create new model instance
            instance = self._model_class(**data)
            
            # Add to session
            self._session.add(instance)
            
            # Commit within transaction context
            with self._connection_manager.transaction_context():
                self._session.commit()
                # Refresh to get any database-generated values
                self._session.refresh(instance)
            
            logger.info(f"Created {self._model_class.__name__} with ID {instance.id}")
            
            return instance
            
        except Exception as e:
            self._handle_db_error(e, "create")
    
    def update(self, id: int, data: Dict[str, Any]) -> Model:
        """
        Update an existing model instance with site-scoping validation.
        
        Args:
            id: Primary key of the model to update
            data: Dictionary of updated attributes
            
        Returns:
            Updated model instance
            
        Raises:
            NotFoundError: If entity not found or not in user's site scope
            DatabaseError: If database operation fails
        """
        try:
            # Find instance with site-scoping
            instance = self.find_by_id(id)
            
            # Update attributes
            for key, value in data.items():
                if hasattr(instance, key):
                    setattr(instance, key, value)
            
            # Commit within transaction context
            with self._connection_manager.transaction_context():
                self._session.commit()
            
            logger.info(f"Updated {self._model_class.__name__} with ID {id}")
            
            return instance
            
        except NotFoundError:
            # Re-raise NotFoundError from find_by_id
            raise
        except Exception as e:
            self._handle_db_error(e, "update")
    
    def delete(self, id: int) -> bool:
        """
        Delete a model instance by ID with site-scoping validation.
        
        Args:
            id: Primary key of the model to delete
            
        Returns:
            True if deleted successfully, False if not found
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            # Find instance with site-scoping
            instance = self.get_by_id(id)
            
            # If not found, return False
            if not instance:
                logger.debug(f"{self._model_class.__name__} with ID {id} not found for deletion")
                return False
            
            # Delete the instance
            self._session.delete(instance)
            
            # Commit within transaction context
            with self._connection_manager.transaction_context():
                self._session.commit()
            
            logger.info(f"Deleted {self._model_class.__name__} with ID {id}")
            
            return True
            
        except Exception as e:
            self._handle_db_error(e, "delete")
    
    def hard_delete(self, id: int) -> bool:
        """
        Permanently delete a model instance by ID with site-scoping validation.
        
        This method raises NotFoundError if the entity is not found, unlike delete().
        
        Args:
            id: Primary key of the model to delete
            
        Returns:
            True if deleted successfully
            
        Raises:
            NotFoundError: If entity not found or not in user's site scope
            DatabaseError: If database operation fails
        """
        try:
            # Find instance with site-scoping (raises NotFoundError if not found)
            instance = self.find_by_id(id)
            
            # Delete the instance
            self._session.delete(instance)
            
            # Commit within transaction context
            with self._connection_manager.transaction_context():
                self._session.commit()
            
            logger.info(f"Hard deleted {self._model_class.__name__} with ID {id}")
            
            return True
            
        except NotFoundError:
            # Re-raise NotFoundError from find_by_id
            raise
        except Exception as e:
            self._handle_db_error(e, "hard_delete")
    
    def apply_filters(self, query: Query, filters: Dict[str, Any]) -> Query:
        """
        Apply dictionary filters to a query.
        
        Args:
            query: SQLAlchemy query object
            filters: Dictionary of filter criteria
            
        Returns:
            SQLAlchemy query with filters applied
        """
        if not filters:
            return query
            
        for key, value in filters.items():
            # Skip if key is not a column in model
            if not hasattr(self._model_class, key):
                continue
                
            column = getattr(self._model_class, key)
            
            # Apply appropriate filter based on value type
            if value is None:
                query = query.filter(column.is_(None))
            elif isinstance(value, list):
                query = query.filter(column.in_(value))
            elif isinstance(value, dict):
                # Handle operators like eq, gt, lt, etc.
                for op, op_value in value.items():
                    if op == 'eq':
                        query = query.filter(column == op_value)
                    elif op == 'neq':
                        query = query.filter(column != op_value)
                    elif op == 'gt':
                        query = query.filter(column > op_value)
                    elif op == 'gte':
                        query = query.filter(column >= op_value)
                    elif op == 'lt':
                        query = query.filter(column < op_value)
                    elif op == 'lte':
                        query = query.filter(column <= op_value)
                    elif op == 'like':
                        query = query.filter(column.like(f'%{op_value}%'))
            else:
                # Simple equality
                query = query.filter(column == value)
                
        return query
    
    def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Count model instances with optional filtering and site-scoping.
        
        Args:
            filters: Optional dictionary of filter criteria
            
        Returns:
            Count of matching records within site scope
        """
        query = self.get_query()
        
        # Apply any additional filters
        if filters:
            query = self.apply_filters(query, filters)
        
        # Return count
        return query.count()
    
    def exists(self, filters: Dict[str, Any]) -> bool:
        """
        Check if any instances match the criteria within site scope.
        
        Args:
            filters: Dictionary of filter criteria
            
        Returns:
            True if any matching records exist within site scope
        """
        query = self.get_query()
        
        # Apply filters
        query = self.apply_filters(query, filters)
        
        # Check if any records exist
        return self._session.query(query.exists()).scalar()
    
    def _handle_db_error(self, e: Exception, operation: str) -> None:
        """
        Handle database errors with proper logging and exception translation.
        
        Args:
            e: The exception that occurred
            operation: The operation being performed
            
        Raises:
            DatabaseError: Translated exception with detailed message
        """
        # Log the error
        logger.error(f"Database error during {operation} operation on {self._model_class.__name__}: {str(e)}")
        
        # Translate exception to appropriate custom exception
        if isinstance(e, sql_exc.IntegrityError):
            # Handle integrity errors like unique constraint violations
            error_message = f"Integrity constraint violated while performing {operation} operation"
            details = {"error": str(e)}
            raise DatabaseError(error_message, details=details, original_exception=e)
        elif isinstance(e, sql_exc.DataError):
            # Handle data errors like invalid data type
            error_message = f"Invalid data error while performing {operation} operation"
            details = {"error": str(e)}
            raise DatabaseError(error_message, details=details, original_exception=e)
        elif isinstance(e, sql_exc.OperationalError):
            # Handle operational errors like connection issues
            error_message = f"Database operation error while performing {operation} operation"
            details = {"error": str(e)}
            raise DatabaseError(error_message, details=details, original_exception=e)
        elif isinstance(e, DatabaseError):
            # Re-raise DatabaseError
            raise e
        else:
            # Handle other exceptions
            error_message = f"Unexpected error during {operation} operation"
            details = {"error": str(e), "type": e.__class__.__name__}
            raise DatabaseError(error_message, details=details, original_exception=e)