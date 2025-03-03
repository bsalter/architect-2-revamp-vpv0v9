"""
Controller for user management endpoints in the Interaction Management System.
Provides RESTful API endpoints for retrieving, creating, updating, deleting users,
and managing user-site associations with site-scoped access control.
"""

from typing import Dict, List, Any, Optional, Tuple

from flask import Blueprint, request, jsonify, current_app  # flask 2.3.2
from marshmallow import ValidationError  # marshmallow 3.20.1

from ...services.user_service import UserService  # UserService class for user management operations
from ..schemas.user_schemas import UserSchema, UserCreateSchema, UserUpdateSchema, UserProfileSchema, UserSiteSchema, UserListSchema  # Schemas for validating user-related requests and responses
from ...auth.site_context_service import SiteContextService  # Service for site context management and validation
from ..helpers.response import success_response, error_response, validation_error_response, not_found_response, unauthorized_response, forbidden_response, created_response, no_content_response, paginated_response  # Standardized response formatting functions
from ...logging.audit_logger import AuditLogger, USER_CATEGORY  # Audit logging for user management operations
from ...logging.structured_logger import StructuredLogger  # Structured logging for controller operations
from ...utils.error_util import AuthenticationError, AuthorizationError, ValidationError, NotFoundError, SiteContextError  # Exception types for various error scenarios
from ...utils.enums import UserRole  # Enum defining user role types

# Blueprint for user-related endpoints
user_bp = Blueprint('users', __name__, url_prefix='/api/users')

# Initialize structured logger
logger = StructuredLogger(__name__)

# Initialize audit logger
audit_logger = AuditLogger()


def get_user_service() -> UserService:
    """
    Helper function to get the user service instance from app context.

    Returns:
        UserService: User service instance
    """
    return current_app.extensions['user_service']


def get_site_context_service() -> SiteContextService:
    """
    Helper function to get the site context service instance from app context.

    Returns:
        SiteContextService: Site context service instance
    """
    return current_app.extensions['site_context_service']


@user_bp.route('', methods=['GET'])
def get_users() -> Tuple[Dict[str, Any], int]:
    """
    Get a paginated list of users for the current site with optional filtering.

    Returns:
        Tuple[Dict[str, Any], int]: JSON response with paginated user data and HTTP status code
    """
    try:
        # Extract query parameters (page, per_page, sort_by, sort_desc, filters)
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        sort_by = request.args.get('sort_by')
        sort_desc = request.args.get('sort_desc', 'false').lower() == 'true'
        filters = request.args.get('filters')  # TODO: Implement filter parsing

        # Get current site ID from SiteContextService
        site_id = get_site_context_service().get_current_site_id()

        # Call user_service.get_users_by_site with site_id and query params
        users, total = get_user_service().get_users_by_site(site_id, filters=filters, page=page, per_page=per_page, sort_by=sort_by, sort_desc=sort_desc)

        # Format response using UserSchema and UserListSchema
        user_schema = UserSchema(many=True)
        users_data = user_schema.dump(users)

        # Return paginated_response with user data
        return paginated_response(items=users_data, total=total, page=page, page_size=per_page)

    except AuthenticationError as e:
        # Handle AuthenticationError with unauthorized_response
        return unauthorized_response(message=str(e))
    except SiteContextError as e:
        # Handle SiteContextError with forbidden_response
        return forbidden_response(message=str(e))
    except Exception as e:
        # Handle other exceptions with server_error_response
        logger.error(f"Error getting users: {str(e)}")
        return server_error_response(message="Failed to retrieve users")


@user_bp.route('/<int:user_id>', methods=['GET'])
def get_user(user_id: int) -> Tuple[Dict[str, Any], int]:
    """
    Get a specific user by ID with site-scoped access control.

    Returns:
        Tuple[Dict[str, Any], int]: JSON response with user data and HTTP status code
    """
    try:
        # Call user_service.get_user_by_id to retrieve user with site-scoping
        user = get_user_service().get_user_by_id(user_id)

        # Format response using UserProfileSchema
        user_profile_schema = UserProfileSchema()
        user_data = user_profile_schema.dump(user)

        # Return success_response with user data
        return success_response(data=user_data)

    except NotFoundError as e:
        # Handle NotFoundError with not_found_response
        return not_found_response(resource_type="User", resource_id=user_id)
    except AuthenticationError as e:
        # Handle AuthenticationError with unauthorized_response
        return unauthorized_response(message=str(e))
    except AuthorizationError as e:
        # Handle AuthorizationError with forbidden_response
        return forbidden_response(message=str(e))
    except Exception as e:
        # Handle other exceptions with server_error_response
        logger.error(f"Error getting user: {str(e)}")
        return server_error_response(message="Failed to retrieve user")


