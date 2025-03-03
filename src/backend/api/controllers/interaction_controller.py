# src/backend/api/controllers/interaction_controller.py
"""
Flask API controller that handles HTTP endpoints for Interaction CRUD operations and search functionality.
Provides routes for creating, retrieving, updating, and deleting interactions, as well as searching and
filtering interactions to power the Finder interface.
"""

from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime
import marshmallow  # marshmallow==3.20.1
from http import HTTPStatus  # standard library

from flask import Blueprint, request, current_app  # flask==2.3.2

from ..schemas.interaction_schemas import InteractionCreateSchema, InteractionUpdateSchema, InteractionResponseSchema, InteractionDetailSchema, InteractionListSchema
from ..helpers.response import success_response, created_response, no_content_response, error_response, validation_error_response, not_found_response, paginated_response
from ..helpers.pagination import get_pagination_info
from ...services.interaction_service import InteractionService
from ...services.search_service import SearchService
from ...auth.site_context_service import SiteContextService
from ...auth.user_context_service import UserContextService
from ...utils.error_util import ValidationError, NotFoundError, SiteContextError
from ...logging.structured_logger import StructuredLogger  # StructuredLogger
# Initialize structured logger
logger = StructuredLogger(__name__)

# Create Flask Blueprint
interaction_blueprint = Blueprint('interactions', __name__)


@interaction_blueprint.route('/interactions', methods=['GET'])
def get_interactions() -> Tuple[Dict[str, Any], int]:
    """
    Endpoint to retrieve a paginated list of interactions with optional search parameters.

    Returns:
        tuple: JSON response with interaction list and HTTP status code
    """
    try:
        # Extract search query parameter from request
        search_query = request.args.get('search')

        # Extract pagination parameters using get_pagination_info()
        page, page_size = get_pagination_info()

        # If search query provided, use SearchService.search()
        if search_query:
            interactions, total = SearchService(InteractionService, SiteContextService).search(search_query, page, page_size)
        # If no search query, use InteractionService.get_interactions()
        else:
            interactions, total = InteractionService(InteractionService, SiteContextService, UserContextService, InteractionCreateSchema, StructuredLogger).get_interactions(page, page_size)

        # Serialize results using InteractionListSchema
        interaction_list = InteractionListSchema().dump({'interactions': interactions, 'total': total})

        # Return paginated_response with results
        return paginated_response(items=interaction_list['interactions'], total=interaction_list['total'], page=page, page_size=page_size)

    except ValidationError as e:
        # Handle ValidationError with validation_error_response
        return validation_error_response(errors=e.details, message=e.message)
    except SiteContextError as e:
        # Handle SiteContextError with appropriate error response
        return error_response(message=e.message, error_type=e.error_type, status_code=HTTPStatus.FORBIDDEN)
    except Exception as e:
        # Handle unexpected errors with server_error_response
        logger.error(f"Unexpected error in get_interactions: {e}")
        return error_response(message="An unexpected error occurred", error_type=ErrorType.SERVER, status_code=HTTPStatus.INTERNAL_SERVER_ERROR)
    finally:
        # Log all requests and responses
        logger.info("get_interactions request completed")


@interaction_blueprint.route('/interactions/<int:interaction_id>', methods=['GET'])
def get_interaction(interaction_id: int) -> Tuple[Dict[str, Any], int]:
    """
    Endpoint to retrieve a single interaction by ID.

    Args:
        interaction_id (int): The ID of the interaction to retrieve

    Returns:
        tuple: JSON response with interaction data and HTTP status code
    """
    try:
        # Log request with interaction ID
        logger.info(f"Attempting to retrieve interaction with ID: {interaction_id}")

        # Try to get interaction using InteractionService.get_interaction_by_id()
        interaction = InteractionService(InteractionService, SiteContextService, UserContextService, InteractionCreateSchema, StructuredLogger).get_interaction_by_id(interaction_id)

        # Serialize result using InteractionDetailSchema
        interaction_data = InteractionDetailSchema().dump(interaction)

        # Return success_response with interaction data
        return success_response(data=interaction_data, message="Interaction retrieved successfully")

    except NotFoundError as e:
        # Handle NotFoundError with not_found_response
        return not_found_response(resource_type="interaction", resource_id=str(interaction_id))
    except SiteContextError as e:
        # Handle SiteContextError with appropriate error response
        return error_response(message=e.message, error_type=e.error_type, status_code=HTTPStatus.FORBIDDEN)
    except Exception as e:
        # Handle unexpected errors with server_error_response
        logger.error(f"Unexpected error in get_interaction: {e}")
        return error_response(message="An unexpected error occurred", error_type=ErrorType.SERVER, status_code=HTTPStatus.INTERNAL_SERVER_ERROR)
    finally:
        # Log response status
        logger.info(f"get_interaction request completed for interaction ID: {interaction_id}")


