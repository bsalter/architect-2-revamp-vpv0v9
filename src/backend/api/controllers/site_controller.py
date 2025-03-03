"""
Controller that handles API endpoints for site management, including site CRUD operations,
user-site associations, and site context switching. This controller enforces site-scoped
access control and serves as the interface between the client application and site-related business logic.
"""

from flask import Blueprint, request, jsonify, g  # flask 2.3.2
from http import HTTPStatus  # standard library
from typing import Dict, List, Any, Optional  # standard library
import marshmallow  # marshmallow 3.20.1

from ...services.site_service import SiteService  # src/backend/services/site_service.py
from ...auth.user_context_service import UserContextService  # src/backend/auth/user_context_service.py
from ...auth.site_context_service import SiteContextService  # src/backend/auth/site_context_service.py
from ..schemas.site_schemas import SiteSchema, SiteCreateSchema, SiteUpdateSchema, SiteListSchema, SiteBriefSchema, SiteUserAssignSchema, UserSiteSchema, SiteContextSchema  # src/backend/api/schemas/site_schemas.py
from ..helpers.response import success_response, created_response, no_content_response, error_response, validation_error_response, not_found_response, paginated_response  # src/backend/api/helpers/response.py
from ..helpers.pagination import get_pagination_info  # src/backend/api/helpers/pagination.py
from ..middleware.auth_middleware import requires_auth  # src/backend/api/middleware/auth_middleware.py
from ..middleware.site_context_middleware import requires_site_context  # src/backend/api/middleware/site_context_middleware.py
from ...logging.structured_logger import StructuredLogger  # src/backend/logging/structured_logger.py
from ...utils.error_util import ValidationError, NotFoundError, AuthorizationError, SiteContextError  # src/backend/utils/error_util.py

# Define the blueprint for site-related API endpoints
site_blueprint = Blueprint('sites', __name__, url_prefix='/api/sites')

# Initialize structured logger for this module
logger = StructuredLogger(__name__)

# Initialize SiteService, UserContextService, and SiteContextService
site_service = SiteService()
user_context_service = UserContextService()
site_context_service = SiteContextService()

@site_blueprint.route('/', methods=['GET'])
@requires_auth
def get_all_sites():
    """
    Get all sites the current user has access to with pagination
    """
    try:
        # Extract pagination parameters from request using get_pagination_info()
        page, per_page = get_pagination_info()

        # Extract filter parameters from request query string
        filters = request.args.to_dict()

        # Get current user ID from user context service
        user_id = user_context_service.get_current_user_id()

        # Call site_service.get_all_sites() with pagination and filters
        sites, total_count = site_service.get_all_sites(page=page, per_page=per_page, filters=filters)

        # Serialize sites with SiteSchema
        site_schema = SiteSchema(many=True)
        serialized_sites = site_schema.dump(sites)

        # Return paginated_response with serialized sites
        return paginated_response(items=serialized_sites, total=total_count, page=page, page_size=per_page)

    except Exception as e:
        # Handle exceptions and return appropriate error responses
        logger.error(f"Error getting all sites: {str(e)}")
        return error_response(message="Failed to retrieve sites", error_type=ErrorType.SERVER, details={'error': str(e)}), HTTPStatus.INTERNAL_SERVER_ERROR

    finally:
        # Log the operation and its outcome
        logger.info("Get all sites operation completed")