@user_bp.route('', methods=['POST'])
def create_user() -> Tuple[Dict[str, Any], int]:
    """
    Create a new user with site association.

    Returns:
        Tuple[Dict[str, Any], int]: JSON response with created user data and HTTP status code
    """
    try:
        # Extract request data from request.json
        request_data = request.get_json()

        # Validate request data using UserCreateSchema
        user_create_schema = UserCreateSchema()
        validated_data = user_create_schema.load(request_data)

        # Call user_service.create_user with validated data
        user = get_user_service().create_user(validated_data)

        # Log user creation with audit_logger
        audit_logger.log_user_operation(action="create_user", username=user.username, success=True)

        # Format response using UserProfileSchema
        user_profile_schema = UserProfileSchema()
        user_data = user_profile_schema.dump(user)

        # Return created_response with user data
        return created_response(data=user_data)

    except ValidationError as e:
        # Handle ValidationError with validation_error_response
        return validation_error_response(errors=e.messages)
    except AuthenticationError as e:
        # Handle AuthenticationError with unauthorized_response
        return unauthorized_response(message=str(e))
    except AuthorizationError as e:
        # Handle AuthorizationError with forbidden_response
        return forbidden_response(message=str(e))
    except Exception as e:
        # Handle other exceptions with server_error_response
        logger.error(f"Error creating user: {str(e)}")
        return server_error_response(message="Failed to create user")


@user_bp.route('/<int:user_id>', methods=['PUT'])
def update_user(user_id: int) -> Tuple[Dict[str, Any], int]:
    """
    Update an existing user.

    Returns:
        Tuple[Dict[str, Any], int]: JSON response with updated user data and HTTP status code
    """
    try:
        # Extract request data from request.json
        request_data = request.get_json()

        # Validate request data using UserUpdateSchema
        user_update_schema = UserUpdateSchema()
        validated_data = user_update_schema.load(request_data, partial=True)

        # Call user_service.update_user with user_id and validated data
        user = get_user_service().update_user(user_id, validated_data)

        # Log user update with audit_logger
        audit_logger.log_user_operation(action="update_user", username=user.username, success=True)

        # Format response using UserProfileSchema
        user_profile_schema = UserProfileSchema()
        user_data = user_profile_schema.dump(user)

        # Return success_response with updated user data
        return success_response(data=user_data)

    except NotFoundError as e:
        # Handle NotFoundError with not_found_response
        return not_found_response(resource_type="User", resource_id=user_id)
    except ValidationError as e:
        # Handle ValidationError with validation_error_response
        return validation_error_response(errors=e.messages)
    except AuthenticationError as e:
        # Handle AuthenticationError with unauthorized_response
        return unauthorized_response(message=str(e))
    except AuthorizationError as e:
        # Handle AuthorizationError with forbidden_response
        return forbidden_response(message=str(e))
    except Exception as e:
        # Handle other exceptions with server_error_response
        logger.error(f"Error updating user: {str(e)}")
        return server_error_response(message="Failed to update user")


@user_bp.route('/<int:user_id>', methods=['DELETE'])
def delete_user(user_id: int) -> Tuple[Dict[str, Any], int]:
    """
    Delete a user account.

    Returns:
        Tuple[Dict[str, Any], int]: JSON response confirming deletion and HTTP status code
    """
    try:
        # Call user_service.delete_user with user_id
        get_user_service().delete_user(user_id)

        # Log user deletion with audit_logger
        audit_logger.log_user_operation(action="delete_user", username=f"user_id:{user_id}", success=True)

        # Return success_response with confirmation message
        return no_content_response()

    except NotFoundError as e:
        # Handle NotFoundError with not_found_response
        return not_found_response(resource_type="User", resource_id=user_id)
    except AuthenticationError as e:
        # Handle AuthenticationError with unauthorized_response
        return unauthorized_response(message=str(e))
    except AuthorizationError as e:
        # Handle AuthorizationError with forbidden_response
        return forbidden_response(message=str(e))
    except Exception as e:
        # Handle other exceptions with server_error_response
        logger.error(f"Error deleting user: {str(e)}")
        return server_error_response(message="Failed to delete user")


@user_bp.route('/profile', methods=['GET'])
def get_user_profile() -> Tuple[Dict[str, Any], int]:
    """
    Get the current authenticated user's profile.

    Returns:
        Tuple[Dict[str, Any], int]: JSON response with user profile data and HTTP status code
    """
    try:
        # Call user_service.get_current_user to get the current authenticated user
        user = get_user_service().get_current_user()

        # If no authenticated user, return unauthorized_response
        if not user:
            return unauthorized_response(message="No authenticated user found")

        # Format response using UserProfileSchema
        user_profile_schema = UserProfileSchema()
        user_data = user_profile_schema.dump(user)

        # Return success_response with user profile data
        return success_response(data=user_data)

    except AuthenticationError as e:
        # Handle AuthenticationError with unauthorized_response
        return unauthorized_response(message=str(e))
    except Exception as e:
        # Handle other exceptions with server_error_response
        logger.error(f"Error getting user profile: {str(e)}")
        return server_error_response(message="Failed to retrieve user profile")


