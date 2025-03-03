"""
Service layer implementation for Interaction management, providing high-level CRUD operations with data validation,
site-scoping, audit logging, and caching. This service acts as a bridge between API controllers and the data layer,
enforcing business rules and maintaining data integrity for interaction records.
"""

from typing import Dict, List, Optional, Any, Union
from datetime import datetime

from ..models.interaction import Interaction  # Interaction model with validation capabilities
from ..repositories.interaction_repository import InteractionRepository  # Data access layer for interaction entities with site-scoping
from ..auth.site_context_service import SiteContextService  # Manages and enforces site-scoping for interactions
from ..auth.user_context_service import UserContextService  # Provides user context for creation and auditing
from .validation_service import InteractionValidator  # Provides validation for interaction data
from ..logging.audit_logger import AuditLogger  # Logs audit trails for interaction operations
from ..cache.cache_service import CacheService, get_cache_service  # Caches interaction data to improve performance
from ..models.interaction_history import CHANGE_TYPE_CREATE, CHANGE_TYPE_UPDATE, CHANGE_TYPE_DELETE  # Constants for operation type in history records
from ..utils.error_util import ValidationError, NotFoundError, SiteContextError  # Exceptions for validation failures
from ..logging.structured_logger import StructuredLogger  # Provides structured logging for operations

# Initialize logger
logger = StructuredLogger(__name__)

# Enable or disable caching
CACHE_ENABLED = True