@site_blueprint.route('/<int:site_id>', methods=['GET'])
@requires_auth
def get_site_by_id(site_id: int):
    """
    Get details of a specific site by ID
    """
    try:
        # Try to get site from site_service.get_site_by_id(site_id)
        site = site_service.get_site_by_id(site_id)

        # If site found, get site stats from site_service.get_site_stats(site_id)
        site_stats = site_service.get_site_stats(site_id)

        # Serialize site with SiteSchema and include stats
        site_schema = SiteSchema()
        serialized_site = site_schema.dump(site)
        serialized_site.update(site_stats)

        # Return success_response with serialized site
        return success_response(data=serialized_site, message="Site retrieved successfully")

    except NotFoundError as e:
        # Handle NotFoundError and return not_found_response
        logger.warning(f"Site not found: {str(e)}")
        return not_found_response(resource_type="Site", resource_id=site_id), HTTPStatus.NOT_FOUND

    except Exception as e:
        # Handle other exceptions and return appropriate error responses
        logger.error(f"Error getting site by ID: {str(e)}")
        return error_response(message="Failed to retrieve site", error_type=ErrorType.SERVER, details={'error': str(e)}), HTTPStatus.INTERNAL_SERVER_ERROR

    finally:
        # Log the operation and its outcome
        logger.info(f"Get site by ID operation completed for site ID: {site_id}")

@site_blueprint.route('/', methods=['POST'])
@requires_auth
def create_site():
    """
    Create a new site
    """
    try:
        # Get JSON data from request
        json_data = request.get_json()

        # Validate request data using SiteCreateSchema
        site_create_schema = SiteCreateSchema()
        validated_data = site_create_schema.load(json_data)

        # Get current user ID from user context service
        user_id = user_context_service.get_current_user_id()

        # Call site_service.create_site() with validated data and user ID
        site = site_service.create_site(validated_data, creator_user_id=user_id)

        # Serialize created site with SiteSchema
        site_schema = SiteSchema()
        serialized_site = site_schema.dump(site)

        # Return created_response with serialized site
        return created_response(data=serialized_site, message="Site created successfully")

    except marshmallow.exceptions.ValidationError as e:
        # Handle ValidationError and return validation_error_response
        logger.warning(f"Validation error creating site: {str(e)}")
        return validation_error_response(errors=e.messages, message="Invalid site data"), HTTPStatus.BAD_REQUEST

    except Exception as e:
        # Handle other exceptions and return appropriate error responses
        logger.error(f"Error creating site: {str(e)}")
        return error_response(message="Failed to create site", error_type=ErrorType.SERVER, details={'error': str(e)}), HTTPStatus.INTERNAL_SERVER_ERROR

    finally:
        # Log the operation and its outcome
        logger.info("Create site operation completed")

@site_blueprint.route('/<int:site_id>', methods=['PUT'])
@requires_auth
def update_site(site_id: int):
    """
    Update an existing site
    """
    try:
        # Get JSON data from request
        json_data = request.get_json()

        # Validate request data using SiteUpdateSchema
        site_update_schema = SiteUpdateSchema()
        validated_data = site_update_schema.load(json_data)

        # Call site_service.update_site() with site_id and validated data
        site = site_service.update_site(site_id, validated_data)

        # Serialize updated site with SiteSchema
        site_schema = SiteSchema()
        serialized_site = site_schema.dump(site)

        # Return success_response with serialized site
        return success_response(data=serialized_site, message="Site updated successfully")

    except NotFoundError as e:
        # Handle NotFoundError and return not_found_response
        logger.warning(f"Site not found: {str(e)}")
        return not_found_response(resource_type="Site", resource_id=site_id), HTTPStatus.NOT_FOUND

    except marshmallow.exceptions.ValidationError as e:
        # Handle ValidationError and return validation_error_response
        logger.warning(f"Validation error updating site: {str(e)}")
        return validation_error_response(errors=e.messages, message="Invalid site data"), HTTPStatus.BAD_REQUEST

    except AuthorizationError as e:
        # Handle AuthorizationError and return error_response with HTTP_FORBIDDEN
        logger.warning(f"Authorization error updating site: {str(e)}")
        return error_response(message=str(e), error_type=ErrorType.AUTHORIZATION, error_code="PERMISSION_DENIED"), HTTPStatus.FORBIDDEN

    except Exception as e:
        # Handle other exceptions and return appropriate error responses
        logger.error(f"Error updating site: {str(e)}")
        return error_response(message="Failed to update site", error_type=ErrorType.SERVER, details={'error': str(e)}), HTTPStatus.INTERNAL_SERVER_ERROR

    finally:
        # Log the operation and its outcome
        logger.info(f"Update site operation completed for site ID: {site_id}")

