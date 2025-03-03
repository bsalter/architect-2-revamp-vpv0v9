"""
Controller responsible for handling search-related API endpoints in the Interaction Management System.
Exposes endpoints for basic search, advanced search with filtering, and specialized searches like date range, type, and lead filters.
Ensures proper authentication, validation, and site-scoping of all search results.
"""
from typing import Dict, Tuple

from flask import Blueprint, request, jsonify  # flask 2.3.2
from datetime import datetime  # standard library

from ..schemas.search_schemas import SearchSchema, AdvancedSearchSchema, SearchResultsSchema, DateRangeSchema  # src/backend/api/schemas/search_schemas.py
from ..middleware.auth_middleware import requires_auth  # src/backend/api/middleware/auth_middleware.py
from ..helpers.response import success_response, paginated_response, validation_error_response, server_error_response  # src/backend/api/helpers/response.py
from ...utils.error_util import ValidationError  # src/backend/utils/error_util.py
from ...services.search_service import SearchService  # src/backend/services/search_service.py
from ...repositories.interaction_repository import InteractionRepository  # src/backend/repositories/interaction_repository.py
from ...auth.site_context_service import SiteContextService  # src/backend/auth/site_context_service.py
from ...logging.structured_logger import StructuredLogger  # src/backend/logging/structured_logger.py

# Create Flask blueprint for search routes
search_blueprint = Blueprint('search', __name__, url_prefix='/api/search')

# Initialize structured logger
logger = StructuredLogger(__name__)

# Initialize search service (using dependency injection)
search_service = SearchService(InteractionRepository(), SiteContextService())


@search_blueprint.route('/interactions', methods=['GET'])
@requires_auth
def search_interactions() -> Tuple[Dict, int]:
    """
    Handle basic search requests with optional filtering.

    Returns:
        Tuple[Dict, int]: JSON response with search results and HTTP status code
    """
    try:
        # Extract query parameter from request
        query = request.args.get('query', '')

        # Extract pagination parameters (page, page_size)
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 20, type=int)

        # Validate search parameters using SearchSchema
        search_schema = SearchSchema()
        try:
            validated_data = search_schema.load({'query': query, 'pagination': {'page': page, 'page_size': page_size}})
            query = validated_data.get('query', '')
            page = validated_data['pagination']['page']
            page_size = validated_data['pagination']['page_size']
        except ValidationError as err:
            logger.error(f"Validation error: {err.messages}")
            return validation_error_response(err.messages)

        # Call search_service.search with validated parameters
        interactions, total_count = search_service.search(query=query, page=page, page_size=page_size)

        # Format search results using SearchResultsSchema
        results_schema = SearchResultsSchema()
        formatted_results = results_schema.dump({'results': interactions, 'pagination': {'page': page, 'page_size': page_size, 'total': total_count}})

        # Return paginated_response with formatted results
        return paginated_response(items=formatted_results['results'],
                                  total=total_count,
                                  page=page,
                                  page_size=page_size)

    except ValidationError as e:
        # Handle validation errors with validation_error_response
        logger.error(f"Validation error: {str(e)}")
        return validation_error_response(e.messages)

    except Exception as e:
        # Handle unexpected errors with server_error_response and logging
        logger.error(f"Unexpected error: {str(e)}")
        return server_error_response()


@search_blueprint.route('/advanced', methods=['POST'])
@requires_auth
def advanced_search() -> Tuple[Dict, int]:
    """
    Handle advanced search requests with complex filtering and sorting.

    Returns:
        Tuple[Dict, int]: JSON response with search results and HTTP status code
    """
    try:
        # Get JSON data from request
        json_data = request.get_json()

        # Validate search parameters using AdvancedSearchSchema
        search_schema = AdvancedSearchSchema()
        try:
            validated_data = search_schema.load(json_data)
        except ValidationError as err:
            logger.error(f"Validation error: {err.messages}")
            return validation_error_response(err.messages)

        # Call search_service.advanced_search with validated parameters
        interactions, total_count = search_service.advanced_search(search_params=validated_data)

        # Format search results using SearchResultsSchema
        results_schema = SearchResultsSchema()
        formatted_results = results_schema.dump({'results': interactions, 'pagination': validated_data.get('pagination')})

        # Return paginated_response with formatted results
        page = validated_data.get('pagination', {}).get('page', 1)
        page_size = validated_data.get('pagination', {}).get('page_size', 20)

        return paginated_response(items=formatted_results['results'],
                                  total=total_count,
                                  page=page,
                                  page_size=page_size)

    except ValidationError as e:
        # Handle validation errors with validation_error_response
        logger.error(f"Validation error: {str(e)}")
        return validation_error_response(e.messages)

    except Exception as e:
        # Handle unexpected errors with server_error_response and logging
        logger.error(f"Unexpected error: {str(e)}")
        return server_error_response()