class InteractionService:
    """
    Service class that handles business logic for interaction management, including validation, site-scoping,
    caching, and audit logging.
    """

    def __init__(self, interaction_repository: InteractionRepository, site_context_service: SiteContextService,
                 user_context_service: UserContextService, validator: InteractionValidator,
                 audit_logger: AuditLogger):
        """
        Initialize the interaction service with required dependencies.

        Args:
            interaction_repository: Repository for interaction data access
            site_context_service: Service for managing site context
            user_context_service: Service for accessing user context
            validator: Validator for interaction data
            audit_logger: Logger for audit trails
        """
        self._interaction_repository = interaction_repository
        self._site_context_service = site_context_service
        self._user_context_service = user_context_service
        self._validator = validator
        self._audit_logger = audit_logger
        self._cache_service = get_cache_service()  # Access the cache service singleton

        logger.info("InteractionService initialized")

    def create_interaction(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new interaction with validation, site-scoping, and audit logging.

        Args:
            data: Dictionary containing interaction data

        Returns:
            Created interaction data

        Raises:
            ValidationError: If data fails validation
            SiteContextError: If site context is invalid
        """
        logger.info("Attempting to create a new interaction", extra={'interaction_data': data})

        try:
            # Get current user ID from user_context_service
            user_id = self._user_context_service.get_current_user_id()
            if 'created_by' not in data:
                data['created_by'] = user_id

            # Get current site ID from site_context_service
            site_id = self._site_context_service.get_current_site_id()
            if 'site_id' not in data:
                data['site_id'] = site_id

            # Validate interaction data using validator.validate_create
            validated_data = self._validator.validate_create(data)

            # Create interaction using interaction_repository.create_interaction
            interaction = self._interaction_repository.create_interaction(validated_data)

            # Create audit log using audit_logger.log_interaction_history with CHANGE_TYPE_CREATE
            self._audit_logger.log_interaction_history(interaction, CHANGE_TYPE_CREATE)

            # Cache created interaction if CACHE_ENABLED
            if CACHE_ENABLED:
                self._cache_service.store_interaction(interaction.id, interaction.to_dict())

            logger.info(f"Successfully created interaction with ID {interaction.id}")

            # Return interaction data as dictionary
            return interaction.to_dict()

        except ValidationError as e:
            logger.error(f"Validation error during interaction creation: {e}", extra={'errors': e.details})
            raise
        except SiteContextError as e:
            logger.error(f"Site context error during interaction creation: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during interaction creation: {e}")
            raise

    def get_interaction(self, interaction_id: int) -> Dict[str, Any]:
        """
        Get an interaction by ID with site-scoping and caching.

        Args:
            interaction_id: ID of the interaction to retrieve

        Returns:
            Interaction data or None if not found

        Raises:
            NotFoundError: If interaction not found
            SiteContextError: If site context is invalid
        """
        logger.info(f"Attempting to retrieve interaction with ID {interaction_id}")

        try:
            # Check if interaction is in cache if CACHE_ENABLED
            if CACHE_ENABLED:
                cached_interaction = self._cache_service.get_interaction(interaction_id)
                if cached_interaction:
                    logger.debug(f"Retrieved interaction {interaction_id} from cache")
                    return cached_interaction

            # If not in cache, retrieve from repository with site-scoping
            interaction = self._interaction_repository.find_by_id(interaction_id)

            # Log data access audit event
            self._audit_logger.log_data_access(
                action='view',
                resource_type='interaction',
                resource_id=str(interaction_id)
            )

            # If interaction found, cache it if CACHE_ENABLED
            if CACHE_ENABLED:
                self._cache_service.store_interaction(interaction.id, interaction.to_dict())

            logger.info(f"Successfully retrieved interaction with ID {interaction_id}")

            # Return interaction data as dictionary if found, None otherwise
            return interaction.to_dict()

        except NotFoundError as e:
            logger.warning(f"Interaction with ID {interaction_id} not found: {e}")
            raise
        except SiteContextError as e:
            logger.error(f"Site context error during interaction retrieval: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during interaction retrieval: {e}")
            raise

    def get_interaction_by_id(self, interaction_id: int) -> Dict[str, Any]:
        """
        Get an interaction by ID with strict site-scoping and error handling.

        Args:
            interaction_id: ID of the interaction to retrieve

        Returns:
            Interaction data

        Raises:
            NotFoundError: If interaction not found
            SiteContextError: If site context is invalid
        """
        try:
            # Call get_interaction method
            result = self.get_interaction(interaction_id)

            # If result is None, raise NotFoundError
            if result is None:
                logger.warning(f"Interaction with ID {interaction_id} not found")
                raise NotFoundError(f"Interaction with ID {interaction_id} not found")

            logger.info(f"Successfully retrieved interaction with ID {interaction_id}")

            # Return interaction data as dictionary
            return result

        except NotFoundError as e:
            logger.warning(f"Interaction with ID {interaction_id} not found: {e}")
            raise
        except SiteContextError as e:
            logger.error(f"Site context error during interaction retrieval: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during interaction retrieval: {e}")
            raise

    def update_interaction(self, interaction_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing interaction with validation, site-scoping, and audit logging.

        Args:
            interaction_id: ID of the interaction to update
            data: Dictionary containing updated interaction data

        Returns:
            Updated interaction data

        Raises:
            ValidationError: If data fails validation
            NotFoundError: If interaction not found
            SiteContextError: If site context is invalid
        """
        logger.info(f"Attempting to update interaction with ID {interaction_id}", extra={'update_data': data})

        try:
            # Get existing interaction with site-scoping using repository
            existing_interaction = self._interaction_repository.find_by_id(interaction_id)

            # Store original state for audit purposes
            before_state = existing_interaction.to_dict()

            # Validate update data using validator.validate_update
            validated_data = self._validator.validate_update(data, before_state)

            # Update interaction using interaction_repository.update_interaction
            updated_interaction = self._interaction_repository.update_interaction(interaction_id, validated_data)

            # Create audit log using audit_logger.log_interaction_history with CHANGE_TYPE_UPDATE
            self._audit_logger.log_interaction_history(updated_interaction, CHANGE_TYPE_UPDATE, before_state)

            # Invalidate cache for updated interaction if CACHE_ENABLED
            if CACHE_ENABLED:
                self._cache_service.invalidate_interaction(updated_interaction.id, updated_interaction.site_id)
                self._cache_service.store_interaction(updated_interaction.id, updated_interaction.to_dict())

            logger.info(f"Successfully updated interaction with ID {interaction_id}")

            # Return updated interaction data as dictionary
            return updated_interaction.to_dict()

        except ValidationError as e:
            logger.error(f"Validation error during interaction update: {e}", extra={'errors': e.details})
            raise
        except NotFoundError as e:
            logger.warning(f"Interaction with ID {interaction_id} not found: {e}")
            raise
        except SiteContextError as e:
            logger.error(f"Site context error during interaction update: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during interaction update: {e}")
            raise

    def delete_interaction(self, interaction_id: int) -> bool:
        """
        Delete an interaction with site-scoping and audit logging.

        Args:
            interaction_id: ID of the interaction to delete

        Returns:
            True if successful, False otherwise

        Raises:
            NotFoundError: If interaction not found
            SiteContextError: If site context is invalid
        """
        logger.info(f"Attempting to delete interaction with ID {interaction_id}")

        try:
            # Get existing interaction with site-scoping using repository
            existing_interaction = self._interaction_repository.find_by_id(interaction_id)

            # Store state for audit purposes
            before_state = existing_interaction.to_dict()

            # Delete interaction using interaction_repository.delete
            success = self._interaction_repository.delete(interaction_id)

            # Create audit log using audit_logger.log_interaction_history with CHANGE_TYPE_DELETE
            self._audit_logger.log_interaction_history(existing_interaction, CHANGE_TYPE_DELETE, before_state)

            # Invalidate cache for deleted interaction if CACHE_ENABLED
            if CACHE_ENABLED:
                self._cache_service.invalidate_interaction(existing_interaction.id, existing_interaction.site_id)

            logger.info(f"Successfully deleted interaction with ID {interaction_id}")

            # Return True indicating successful deletion
            return success

        except NotFoundError as e:
            logger.warning(f"Interaction with ID {interaction_id} not found: {e}")
            raise
        except SiteContextError as e:
            logger.error(f"Site context error during interaction deletion: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during interaction deletion: {e}")
            raise

    def get_upcoming_interactions(self, limit: int) -> List[Dict]:
        """
        Get a list of upcoming interactions for the current site.

        Args:
            limit: Maximum number of interactions to return

        Returns:
            List of upcoming interaction records

        Raises:
            SiteContextError: If site context is invalid
        """
        logger.info(f"Attempting to retrieve {limit} upcoming interactions")

        try:
            # Validate site context using site_context_service
            self._site_context_service.requires_site_context()

            # Get upcoming interactions using interaction_repository.get_upcoming_interactions
            interactions = self._interaction_repository.get_upcoming_interactions(limit)

            # Log data access audit event
            self._audit_logger.log_data_access(
                action='list',
                resource_type='interaction',
                resource_id='upcoming'
            )

            logger.info(f"Successfully retrieved {len(interactions)} upcoming interactions")

            # Return list of interaction records as dictionaries
            return self._format_interaction_list(interactions)

        except SiteContextError as e:
            logger.error(f"Site context error during upcoming interaction retrieval: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during upcoming interaction retrieval: {e}")
            raise

    def get_recent_interactions(self, limit: int) -> List[Dict]:
        """
        Get a list of recent past interactions for the current site.

        Args:
            limit: Maximum number of interactions to return

        Returns:
            List of recent interaction records

        Raises:
            SiteContextError: If site context is invalid
        """
        logger.info(f"Attempting to retrieve {limit} recent interactions")

        try:
            # Validate site context using site_context_service
            self._site_context_service.requires_site_context()

            # Get recent interactions using interaction_repository.get_recent_interactions
            interactions = self._interaction_repository.get_recent_interactions(limit)

            # Log data access audit event
            self._audit_logger.log_data_access(
                action='list',
                resource_type='interaction',
                resource_id='recent'
            )

            logger.info(f"Successfully retrieved {len(interactions)} recent interactions")

            # Return list of interaction records as dictionaries
            return self._format_interaction_list(interactions)

        except SiteContextError as e:
            logger.error(f"Site context error during recent interaction retrieval: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during recent interaction retrieval: {e}")
            raise

    def _format_interaction(self, interaction: object) -> Dict[str, Any]:
        """
        Format an interaction model into a standardized dictionary.

        Args:
            interaction: Interaction model instance

        Returns:
            Formatted interaction data
        """
        # Convert interaction to dictionary using to_dict method
        interaction_data = interaction.to_dict()

        # Format datetime fields to ISO format
        # (This is already handled by the to_dict method, so no need to duplicate)

        # Include additional computed fields if needed
        # (No additional computed fields are needed at this time)

        return interaction_data

    def _format_interaction_list(self, interactions: List[object]) -> List[Dict[str, Any]]:
        """
        Format a list of interaction models into standardized dictionaries.

        Args:
            interactions: List of Interaction model instances

        Returns:
            List of formatted interaction dictionaries
        """
        # Initialize empty result list
        formatted_list = []

        # For each interaction in the list
        for interaction in interactions:
            # Format using _format_interaction method
            formatted_interaction = self._format_interaction(interaction)

            # Add formatted interaction to result list
            formatted_list.append(formatted_interaction)

        # Return the formatted list
        return formatted_list