@site_blueprint.route('/<int:site_id>', methods=['DELETE'])
@requires_auth
def delete_site(site_id: int):
    """
    Delete an existing site
    """
    try:
        # Call site_service.delete_site() with site_id
        site_service.delete_site(site_id)

        # Return no_content_response on success
        return no_content_response()

    except NotFoundError as e:
        # Handle NotFoundError and return not_found_response
        logger.warning(f"Site not found: {str(e)}")
        return not_found_response(resource_type="Site", resource_id=site_id), HTTPStatus.NOT_FOUND

    except AuthorizationError as e:
        # Handle AuthorizationError and return error_response with HTTP_FORBIDDEN
        logger.warning(f"Authorization error deleting site: {str(e)}")
        return error_response(message=str(e), error_type=ErrorType.AUTHORIZATION, error_code="PERMISSION_DENIED"), HTTPStatus.FORBIDDEN

    except Exception as e:
        # Handle other exceptions and return appropriate error responses
        logger.error(f"Error deleting site: {str(e)}")
        return error_response(message="Failed to delete site", error_type=ErrorType.SERVER, details={'error': str(e)}), HTTPStatus.INTERNAL_SERVER_ERROR

    finally:
        # Log the operation and its outcome
        logger.info(f"Delete site operation completed for site ID: {site_id}")

@site_blueprint.route('/<int:site_id>/users', methods=['GET'])
@requires_auth
def get_site_users(site_id: int):
    """
    Get all users associated with a site
    """
    try:
        # Get pagination parameters from request using get_pagination_info()
        page, per_page = get_pagination_info()

        # Get filter parameters from request query string
        filters = request.args.to_dict()

        # Call site_service.get_site_users() with site_id, pagination and filters
        users, total_count = site_service.get_site_users(site_id, page=page, per_page=per_page, filters=filters)

        # Serialize users with UserSiteSchema
        user_site_schema = UserSiteSchema(many=True)
        serialized_users = user_site_schema.dump(users)

        # Return paginated_response with serialized users
        return paginated_response(items=serialized_users, total=total_count, page=page, page_size=per_page)

    except NotFoundError as e:
        # Handle NotFoundError and return not_found_response
        logger.warning(f"Site not found: {str(e)}")
        return not_found_response(resource_type="Site", resource_id=site_id), HTTPStatus.NOT_FOUND

    except AuthorizationError as e:
        # Handle AuthorizationError and return error_response with HTTP_FORBIDDEN
        logger.warning(f"Authorization error getting site users: {str(e)}")
        return error_response(message=str(e), error_type=ErrorType.AUTHORIZATION, error_code="PERMISSION_DENIED"), HTTPStatus.FORBIDDEN

    except Exception as e:
        # Handle other exceptions and return appropriate error responses
        logger.error(f"Error getting site users: {str(e)}")
        return error_response(message="Failed to retrieve site users", error_type=ErrorType.SERVER, details={'error': str(e)}), HTTPStatus.INTERNAL_SERVER_ERROR

    finally:
        # Log the operation and its outcome
        logger.info(f"Get site users operation completed for site ID: {site_id}")