@search_blueprint.route('/date-range', methods=['GET'])
@requires_auth
def search_by_date_range() -> Tuple[Dict, int]:
    """
    Search interactions within a specific date range.

    Returns:
        Tuple[Dict, int]: JSON response with search results and HTTP status code
    """
    try:
        # Extract start_date and end_date parameters from request
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')

        # Extract pagination parameters (page, page_size)
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 20, type=int)

        # Validate date range using DateRangeSchema
        date_range_schema = DateRangeSchema()
        try:
            validated_data = date_range_schema.load({'start_date': start_date_str, 'end_date': end_date_str})
            start_date = validated_data['start_date']
            end_date = validated_data['end_date']
        except ValidationError as err:
            logger.error(f"Validation error: {err.messages}")
            return validation_error_response(err.messages)

        # Parse dates to datetime objects
        # Call search_service.search_by_date_range with validated parameters
        interactions, total_count = search_service.search_by_date_range(start_date=start_date, end_date=end_date, page=page, page_size=page_size)

        # Format search results using SearchResultsSchema
        results_schema = SearchResultsSchema()
        formatted_results = results_schema.dump({'results': interactions, 'pagination': {'page': page, 'page_size': page_size, 'total': total_count}})

        # Return paginated_response with formatted results
        return paginated_response(items=formatted_results['results'],
                                  total=total_count,
                                  page=page,
                                  page_size=page_size)

    except ValidationError as e:
        # Handle validation errors with validation_error_response
        logger.error(f"Validation error: {str(e)}")
        return validation_error_response(e.messages)

    except Exception as e:
        # Handle unexpected errors with server_error_response and logging
        logger.error(f"Unexpected error: {str(e)}")
        return server_error_response()


@search_blueprint.route('/type/<interaction_type>', methods=['GET'])
@requires_auth
def search_by_type() -> Tuple[Dict, int]:
    """
    Search interactions by interaction type.

    Returns:
        Tuple[Dict, int]: JSON response with search results and HTTP status code
    """
    try:
        # Extract interaction_type from URL parameter
        interaction_type = request.view_args['interaction_type']

        # Extract pagination parameters (page, page_size)
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 20, type=int)

        # Call search_service.search_by_type with parameters
        interactions, total_count = search_service.search_by_type(interaction_type=interaction_type, page=page, page_size=page_size)

        # Format search results using SearchResultsSchema
        results_schema = SearchResultsSchema()
        formatted_results = results_schema.dump({'results': interactions, 'pagination': {'page': page, 'page_size': page_size, 'total': total_count}})

        # Return paginated_response with formatted results
        return paginated_response(items=formatted_results['results'],
                                  total=total_count,
                                  page=page,
                                  page_size=page_size)

    except ValidationError as e:
        # Handle validation errors with validation_error_response
        logger.error(f"Validation error: {str(e)}")
        return validation_error_response(e.messages)

    except Exception as e:
        # Handle unexpected errors with server_error_response and logging
        logger.error(f"Unexpected error: {str(e)}")
        return server_error_response()


@search_blueprint.route('/lead/<lead>', methods=['GET'])
@requires_auth
def search_by_lead() -> Tuple[Dict, int]:
    """
    Search interactions by lead person.

    Returns:
        Tuple[Dict, int]: JSON response with search results and HTTP status code
    """
    try:
        # Extract lead from URL parameter
        lead = request.view_args['lead']

        # Extract pagination parameters (page, page_size)
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 20, type=int)

        # Call search_service.search_by_lead with parameters
        interactions, total_count = search_service.search_by_lead(lead=lead, page=page, page_size=page_size)

        # Format search results using SearchResultsSchema
        results_schema = SearchResultsSchema()
        formatted_results = results_schema.dump({'results': interactions, 'pagination': {'page': page, 'page_size': page_size, 'total': total_count}})

        # Return paginated_response with formatted results
        return paginated_response(items=formatted_results['results'],
                                  total=total_count,
                                  page=page,
                                  page_size=page_size)

    except ValidationError as e:
        # Handle validation errors with validation_error_response
        logger.error(f"Validation error: {str(e)}")
        return validation_error_response(e.messages)

    except Exception as e:
        # Handle unexpected errors with server_error_response and logging
        logger.error(f"Unexpected error: {str(e)}")
        return server_error_response()


@search_blueprint.route('/upcoming', methods=['GET'])
@requires_auth
def get_upcoming_interactions() -> Tuple[Dict, int]:
    """
    Get a list of upcoming interactions.

    Returns:
        Tuple[Dict, int]: JSON response with upcoming interactions
    """
    try:
        # Extract limit parameter from request (default: 5)
        limit = request.args.get('limit', 5, type=int)

        # Call search_service.get_upcoming_interactions with limit
        upcoming_interactions = search_service.get_upcoming_interactions(limit=limit)

        # Return success_response with the upcoming interactions
        return success_response(data=upcoming_interactions)

    except Exception as e:
        # Handle unexpected errors with server_error_response and logging
        logger.error(f"Unexpected error: {str(e)}")
        return server_error_response()


@search_blueprint.route('/recent', methods=['GET'])
@requires_auth
def get_recent_interactions() -> Tuple[Dict, int]:
    """
    Get a list of recently completed interactions.

    Returns:
        Tuple[Dict, int]: JSON response with recent interactions
    """
    try:
        # Extract limit parameter from request (default: 5)
        limit = request.args.get('limit', 5, type=int)

        # Call search_service.get_recent_interactions with limit
        recent_interactions = search_service.get_recent_interactions(limit=limit)

        # Return success_response with the recent interactions
        return success_response(data=recent_interactions)

    except Exception as e:
        # Handle unexpected errors with server_error_response and logging
        logger.error(f"Unexpected error: {str(e)}")
        return server_error_response()


@search_blueprint.route('/cache/invalidate', methods=['POST'])
@requires_auth
def invalidate_search_cache() -> Tuple[Dict, int]:
    """
    Force invalidation of search cache for current site.

    Returns:
        Tuple[Dict, int]: JSON response with invalidation result
    """
    try:
        # Call search_service.invalidate_search_cache()
        invalidation_count = search_service.invalidate_search_cache()

        # Return success_response with invalidation confirmation
        return success_response(data={'invalidated_entries': invalidation_count},
                                  message="Search cache invalidated successfully")

    except Exception as e:
        # Handle unexpected errors with server_error_response and logging
        logger.error(f"Unexpected error: {str(e)}")
        return server_error_response()