@user_bp.route('/<int:user_id>/sites', methods=['GET'])
def get_user_sites(user_id: int) -> Tuple[Dict[str, Any], int]:
    """
    Get all sites a user has access to.

    Returns:
        Tuple[Dict[str, Any], int]: JSON response with user's site access data and HTTP status code
    """
    try:
        # Call user_service.get_user_sites with user_id
        sites = get_user_service().get_user_sites(user_id)

        # Return success_response with sites data
        return success_response(data={'sites': sites})

    except NotFoundError as e:
        # Handle NotFoundError with not_found_response
        return not_found_response(resource_type="User", resource_id=user_id)
    except AuthenticationError as e:
        # Handle AuthenticationError with unauthorized_response
        return unauthorized_response(message=str(e))
    except AuthorizationError as e:
        # Handle AuthorizationError with forbidden_response
        return forbidden_response(message=str(e))
    except Exception as e:
        # Handle other exceptions with server_error_response
        logger.error(f"Error getting user sites: {str(e)}")
        return server_error_response(message="Failed to retrieve user sites")


@user_bp.route('/<int:user_id>/sites', methods=['POST'])
def add_user_to_site(user_id: int) -> Tuple[Dict[str, Any], int]:
    """
    Add a user to a site with a specified role.

    Returns:
        Tuple[Dict[str, Any], int]: JSON response confirming site association and HTTP status code
    """
    try:
        # Extract request data from request.json
        request_data = request.get_json()

        # Validate request data using UserSiteSchema
        user_site_schema = UserSiteSchema()
        validated_data = user_site_schema.load(request_data)

        # Extract site_id and role from validated data
        site_id = validated_data.get('site_id')
        role = validated_data.get('role')

        # Call user_service.add_user_to_site with user_id, site_id, and role
        get_user_service().add_user_to_site(user_id, site_id, role)

        # Log site access grant with audit_logger
        audit_logger.log_user_operation(action="add_user_to_site", username=f"user_id:{user_id}", success=True, details={'site_id': site_id, 'role': role})

        # Return success_response with confirmation message
        return success_response(message="User added to site successfully")

    except NotFoundError as e:
        # Handle NotFoundError with not_found_response
        return not_found_response(resource_type="User", resource_id=user_id)
    except ValidationError as e:
        # Handle ValidationError with validation_error_response
        return validation_error_response(errors=e.messages)
    except AuthenticationError as e:
        # Handle AuthenticationError with unauthorized_response
        return unauthorized_response(message=str(e))
    except AuthorizationError as e:
        # Handle AuthorizationError with forbidden_response
        return forbidden_response(message=str(e))
    except Exception as e:
        # Handle other exceptions with server_error_response
        logger.error(f"Error adding user to site: {str(e)}")
        return server_error_response(message="Failed to add user to site")


@user_bp.route('/<int:user_id>/sites/<int:site_id>', methods=['DELETE'])
def remove_user_from_site(user_id: int, site_id: int) -> Tuple[Dict[str, Any], int]:
    """
    Remove a user from a site.

    Returns:
        Tuple[Dict[str, Any], int]: JSON response confirming site access removal and HTTP status code
    """
    try:
        # Call user_service.remove_user_from_site with user_id and site_id
        get_user_service().remove_user_from_site(user_id, site_id)

        # Log site access revocation with audit_logger
        audit_logger.log_user_operation(action="remove_user_from_site", username=f"user_id:{user_id}", success=True, details={'site_id': site_id})

        # Return success_response with confirmation message
        return no_content_response()

    except NotFoundError as e:
        # Handle NotFoundError with not_found_response
        return not_found_response(resource_type="User", resource_id=user_id)
    except AuthenticationError as e:
        # Handle AuthenticationError with unauthorized_response
        return unauthorized_response(message=str(e))
    except AuthorizationError as e:
        # Handle AuthorizationError with forbidden_response
        return forbidden_response(message=str(e))
    except Exception as e:
        # Handle other exceptions with server_error_response
        logger.error(f"Error removing user from site: {str(e)}")
        return server_error_response(message="Failed to remove user from site")