@site_blueprint.route('/<int:site_id>/users', methods=['POST'])
@requires_auth
def add_user_to_site(site_id: int):
    """
    Add a user to a site with a specific role
    """
    try:
        # Get JSON data from request
        json_data = request.get_json()

        # Validate request data using SiteUserAssignSchema
        site_user_assign_schema = SiteUserAssignSchema()
        validated_data = site_user_assign_schema.load(json_data)

        # Extract user_id and role from validated data
        user_id = validated_data['user_id']
        role = validated_data['role']

        # Call site_service.add_user_to_site() with site_id, user_id, and role
        user_site_data = site_service.add_user_to_site(site_id, user_id, role)

        # Serialize result with UserSiteSchema
        user_site_schema = UserSiteSchema()
        serialized_data = user_site_schema.dump(user_site_data)

        # Return created_response with serialized data
        return created_response(data=serialized_data, message="User added to site successfully")

    except NotFoundError as e:
        # Handle NotFoundError and return not_found_response
        logger.warning(f"Site or user not found: {str(e)}")
        return not_found_response(resource_type="Site or User", resource_id=site_id), HTTPStatus.NOT_FOUND

    except marshmallow.exceptions.ValidationError as e:
        # Handle ValidationError and return validation_error_response
        logger.warning(f"Validation error adding user to site: {str(e)}")
        return validation_error_response(errors=e.messages, message="Invalid user or role data"), HTTPStatus.BAD_REQUEST

    except AuthorizationError as e:
        # Handle AuthorizationError and return error_response with HTTP_FORBIDDEN
        logger.warning(f"Authorization error adding user to site: {str(e)}")
        return error_response(message=str(e), error_type=ErrorType.AUTHORIZATION, error_code="PERMISSION_DENIED"), HTTPStatus.FORBIDDEN

    except Exception as e:
        # Handle other exceptions and return appropriate error responses
        logger.error(f"Error adding user to site: {str(e)}")
        return error_response(message="Failed to add user to site", error_type=ErrorType.SERVER, details={'error': str(e)}), HTTPStatus.INTERNAL_SERVER_ERROR

    finally:
        # Log the operation and its outcome
        logger.info(f"Add user to site operation completed for site ID: {site_id}")

@site_blueprint.route('/<int:site_id>/users/<int:user_id>', methods=['DELETE'])
@requires_auth
def remove_user_from_site(site_id: int, user_id: int):
    """
    Remove a user from a site
    """
    try:
        # Call site_service.remove_user_from_site() with site_id and user_id
        site_service.remove_user_from_site(site_id, user_id)

        # Return no_content_response on success
        return no_content_response()

    except NotFoundError as e:
        # Handle NotFoundError and return not_found_response
        logger.warning(f"Site or user not found: {str(e)}")
        return not_found_response(resource_type="Site or User", resource_id=f"site_id={site_id}, user_id={user_id}"), HTTPStatus.NOT_FOUND

    except AuthorizationError as e:
        # Handle AuthorizationError and return error_response with HTTP_FORBIDDEN
        logger.warning(f"Authorization error removing user from site: {str(e)}")
        return error_response(message=str(e), error_type=ErrorType.AUTHORIZATION, error_code="PERMISSION_DENIED"), HTTPStatus.FORBIDDEN

    except Exception as e:
        # Handle other exceptions and return appropriate error responses
        logger.error(f"Error removing user from site: {str(e)}")
        return error_response(message="Failed to remove user from site", error_type=ErrorType.SERVER, details={'error': str(e)}), HTTPStatus.INTERNAL_SERVER_ERROR

    finally:
        # Log the operation and its outcome
        logger.info(f"Remove user from site operation completed for site ID: {site_id}, user ID: {user_id}")

