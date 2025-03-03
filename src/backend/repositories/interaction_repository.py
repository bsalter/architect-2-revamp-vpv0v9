"""
Repository implementation for Interaction entities, providing data access operations with site-scoping,
search capabilities, and transaction management. Handles CRUD operations, specialized search methods,
and enforces site-based data isolation.
"""

from typing import Dict, List, Optional, Tuple, Any, Union
from datetime import datetime, timedelta

import sqlalchemy
from sqlalchemy import or_, and_, func, not_, desc, asc

from .base_repository import BaseRepository
from .connection_manager import ConnectionManager
from ..models.interaction import Interaction
from ..auth.site_context_service import SiteContextService
from ..utils.error_util import ValidationError, DatabaseError
from ..utils.enums import InteractionType, Timezone
from ..logging.structured_logger import StructuredLogger

# Initialize logger
logger = StructuredLogger(__name__)

class InteractionRepository(BaseRepository):
    """
    Repository for handling interaction data access with site-scoping, search functionality,
    and proper transaction management.
    """
    
    def __init__(self, connection_manager: ConnectionManager, site_context_service: SiteContextService):
        """
        Initialize the interaction repository with dependencies.
        
        Args:
            connection_manager: Connection manager for database transactions
            site_context_service: Service providing site context for the current user
        """
        # Initialize base repository with Interaction model and site_id column for scoping
        super().__init__(
            Interaction,
            site_column_name='site_id',
            connection_manager=connection_manager,
            get_current_site_id=site_context_service.get_current_site_id,
            apply_site_scope_to_query=site_context_service.apply_site_scope_to_query
        )
        
        # Store dependencies
        self._connection_manager = connection_manager
        self._site_context_service = site_context_service
        
        logger.info("InteractionRepository initialized")
    
    def validate_interaction(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate interaction data before saving to database.
        
        Args:
            data: Dictionary containing interaction data
            
        Returns:
            Validated interaction data
            
        Raises:
            ValidationError: If data fails validation
        """
        # Check required fields
        required_fields = ['title', 'type', 'lead', 'start_datetime', 'end_datetime', 'timezone', 'description']
        missing_fields = [field for field in required_fields if field not in data or data.get(field) is None]
        
        if missing_fields:
            error_msg = f"Missing required fields: {', '.join(missing_fields)}"
            logger.error(error_msg)
            raise ValidationError(error_msg)
        
        # Validate title length
        if not (5 <= len(data['title']) <= 100):
            error_msg = "Title must be between 5 and 100 characters"
            logger.error(error_msg)
            raise ValidationError(error_msg)
        
        # Validate interaction type
        if not InteractionType.is_valid(data['type']):
            error_msg = f"Invalid interaction type. Must be one of: {', '.join(InteractionType.get_values())}"
            logger.error(error_msg)
            raise ValidationError(error_msg)
        
        # Validate start and end dates
        start_datetime = data['start_datetime']
        end_datetime = data['end_datetime']
        
        if not isinstance(start_datetime, datetime) or not isinstance(end_datetime, datetime):
            error_msg = "Start and end dates must be datetime objects"
            logger.error(error_msg)
            raise ValidationError(error_msg)
        
        if end_datetime <= start_datetime:
            error_msg = "End time must be after start time"
            logger.error(error_msg)
            raise ValidationError(error_msg)
        
        # Validate timezone
        if not Timezone.is_valid(data['timezone']):
            error_msg = "Invalid timezone identifier"
            logger.error(error_msg)
            raise ValidationError(error_msg)
        
        # Description must not be empty
        if not data['description']:
            error_msg = "Description is required"
            logger.error(error_msg)
            raise ValidationError(error_msg)
        
        # Return validated data
        return data
    
    def create_interaction(self, data: Dict[str, Any]) -> Interaction:
        """
        Create a new interaction with validation.
        
        Args:
            data: Dictionary containing interaction data
            
        Returns:
            Newly created interaction
            
        Raises:
            ValidationError: If data fails validation
            DatabaseError: If database operation fails
        """
        try:
            # Validate interaction data
            validated_data = self.validate_interaction(data)
            
            # Set site_id from site context if not explicitly provided
            if 'site_id' not in validated_data:
                site_id = self._site_context_service.get_current_site_id()
                if not site_id:
                    error_msg = "Cannot determine site_id for interaction"
                    logger.error(error_msg)
                    raise ValidationError(error_msg)
                validated_data['site_id'] = site_id
            
            # Set created_by from user context if not explicitly provided
            if 'created_by' not in validated_data:
                user_id = self._site_context_service.get_current_user_id()
                if not user_id:
                    error_msg = "Cannot determine created_by for interaction"
                    logger.error(error_msg)
                    raise ValidationError(error_msg)
                validated_data['created_by'] = user_id
            
            # Create interaction using base repository method
            with self._connection_manager.transaction_context():
                interaction = super().create(validated_data)
            
            logger.info(f"Created interaction with ID {interaction.id} for site {interaction.site_id}")
            
            return interaction
        except (ValidationError, DatabaseError):
            # Re-raise ValidationError and DatabaseError
            raise
        except Exception as e:
            error_msg = f"Unexpected error creating interaction: {str(e)}"
            logger.error(error_msg)
            raise DatabaseError(error_msg, original_exception=e)
    
    def update_interaction(self, interaction_id: int, data: Dict[str, Any]) -> Interaction:
        """
        Update an existing interaction with validation.
        
        Args:
            interaction_id: ID of interaction to update
            data: Dictionary containing updated interaction data
            
        Returns:
            Updated interaction
            
        Raises:
            ValidationError: If data fails validation
            DatabaseError: If database operation fails
            NotFoundError: If interaction not found
        """
        try:
            # Get existing interaction (will raise NotFoundError if not found)
            # This automatically applies site-scoping
            interaction = self.find_by_id(interaction_id)
            
            # Create a merged data dictionary with existing data and updates
            merged_data = interaction.to_dict()
            for key, value in data.items():
                if key != 'id' and key != 'site_id':  # Protect id and site_id from changes
                    merged_data[key] = value
            
            # Validate the merged data
            validated_data = self.validate_interaction(merged_data)
            
            # Update interaction using base repository method
            with self._connection_manager.transaction_context():
                updated_interaction = super().update(interaction_id, validated_data)
            
            logger.info(f"Updated interaction with ID {interaction_id}")
            
            return updated_interaction
        except ValidationError:
            # Re-raise ValidationError
            raise
        except Exception as e:
            error_msg = f"Unexpected error updating interaction {interaction_id}: {str(e)}"
            logger.error(error_msg)
            raise DatabaseError(error_msg, original_exception=e)
    
    def find_by_date_range(self, start_date: datetime, end_date: datetime, 
                          page: int = 1, per_page: int = 20) -> Tuple[List[Interaction], int]:
        """
        Find interactions within a specific date range.
        
        Args:
            start_date: Start date for range
            end_date: End date for range
            page: Page number for pagination (1-indexed)
            per_page: Number of items per page
            
        Returns:
            Tuple of (list of interactions, total count)
            
        Raises:
            ValidationError: If date range is invalid
        """
        # Validate date range
        if not isinstance(start_date, datetime) or not isinstance(end_date, datetime):
            error_msg = "Start and end dates must be datetime objects"
            logger.error(error_msg)
            raise ValidationError(error_msg)
        
        if end_date < start_date:
            error_msg = "End date must be after start date"
            logger.error(error_msg)
            raise ValidationError(error_msg)
        
        try:
            # Get base query with site-scoping applied
            query = self.get_query()
            
            # Apply date range filter
            # Look for interactions that overlap with the provided date range
            query = query.filter(
                and_(
                    Interaction.start_datetime < end_date,
                    Interaction.end_datetime > start_date
                )
            )
            
            # Get total count before pagination
            total_count = query.count()
            
            # Apply pagination
            query = query.order_by(Interaction.start_datetime)
            query = query.offset((page - 1) * per_page).limit(per_page)
            
            # Execute query
            interactions = query.all()
            
            logger.debug(f"Found {total_count} interactions in date range {start_date} to {end_date}")
            
            return interactions, total_count
        except Exception as e:
            error_msg = f"Error finding interactions by date range: {str(e)}"
            logger.error(error_msg)
            raise DatabaseError(error_msg, original_exception=e)
    
    def find_by_type(self, interaction_type: str, page: int = 1, per_page: int = 20) -> Tuple[List[Interaction], int]:
        """
        Find interactions by type.
        
        Args:
            interaction_type: Type of interaction to find
            page: Page number for pagination (1-indexed)
            per_page: Number of items per page
            
        Returns:
            Tuple of (list of interactions, total count)
            
        Raises:
            ValidationError: If interaction type is invalid
        """
        # Validate interaction type
        if not InteractionType.is_valid(interaction_type):
            error_msg = f"Invalid interaction type. Must be one of: {', '.join(InteractionType.get_values())}"
            logger.error(error_msg)
            raise ValidationError(error_msg)
        
        try:
            # Get base query with site-scoping applied
            query = self.get_query()
            
            # Apply type filter
            query = query.filter(Interaction.type == interaction_type)
            
            # Get total count before pagination
            total_count = query.count()
            
            # Apply pagination and ordering
            query = query.order_by(Interaction.start_datetime)
            query = query.offset((page - 1) * per_page).limit(per_page)
            
            # Execute query
            interactions = query.all()
            
            logger.debug(f"Found {total_count} interactions of type {interaction_type}")
            
            return interactions, total_count
        except Exception as e:
            error_msg = f"Error finding interactions by type: {str(e)}"
            logger.error(error_msg)
            raise DatabaseError(error_msg, original_exception=e)
    
    def find_by_lead(self, lead: str, page: int = 1, per_page: int = 20) -> Tuple[List[Interaction], int]:
        """
        Find interactions by lead person.
        
        Args:
            lead: Lead person to search for
            page: Page number for pagination (1-indexed)
            per_page: Number of items per page
            
        Returns:
            Tuple of (list of interactions, total count)
            
        Raises:
            ValidationError: If lead parameter is empty
        """
        # Validate lead parameter
        if not lead:
            error_msg = "Lead parameter cannot be empty"
            logger.error(error_msg)
            raise ValidationError(error_msg)
        
        try:
            # Get base query with site-scoping applied
            query = self.get_query()
            
            # Apply lead filter with case-insensitive search
            query = query.filter(func.lower(Interaction.lead).like(f"%{lead.lower()}%"))
            
            # Get total count before pagination
            total_count = query.count()
            
            # Apply pagination and ordering
            query = query.order_by(Interaction.start_datetime)
            query = query.offset((page - 1) * per_page).limit(per_page)
            
            # Execute query
            interactions = query.all()
            
            logger.debug(f"Found {total_count} interactions with lead containing '{lead}'")
            
            return interactions, total_count
        except Exception as e:
            error_msg = f"Error finding interactions by lead: {str(e)}"
            logger.error(error_msg)
            raise DatabaseError(error_msg, original_exception=e)
    
    def search(self, search_term: str, page: int = 1, per_page: int = 20) -> Tuple[List[Interaction], int]:
        """
        Search interactions across all fields.
        
        Args:
            search_term: Search term to look for in all searchable fields
            page: Page number for pagination (1-indexed)
            per_page: Number of items per page
            
        Returns:
            Tuple of (list of interactions, total count)
        """
        if not search_term:
            error_msg = "Search term cannot be empty"
            logger.error(error_msg)
            raise ValidationError(error_msg)
        
        try:
            # Get base query with site-scoping applied
            query = self.get_query()
            
            # Apply search filter across multiple fields
            search_filter = or_(
                func.lower(Interaction.title).like(f"%{search_term.lower()}%"),
                func.lower(Interaction.lead).like(f"%{search_term.lower()}%"),
                func.lower(Interaction.location).like(f"%{search_term.lower()}%"),
                func.lower(Interaction.description).like(f"%{search_term.lower()}%"),
                func.lower(Interaction.notes).like(f"%{search_term.lower()}%")
            )
            query = query.filter(search_filter)
            
            # Get total count before pagination
            total_count = query.count()
            
            # Apply pagination and ordering
            query = query.order_by(Interaction.start_datetime)
            query = query.offset((page - 1) * per_page).limit(per_page)
            
            # Execute query
            interactions = query.all()
            
            logger.debug(f"Found {total_count} interactions matching search term '{search_term}'")
            
            return interactions, total_count
        except Exception as e:
            error_msg = f"Error searching interactions: {str(e)}"
            logger.error(error_msg)
            raise DatabaseError(error_msg, original_exception=e)
    
    def advanced_search(self, filters: Dict[str, Any], sort_by: str = None, 
                      sort_desc: bool = False, page: int = 1, per_page: int = 20) -> Tuple[List[Interaction], int]:
        """
        Advanced search with multiple criteria and sorting.
        
        Args:
            filters: Dictionary of filter criteria
            sort_by: Field to sort by
            sort_desc: Whether to sort in descending order
            page: Page number for pagination (1-indexed)
            per_page: Number of items per page
            
        Returns:
            Tuple of (list of interactions, total count)
        """
        try:
            # Get base query with site-scoping applied
            query = self.get_query()
            
            # Apply filters if provided
            if filters:
                # Title filter
                if 'title' in filters and filters['title']:
                    query = query.filter(func.lower(Interaction.title).like(f"%{filters['title'].lower()}%"))
                
                # Type filter
                if 'type' in filters and filters['type']:
                    if isinstance(filters['type'], list):
                        query = query.filter(Interaction.type.in_(filters['type']))
                    else:
                        query = query.filter(Interaction.type == filters['type'])
                
                # Lead filter
                if 'lead' in filters and filters['lead']:
                    query = query.filter(func.lower(Interaction.lead).like(f"%{filters['lead'].lower()}%"))
                
                # Date range filter
                if 'start_date' in filters and filters['start_date']:
                    if isinstance(filters['start_date'], datetime):
                        query = query.filter(Interaction.start_datetime >= filters['start_date'])
                
                if 'end_date' in filters and filters['end_date']:
                    if isinstance(filters['end_date'], datetime):
                        query = query.filter(Interaction.end_datetime <= filters['end_date'])
                
                # Location filter
                if 'location' in filters and filters['location']:
                    query = query.filter(func.lower(Interaction.location).like(f"%{filters['location'].lower()}%"))
                
                # Text search filter
                if 'text' in filters and filters['text']:
                    text_filter = or_(
                        func.lower(Interaction.title).like(f"%{filters['text'].lower()}%"),
                        func.lower(Interaction.description).like(f"%{filters['text'].lower()}%"),
                        func.lower(Interaction.notes).like(f"%{filters['text'].lower()}%")
                    )
                    query = query.filter(text_filter)
            
            # Get total count before sorting and pagination
            total_count = query.count()
            
            # Apply sorting if specified
            if sort_by and hasattr(Interaction, sort_by):
                sort_column = getattr(Interaction, sort_by)
                if sort_desc:
                    query = query.order_by(desc(sort_column))
                else:
                    query = query.order_by(asc(sort_column))
            else:
                # Default sorting by start_datetime
                query = query.order_by(Interaction.start_datetime)
            
            # Apply pagination
            query = query.offset((page - 1) * per_page).limit(per_page)
            
            # Execute query
            interactions = query.all()
            
            logger.debug(f"Advanced search found {total_count} interactions")
            
            return interactions, total_count
        except Exception as e:
            error_msg = f"Error performing advanced search: {str(e)}"
            logger.error(error_msg)
            raise DatabaseError(error_msg, original_exception=e)
    
    def get_upcoming_interactions(self, limit: int = 5) -> List[Interaction]:
        """
        Get upcoming interactions from current datetime.
        
        Args:
            limit: Maximum number of interactions to return
            
        Returns:
            List of upcoming interaction records
        """
        try:
            # Get current datetime
            now = datetime.utcnow()
            
            # Get base query with site-scoping applied
            query = self.get_query()
            
            # Filter for interactions that haven't started yet
            query = query.filter(Interaction.start_datetime > now)
            
            # Order by start time (ascending) and limit results
            query = query.order_by(Interaction.start_datetime).limit(limit)
            
            # Execute query
            interactions = query.all()
            
            logger.debug(f"Retrieved {len(interactions)} upcoming interactions")
            
            return interactions
        except Exception as e:
            error_msg = f"Error retrieving upcoming interactions: {str(e)}"
            logger.error(error_msg)
            raise DatabaseError(error_msg, original_exception=e)
    
    def get_recent_interactions(self, limit: int = 5) -> List[Interaction]:
        """
        Get recently past interactions.
        
        Args:
            limit: Maximum number of interactions to return
            
        Returns:
            List of recent interaction records
        """
        try:
            # Get current datetime
            now = datetime.utcnow()
            
            # Get base query with site-scoping applied
            query = self.get_query()
            
            # Filter for interactions that have already ended
            query = query.filter(Interaction.end_datetime < now)
            
            # Order by end time (descending) and limit results
            query = query.order_by(desc(Interaction.end_datetime)).limit(limit)
            
            # Execute query
            interactions = query.all()
            
            logger.debug(f"Retrieved {len(interactions)} recent interactions")
            
            return interactions
        except Exception as e:
            error_msg = f"Error retrieving recent interactions: {str(e)}"
            logger.error(error_msg)
            raise DatabaseError(error_msg, original_exception=e)
    
    def get_interactions_by_date(self, date, page: int = 1, per_page: int = 20) -> Tuple[List[Interaction], int]:
        """
        Get interactions for a specific date.
        
        Args:
            date: Date to get interactions for (datetime.date or datetime.datetime)
            page: Page number for pagination (1-indexed)
            per_page: Number of items per page
            
        Returns:
            Tuple of (list of interactions, total count)
        """
        try:
            # Convert date to datetime at start of day
            if isinstance(date, datetime):
                start_date = datetime(date.year, date.month, date.day, 0, 0, 0)
            else:
                start_date = datetime(date.year, date.month, date.day, 0, 0, 0)
            
            # Calculate end of day
            end_date = start_date + timedelta(days=1)
            
            # Use find_by_date_range method
            return self.find_by_date_range(start_date, end_date, page, per_page)
        except Exception as e:
            error_msg = f"Error retrieving interactions by date: {str(e)}"
            logger.error(error_msg)
            raise DatabaseError(error_msg, original_exception=e)