@interaction_blueprint.route('/interactions', methods=['POST'])
def create_interaction() -> Tuple[Dict[str, Any], int]:
    """
    Endpoint to create a new interaction.

    Returns:
        tuple: JSON response with created interaction data and HTTP status code
    """
    try:
        # Log request with request data
        logger.info(f"Attempting to create interaction with data: {request.json}")

        # Validate request JSON data using InteractionCreateSchema
        validated_data = InteractionCreateSchema().load(request.json)

        # Get current user ID using UserContextService
        user_id = UserContextService(UserRepository, InteractionService).get_current_user_id()
        validated_data['created_by'] = user_id

        # Get current site ID using SiteContextService
        site_id = SiteContextService(UserContextService, InteractionService).get_current_site_id()
        validated_data['site_id'] = site_id

        # Create interaction using InteractionService.create_interaction()
        interaction = InteractionService(InteractionService, SiteContextService, UserContextService, InteractionCreateSchema, StructuredLogger).create_interaction(validated_data)

        # Serialize created interaction using InteractionResponseSchema
        interaction_data = InteractionResponseSchema().dump(interaction)

        # Return created_response with interaction data
        return created_response(data=interaction_data, message="Interaction created successfully")

    except ValidationError as e:
        # Handle ValidationError with validation_error_response
        return validation_error_response(errors=e.details, message=e.message)
    except SiteContextError as e:
        # Handle SiteContextError with appropriate error response
        return error_response(message=e.message, error_type=e.error_type, status_code=HTTPStatus.FORBIDDEN)
    except Exception as e:
        # Handle unexpected errors with server_error_response
        logger.error(f"Unexpected error in create_interaction: {e}")
        return error_response(message="An unexpected error occurred", error_type=ErrorType.SERVER, status_code=HTTPStatus.INTERNAL_SERVER_ERROR)
    finally:
        # Log response status
        logger.info("create_interaction request completed")


@interaction_blueprint.route('/interactions/<int:interaction_id>', methods=['PUT'])
def update_interaction(interaction_id: int) -> Tuple[Dict[str, Any], int]:
    """
    Endpoint to update an existing interaction.

    Args:
        interaction_id (int): The ID of the interaction to update

    Returns:
        tuple: JSON response with updated interaction data and HTTP status code
    """
    try:
        # Log request with interaction ID and request data
        logger.info(f"Attempting to update interaction with ID: {interaction_id}, data: {request.json}")

        # Validate request JSON data using InteractionUpdateSchema
        validated_data = InteractionUpdateSchema().load(request.json)

        # Update interaction using InteractionService.update_interaction()
        interaction = InteractionService(InteractionService, SiteContextService, UserContextService, InteractionCreateSchema, StructuredLogger).update_interaction(interaction_id, validated_data)

        # Serialize updated interaction using InteractionResponseSchema
        interaction_data = InteractionResponseSchema().dump(interaction)

        # Return success_response with interaction data
        return success_response(data=interaction_data, message="Interaction updated successfully")

    except ValidationError as e:
        # Handle ValidationError with validation_error_response
        return validation_error_response(errors=e.details, message=e.message)
    except NotFoundError as e:
        # Handle NotFoundError with not_found_response
        return not_found_response(resource_type="interaction", resource_id=str(interaction_id))
    except SiteContextError as e:
        # Handle SiteContextError with appropriate error response
        return error_response(message=e.message, error_type=e.error_type, status_code=HTTPStatus.FORBIDDEN)
    except Exception as e:
        # Handle unexpected errors with server_error_response
        logger.error(f"Unexpected error in update_interaction: {e}")
        return error_response(message="An unexpected error occurred", error_type=ErrorType.SERVER, status_code=HTTPStatus.INTERNAL_SERVER_ERROR)
    finally:
        # Log response status
        logger.info(f"update_interaction request completed for interaction ID: {interaction_id}")