@site_blueprint.route('/<int:site_id>/users/<int:user_id>', methods=['PUT'])
@requires_auth
def update_user_role(site_id: int, user_id: int):
    """
    Update a user's role for a site
    """
    try:
        # Get JSON data from request
        json_data = request.get_json()

        # Validate role from request data
        if 'role' not in json_data:
            logger.warning("Role is missing in request data")
            return validation_error_response(errors={'role': 'Role is required.'}, message="Invalid request data"), HTTPStatus.BAD_REQUEST
        
        role = json_data['role']

        # Call site_service.update_user_role() with site_id, user_id, and new role
        user_site_data = site_service.update_user_role(site_id, user_id, role)

        # Serialize result with UserSiteSchema
        user_site_schema = UserSiteSchema()
        serialized_data = user_site_schema.dump(user_site_data)

        # Return success_response with serialized data
        return success_response(data=serialized_data, message="User role updated successfully")

    except NotFoundError as e:
        # Handle NotFoundError and return not_found_response
        logger.warning(f"Site or user not found: {str(e)}")
        return not_found_response(resource_type="Site or User", resource_id=f"site_id={site_id}, user_id={user_id}"), HTTPStatus.NOT_FOUND

    except marshmallow.exceptions.ValidationError as e:
        # Handle ValidationError and return validation_error_response
        logger.warning(f"Validation error updating user role: {str(e)}")
        return validation_error_response(errors=e.messages, message="Invalid role data"), HTTPStatus.BAD_REQUEST

    except AuthorizationError as e:
        # Handle AuthorizationError and return error_response with HTTP_FORBIDDEN
        logger.warning(f"Authorization error updating user role: {str(e)}")
        return error_response(message=str(e), error_type=ErrorType.AUTHORIZATION, error_code="PERMISSION_DENIED"), HTTPStatus.FORBIDDEN

    except Exception as e:
        # Handle other exceptions and return appropriate error responses
        logger.error(f"Error updating user role: {str(e)}")
        return error_response(message="Failed to update user role", error_type=ErrorType.SERVER, details={'error': str(e)}), HTTPStatus.INTERNAL_SERVER_ERROR

    finally:
        # Log the operation and its outcome
        logger.info(f"Update user role operation completed for site ID: {site_id}, user ID: {user_id}")

@site_blueprint.route('/user/<int:user_id>', methods=['GET'])
@requires_auth
def get_user_sites(user_id: int):
    """
    Get all sites a specific user has access to
    """
    try:
        # Call site_service.get_user_sites() with user_id
        sites = site_service.get_user_sites(user_id)

        # Serialize sites with SiteSchema
        site_schema = SiteBriefSchema(many=True)
        serialized_sites = site_schema.dump(sites)

        # Return success_response with serialized sites
        return success_response(data=serialized_sites, message="User sites retrieved successfully")

    except NotFoundError as e:
        # Handle NotFoundError and return not_found_response
        logger.warning(f"User not found: {str(e)}")
        return not_found_response(resource_type="User", resource_id=user_id), HTTPStatus.NOT_FOUND

    except AuthorizationError as e:
        # Handle AuthorizationError and return error_response with HTTP_FORBIDDEN
        logger.warning(f"Authorization error getting user sites: {str(e)}")
        return error_response(message=str(e), error_type=ErrorType.AUTHORIZATION, error_code="PERMISSION_DENIED"), HTTPStatus.FORBIDDEN

    except Exception as e:
        # Handle other exceptions and return appropriate error responses
        logger.error(f"Error getting user sites: {str(e)}")
        return error_response(message="Failed to retrieve user sites", error_type=ErrorType.SERVER, details={'error': str(e)}), HTTPStatus.INTERNAL_SERVER_ERROR

    finally:
        # Log the operation and its outcome
        logger.info(f"Get user sites operation completed for user ID: {user_id}")