@user_bp.route('/<int:user_id>/sites/<int:site_id>/role', methods=['PUT'])
def update_user_role(user_id: int, site_id: int) -> Tuple[Dict[str, Any], int]:
    """
    Update a user's role for a specific site.

    Returns:
        Tuple[Dict[str, Any], int]: JSON response confirming role update and HTTP status code
    """
    try:
        # Extract request data from request.json
        request_data = request.get_json()

        # Validate role is provided and valid
        new_role = request_data.get('role')
        if not new_role or not UserRole.is_valid(new_role):
            return validation_error_response(errors={'role': 'Invalid role'})

        # Call user_service.update_user_role with user_id, site_id, and new_role
        get_user_service().update_user_role(user_id, site_id, new_role)

        # Log role update with audit_logger
        audit_logger.log_user_operation(action="update_user_role", username=f"user_id:{user_id}", success=True, details={'site_id': site_id, 'role': new_role})

        # Return success_response with confirmation message
        return success_response(message="User role updated successfully")

    except NotFoundError as e:
        # Handle NotFoundError with not_found_response
        return not_found_response(resource_type="User", resource_id=user_id)
    except ValidationError as e:
        # Handle ValidationError with validation_error_response
        return validation_error_response(errors=e.messages)
    except AuthenticationError as e:
        # Handle AuthenticationError with unauthorized_response
        return unauthorized_response(message=str(e))
    except AuthorizationError as e:
        # Handle AuthorizationError with forbidden_response
        return forbidden_response(message=str(e))
    except Exception as e:
        # Handle other exceptions with server_error_response
        logger.error(f"Error updating user role: {str(e)}")
        return server_error_response(message="Failed to update user role")


@user_bp.route('/<int:user_id>/password', methods=['PUT'])
def change_password(user_id: int) -> Tuple[Dict[str, Any], int]:
    """
    Change a user's password (requires current password).

    Returns:
        Tuple[Dict[str, Any], int]: JSON response confirming password change and HTTP status code
    """
    try:
        # Extract request data from request.json
        request_data = request.get_json()

        # Validate request contains current_password and new_password
        current_password = request_data.get('current_password')
        new_password = request_data.get('new_password')

        if not current_password or not new_password:
            return validation_error_response(errors={'password': 'Current and new passwords are required'})

        # Call user_service.change_password with user_id, current_password, and new_password
        get_user_service().change_password(user_id, current_password, new_password)

        # Log password change with audit_logger (without actual passwords)
        audit_logger.log_user_operation(action="change_password", username=f"user_id:{user_id}", success=True)

        # Return success_response with confirmation message
        return success_response(message="Password changed successfully")

    except NotFoundError as e:
        # Handle NotFoundError with not_found_response
        return not_found_response(resource_type="User", resource_id=user_id)
    except ValidationError as e:
        # Handle ValidationError with validation_error_response
        return validation_error_response(errors=e.messages)
    except AuthenticationError as e:
        # Handle AuthenticationError with unauthorized_response
        return unauthorized_response(message=str(e))
    except AuthorizationError as e:
        # Handle AuthorizationError with forbidden_response
        return forbidden_response(message=str(e))
    except Exception as e:
        # Handle other exceptions with server_error_response
        logger.error(f"Error changing password: {str(e)}")
        return server_error_response(message="Failed to change password")


@user_bp.route('/<int:user_id>/password/reset', methods=['POST'])
def reset_password(user_id: int) -> Tuple[Dict[str, Any], int]:
    """
    Reset a user's password (admin function, no current password needed).

    Returns:
        Tuple[Dict[str, Any], int]: JSON response confirming password reset and HTTP status code
    """
    try:
        # Extract request data from request.json
        request_data = request.get_json()

        # Validate request contains new_password
        new_password = request_data.get('new_password')

        if not new_password:
            return validation_error_response(errors={'password': 'New password is required'})

        # Call user_service.reset_password with user_id and new_password
        get_user_service().reset_password(user_id, new_password)

        # Log password reset with audit_logger (without actual password)
        audit_logger.log_user_operation(action="reset_password", username=f"user_id:{user_id}", success=True)

        # Return success_response with confirmation message
        return success_response(message="Password reset successfully")

    except NotFoundError as e:
        # Handle NotFoundError with not_found_response
        return not_found_response(resource_type="User", resource_id=user_id)
    except AuthenticationError as e:
        # Handle AuthenticationError with unauthorized_response
        return unauthorized_response(message=str(e))
    except AuthorizationError as e:
        # Handle AuthorizationError with forbidden_response
        return forbidden_response(message=str(e))
    except ValidationError as e:
        # Handle ValidationError with validation_error_response
        return validation_error_response(errors=e.messages)
    except Exception as e:
        # Handle other exceptions with server_error_response
        logger.error(f"Error resetting password: {str(e)}")
        return server_error_response(message="Failed to reset password")