@interaction_blueprint.route('/interactions/<int:interaction_id>', methods=['DELETE'])
def delete_interaction(interaction_id: int) -> Tuple[Dict[str, Any], int]:
    """
    Endpoint to delete an interaction.

    Args:
        interaction_id (int): The ID of the interaction to delete

    Returns:
        tuple: JSON response with deletion confirmation and HTTP status code
    """
    try:
        # Log request with interaction ID
        logger.info(f"Attempting to delete interaction with ID: {interaction_id}")

        # Delete interaction using InteractionService.delete_interaction()
        InteractionService(InteractionService, SiteContextService, UserContextService, InteractionCreateSchema, StructuredLogger).delete_interaction(interaction_id)

        # Return no_content_response if successful
        return no_content_response()

    except NotFoundError as e:
        # Handle NotFoundError with not_found_response
        return not_found_response(resource_type="interaction", resource_id=str(interaction_id))
    except SiteContextError as e:
        # Handle SiteContextError with appropriate error response
        return error_response(message=e.message, error_type=e.error_type, status_code=HTTPStatus.FORBIDDEN)
    except Exception as e:
        # Handle unexpected errors with server_error_response
        logger.error(f"Unexpected error in delete_interaction: {e}")
        return error_response(message="An unexpected error occurred", error_type=ErrorType.SERVER, status_code=HTTPStatus.INTERNAL_SERVER_ERROR)
    finally:
        # Log response status
        logger.info(f"delete_interaction request completed for interaction ID: {interaction_id}")


@interaction_blueprint.route('/search/interactions', methods=['POST'])
def search_interactions() -> Tuple[Dict[str, Any], int]:
    """
    Endpoint for advanced search with multiple filter criteria.

    Returns:
        tuple: JSON response with search results and HTTP status code
    """
    try:
        # Log request with search parameters
        logger.info(f"Attempting advanced search with parameters: {request.json}")

        # Extract search parameters from request JSON
        search_params = request.get_json()

        # Call SearchService.advanced_search() with parameters
        interactions, total = SearchService(InteractionService, SiteContextService).advanced_search(search_params)

        # Serialize results using InteractionListSchema
        interaction_list = InteractionListSchema().dump({'interactions': interactions, 'total': total})

        # Return paginated_response with results
        return paginated_response(items=interaction_list['interactions'], total=interaction_list['total'], page=search_params.get('page', 1), page_size=search_params.get('page_size', 20))

    except ValidationError as e:
        # Handle ValidationError with validation_error_response
        return validation_error_response(errors=e.details, message=e.message)
    except SiteContextError as e:
        # Handle SiteContextError with appropriate error response
        return error_response(message=e.message, error_type=e.error_type, status_code=HTTPStatus.FORBIDDEN)
    except Exception as e:
        # Handle unexpected errors with server_error_response
        logger.error(f"Unexpected error in search_interactions: {e}")
        return error_response(message="An unexpected error occurred", error_type=ErrorType.SERVER, status_code=HTTPStatus.INTERNAL_SERVER_ERROR)
    finally:
        # Log response status with result count
        logger.info(f"search_interactions request completed with {len(interactions)} results")