@site_blueprint.route('/<int:site_id>/context', methods=['POST'])
@requires_auth
def switch_site_context(site_id: int):
    """
    Switch the current site context to a different site
    """
    try:
        # Call site_service.switch_site_context() with site_id
        site_service.switch_site_context(site_id)

        # Serialize site context with SiteContextSchema
        site_context_schema = SiteContextSchema()
        serialized_context = site_context_schema.dump({'site_id': site_id, 'name': f'Site {site_id}', 'role': 'admin'}) #TODO: Remove hardcoded values

        # Return success_response with serialized site context
        return success_response(data=serialized_context, message="Site context switched successfully")

    except NotFoundError as e:
        # Handle NotFoundError and return not_found_response
        logger.warning(f"Site not found: {str(e)}")
        return not_found_response(resource_type="Site", resource_id=site_id), HTTPStatus.NOT_FOUND

    except AuthorizationError as e:
        # Handle AuthorizationError and return error_response with HTTP_FORBIDDEN
        logger.warning(f"Authorization error switching site context: {str(e)}")
        return error_response(message=str(e), error_type=ErrorType.AUTHORIZATION, error_code="PERMISSION_DENIED"), HTTPStatus.FORBIDDEN

    except SiteContextError as e:
        # Handle SiteContextError and return error_response with specific error details
        logger.warning(f"Site context error: {str(e)}")
        return error_response(message=str(e), error_type=ErrorType.AUTHORIZATION, details=e.to_dict(), error_code="SITE_CONTEXT_ERROR"), HTTPStatus.FORBIDDEN

    except Exception as e:
        # Handle other exceptions and return appropriate error responses
        logger.error(f"Error switching site context: {str(e)}")
        return error_response(message="Failed to switch site context", error_type=ErrorType.SERVER, details={'error': str(e)}), HTTPStatus.INTERNAL_SERVER_ERROR

    finally:
        # Log the operation and its outcome
        logger.info(f"Switch site context operation completed for site ID: {site_id}")

@site_blueprint.route('/context', methods=['GET'])
@requires_auth
def get_current_site_context():
    """
    Get the current site context information
    """
    try:
        # Get current site context from site_context_service.get_current_site_context()
        site_context = site_context_service.get_current_site_context()

        if not site_context:
            logger.warning("No site context found")
            return not_found_response(resource_type="Site Context", resource_id="current"), HTTPStatus.NOT_FOUND

        # Serialize site context with SiteContextSchema
        site_context_schema = SiteContextSchema()
        serialized_context = site_context_schema.dump(site_context)

        # Return success_response with serialized site context
        return success_response(data=serialized_context, message="Current site context retrieved successfully")

    except SiteContextError as e:
        # Handle SiteContextError and return error_response with specific error details
        logger.warning(f"Site context error: {str(e)}")
        return error_response(message=str(e), error_type=ErrorType.AUTHORIZATION, details=e.to_dict(), error_code="SITE_CONTEXT_ERROR"), HTTPStatus.FORBIDDEN

    except Exception as e:
        # Handle other exceptions and return appropriate error responses
        logger.error(f"Error getting current site context: {str(e)}")
        return error_response(message="Failed to retrieve current site context", error_type=ErrorType.SERVER, details={'error': str(e)}), HTTPStatus.INTERNAL_SERVER_ERROR

    finally:
        # Log the operation and its outcome
        logger.info("Get current site context operation completed")

@site_blueprint.route('/search', methods=['GET'])
@requires_auth
def search_sites():
    """
    Search sites by name or description with user access filtering
    """
    try:
        # Get search term from request query params
        search_term = request.args.get('search_term', '')

        # Get pagination parameters from request using get_pagination_info()
        page, per_page = get_pagination_info()

        # Call site_service.search_sites() with search term and pagination
        sites, total_count = site_service.search_sites(search_term, page=page, per_page=per_page)

        # Serialize sites with SiteSchema
        site_schema = SiteSchema(many=True)
        serialized_sites = site_schema.dump(sites)

        # Return paginated_response with serialized sites
        return paginated_response(items=serialized_sites, total=total_count, page=page, page_size=per_page)

    except Exception as e:
        # Handle exceptions and return appropriate error responses
        logger.error(f"Error searching sites: {str(e)}")
        return error_response(message="Failed to search sites", error_type=ErrorType.SERVER, details={'error': str(e)}), HTTPStatus.INTERNAL_SERVER_ERROR

    finally:
        # Log the operation and its outcome
        logger.info(f"Search sites operation completed with search term: {search_term}")