@interaction_blueprint.route('/search/interactions/dates', methods=['GET'])
def search_by_date_range() -> Tuple[Dict[str, Any], int]:
    """
    Endpoint to search interactions by date range.

    Returns:
        tuple: JSON response with search results and HTTP status code
    """
    try:
        # Extract start_date and end_date parameters from request
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')

        # Parse date strings to datetime objects
        start_date = datetime.fromisoformat(start_date_str) if start_date_str else None
        end_date = datetime.fromisoformat(end_date_str) if end_date_str else None

        # Extract pagination parameters using get_pagination_info()
        page, page_size = get_pagination_info()

        # Call SearchService.search_by_date_range() with parameters
        interactions, total = SearchService(InteractionService, SiteContextService).search_by_date_range(start_date, end_date, page, page_size)

        # Serialize results using InteractionListSchema
        interaction_list = InteractionListSchema().dump({'interactions': interactions, 'total': total})

        # Return paginated_response with results
        return paginated_response(items=interaction_list['interactions'], total=interaction_list['total'], page=page, page_size=page_size)

    except ValidationError as e:
        # Handle ValidationError with validation_error_response
        return validation_error_response(errors=e.details, message=e.message)
    except SiteContextError as e:
        # Handle SiteContextError with appropriate error response
        return error_response(message=e.message, error_type=e.error_type, status_code=HTTPStatus.FORBIDDEN)
    except Exception as e:
        # Handle unexpected errors with server_error_response
        logger.error(f"Unexpected error in search_by_date_range: {e}")
        return error_response(message="An unexpected error occurred", error_type=ErrorType.SERVER, status_code=HTTPStatus.INTERNAL_SERVER_ERROR)
    finally:
        # Log response status with result count
        logger.info(f"search_by_date_range request completed with {len(interactions)} results")


@interaction_blueprint.route('/search/interactions/type/<string:interaction_type>', methods=['GET'])
def search_by_type(interaction_type: str) -> Tuple[Dict[str, Any], int]:
    """
    Endpoint to search interactions by type.

    Args:
        interaction_type (str): The type of interaction to search for

    Returns:
        tuple: JSON response with search results and HTTP status code
    """
    try:
        # Extract interaction_type from URL parameter
        # Extract pagination parameters using get_pagination_info()
        page, page_size = get_pagination_info()

        # Call SearchService.search_by_type() with parameters
        interactions, total = SearchService(InteractionService, SiteContextService).search_by_type(interaction_type, page, page_size)

        # Serialize results using InteractionListSchema
        interaction_list = InteractionListSchema().dump({'interactions': interactions, 'total': total})

        # Return paginated_response with results
        return paginated_response(items=interaction_list['interactions'], total=interaction_list['total'], page=page, page_size=page_size)

    except ValidationError as e:
        # Handle ValidationError with validation_error_response
        return validation_error_response(errors=e.details, message=e.message)
    except SiteContextError as e:
        # Handle SiteContextError with appropriate error response
        return error_response(message=e.message, error_type=e.error_type, status_code=HTTPStatus.FORBIDDEN)
    except Exception as e:
        # Handle unexpected errors with server_error_response
        logger.error(f"Unexpected error in search_by_type: {e}")
        return error_response(message="An unexpected error occurred", error_type=ErrorType.SERVER, status_code=HTTPStatus.INTERNAL_SERVER_ERROR)
    finally:
        # Log response status with result count
        logger.info(f"search_by_type request completed with {len(interactions)} results")


@interaction_blueprint.route('/search/interactions/lead/<string:lead>', methods=['GET'])
def search_by_lead(lead: str) -> Tuple[Dict[str, Any], int]:
    """
    Endpoint to search interactions by lead person.

    Args:
        lead (str): The lead person to search for

    Returns:
        tuple: JSON response with search results and HTTP status code
    """
    try:
        # Extract lead from URL parameter
        # Extract pagination parameters using get_pagination_info()
        page, page_size = get_pagination_info()

        # Call SearchService.search_by_lead() with parameters
        interactions, total = SearchService(InteractionService, SiteContextService).search_by_lead(lead, page, page_size)

        # Serialize results using InteractionListSchema
        interaction_list = InteractionListSchema().dump({'interactions': interactions, 'total': total})

        # Return paginated_response with results
        return paginated_response(items=interaction_list['interactions'], total=interaction_list['total'], page=page, page_size=page_size)

    except ValidationError as e:
        # Handle ValidationError with validation_error_response
        return validation_error_response(errors=e.details, message=e.message)
    except SiteContextError as e:
        # Handle SiteContextError with appropriate error response
        return error_response(message=e.message, error_type=e.error_type, status_code=HTTPStatus.FORBIDDEN)
    except Exception as e:
        # Handle unexpected errors with server_error_response
        logger.error(f"Unexpected error in search_by_lead: {e}")
        return error_response(message="An unexpected error occurred", error_type=ErrorType.SERVER, status_code=HTTPStatus.INTERNAL_SERVER_ERROR)
    finally:
        # Log response status with result count
        logger.info(f"search_by_lead request completed with {len(interactions)} results")