# src/backend/api/controllers/auth_controller.py
"""Controller for authentication endpoints in the Interaction Management System that processes authentication requests, manages user sessions, and handles site context selection. Provides RESTful API endpoints for login, logout, token refresh, and site context switching."""

from typing import Dict, Any, Optional, Tuple  # typing: standard library
from flask import Blueprint, request, jsonify, current_app  # flask: version 2.3.2
from marshmallow import ValidationError  # marshmallow: version 3.20.1

from ...services.auth_service import AuthService  # AuthService: Core service for handling authentication operations
from ..schemas.auth_schemas import LoginSchema, TokenSchema, RefreshSchema, LogoutSchema, SiteSelectionSchema, PasswordResetRequestSchema  # LoginSchema, TokenSchema, RefreshSchema, LogoutSchema, SiteSelectionSchema, PasswordResetRequestSchema: Schemas for validating authentication-related requests and responses
from ..helpers.response import success_response, error_response, validation_error_response, unauthorized_response, site_context_error_response  # success_response, error_response, validation_error_response, unauthorized_response, site_context_error_response: Standardized response formatting functions
from ...logging.audit_logger import AuditLogger, AUTH_CATEGORY  # AuditLogger, AUTH_CATEGORY: Audit logging for authentication events
from ...logging.structured_logger import StructuredLogger  # StructuredLogger: Structured logging for controller operations
from ...utils.error_util import AuthenticationError, SiteContextError  # AuthenticationError, SiteContextError: Exception types for authentication and site context errors

# Create a Flask Blueprint for authentication routes
auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

# Initialize structured logger for this module
logger = StructuredLogger(__name__)


@auth_bp.route('/login', methods=['POST'])
def login() -> Tuple[Dict[str, Any], int]:
    """Handle user login requests, authenticating credentials and returning JWT tokens

    Returns:
        Tuple[Dict[str, Any], int]: JSON response with authentication token data and HTTP status code
    """
    try:
        # Extract request data from request.json
        request_data = request.get_json()

        # Validate request data using LoginSchema
        validated_data = LoginSchema().load(request_data)

        # Extract username and password from validated data
        username = validated_data['username']
        password = validated_data['password']

        # Call auth_service.login to authenticate user
        auth_service = get_auth_service()
        auth_result = auth_service.login(username, password)

        # Audit log the login event
        audit_logger = current_app.extensions['audit_logger']
        audit_logger.log_authentication(
            action='login',
            username=username,
            success=True,
            details={'user_id': auth_result['user']['user_id']}
        )

        # Return success_response with token data
        return success_response(data=auth_result)

    except ValidationError as e:
        # If validation fails, return validation_error_response with errors
        logger.warning(f"Validation error during login: {str(e)}")
        return validation_error_response(errors=e.messages)

    except AuthenticationError as e:
        # If AuthenticationError occurs, log error and return unauthorized_response
        logger.warning(f"Authentication failed for user: {str(e)}")
        return unauthorized_response(message=str(e))

    except Exception as e:
        # If other exceptions occur, log error and return appropriate error response
        logger.error(f"An unexpected error occurred during login: {str(e)}")
        return error_response(message="An unexpected error occurred", error_type=ErrorType.SERVER)


@auth_bp.route('/refresh', methods=['POST'])
def refresh_token() -> Tuple[Dict[str, Any], int]:
    """Handle token refresh requests to extend session without re-authentication

    Returns:
        Tuple[Dict[str, Any], int]: JSON response with new token data and HTTP status code
    """
    try:
        # Extract request data from request.json
        request_data = request.get_json()

        # Validate request data using RefreshSchema
        validated_data = RefreshSchema().load(request_data)

        # Extract refresh_token from validated data
        refresh_token = validated_data['refresh_token']

        # Call auth_service.refresh_token to get new access token
        auth_service = get_auth_service()
        auth_result = auth_service.refresh_token(refresh_token)

        # Return success_response with new token data
        return success_response(data=auth_result)

    except ValidationError as e:
        # If validation fails, return validation_error_response with errors
        logger.warning(f"Validation error during token refresh: {str(e)}")
        return validation_error_response(errors=e.messages)

    except AuthenticationError as e:
        # If AuthenticationError occurs, log error and return unauthorized_response
        logger.warning(f"Authentication failed during token refresh: {str(e)}")
        return unauthorized_response(message=str(e))

    except Exception as e:
        # If other exceptions occur, log error and return appropriate error response
        logger.error(f"An unexpected error occurred during token refresh: {str(e)}")
        return error_response(message="An unexpected error occurred", error_type=ErrorType.SERVER)


@auth_bp.route('/logout', methods=['POST'])
def logout() -> Tuple[Dict[str, Any], int]:
    """Handle user logout requests, invalidating current session token

    Returns:
        Tuple[Dict[str, Any], int]: JSON response confirming logout and HTTP status code
    """
    try:
        # Extract request data from request.json
        request_data = request.get_json()

        # Validate request data using LogoutSchema
        validated_data = LogoutSchema().load(request_data)

        # Extract token from validated data
        token = validated_data['token']

        # Call auth_service.logout to invalidate the token
        auth_service = get_auth_service()
        auth_service.logout(token)

        # Return success_response with confirmation message
        return success_response(message="Logout successful")

    except ValidationError as e:
        # If validation fails, return validation_error_response with errors
        logger.warning(f"Validation error during logout: {str(e)}")
        return validation_error_response(errors=e.messages)

    except AuthenticationError as e:
        # If AuthenticationError occurs, log error and return unauthorized_response
        logger.warning(f"Authentication error during logout: {str(e)}")
        return unauthorized_response(message=str(e))

    except Exception as e:
        # If other exceptions occur, log error and return appropriate error response
        logger.error(f"An unexpected error occurred during logout: {str(e)}")
        return error_response(message="An unexpected error occurred", error_type=ErrorType.SERVER)


@auth_bp.route('/sites', methods=['GET'])
def get_user_sites() -> Tuple[Dict[str, Any], int]:
    """Get all sites available to the current authenticated user

    Returns:
        Tuple[Dict[str, Any], int]: JSON response with user's available sites and HTTP status code
    """
    try:
        # Get token from request Authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            logger.warning("Authorization header is missing")
            return unauthorized_response(message="Authorization header is missing")

        token = _extract_token_from_header()
        if not token:
            logger.warning("Invalid authorization header format")
            return unauthorized_response(message="Invalid authorization header format")

        # Call auth_service.validate_token to verify token
        auth_service = get_auth_service()
        auth_service.validate_token(token)

        # Call auth_service.get_available_sites to get user's sites
        sites = auth_service.get_available_sites()

        # Return success_response with sites data
        return success_response(data={'sites': sites})

    except AuthenticationError as e:
        # If AuthenticationError occurs, log error and return unauthorized_response
        logger.warning(f"Authentication error while getting user sites: {str(e)}")
        return unauthorized_response(message=str(e))

    except Exception as e:
        # If other exceptions occur, log error and return appropriate error response
        logger.error(f"An unexpected error occurred while getting user sites: {str(e)}")
        return error_response(message="An unexpected error occurred", error_type=ErrorType.SERVER)


@auth_bp.route('/site', methods=['POST'])
def switch_site() -> Tuple[Dict[str, Any], int]:
    """Switch the current site context for the authenticated user's session

    Returns:
        Tuple[Dict[str, Any], int]: JSON response with updated site context and HTTP status code
    """
    try:
        # Extract request data from request.json
        request_data = request.get_json()

        # Validate request data using SiteSelectionSchema
        validated_data = SiteSelectionSchema().load(request_data)

        # Extract site_id from validated data
        site_id = validated_data['site_id']

        # Get token from request Authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            logger.warning("Authorization header is missing")
            return unauthorized_response(message="Authorization header is missing")

        token = _extract_token_from_header()
        if not token:
            logger.warning("Invalid authorization header format")
            return unauthorized_response(message="Invalid authorization header format")

        # Call auth_service.switch_site with site_id and token
        auth_service = get_auth_service()
        site_context = auth_service.switch_site(site_id, token)

        # Return success_response with updated site context
        return success_response(data={'site_context': site_context})

    except ValidationError as e:
        # If validation fails, return validation_error_response with errors
        logger.warning(f"Validation error during site switch: {str(e)}")
        return validation_error_response(errors=e.messages)

    except AuthenticationError as e:
        # If AuthenticationError occurs, log error and return unauthorized_response
        logger.warning(f"Authentication error during site switch: {str(e)}")
        return unauthorized_response(message=str(e))

    except SiteContextError as e:
        # If SiteContextError occurs, log error and return site_context_error_response
        logger.warning(f"Site context error during site switch: {str(e)}")
        return site_context_error_response(message=str(e))

    except Exception as e:
        # If other exceptions occur, log error and return appropriate error response
        logger.error(f"An unexpected error occurred during site switch: {str(e)}")
        return error_response(message="An unexpected error occurred", error_type=ErrorType.SERVER)


@auth_bp.route('/profile', methods=['GET'])
def get_current_user() -> Tuple[Dict[str, Any], int]:
    """Get the current authenticated user's profile information

    Returns:
        Tuple[Dict[str, Any], int]: JSON response with user profile data and HTTP status code
    """
    try:
        # Get token from request Authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            logger.warning("Authorization header is missing")
            return unauthorized_response(message="Authorization header is missing")

        token = _extract_token_from_header()
        if not token:
            logger.warning("Invalid authorization header format")
            return unauthorized_response(message="Invalid authorization header format")

        # Call auth_service.validate_token to verify token
        auth_service = get_auth_service()
        auth_service.validate_token(token)

        # Call auth_service.get_current_user to get user profile
        user_profile = auth_service.get_current_user()

        # Return success_response with user profile data
        return success_response(data={'user': user_profile})

    except AuthenticationError as e:
        # If AuthenticationError occurs, log error and return unauthorized_response
        logger.warning(f"Authentication error while getting user profile: {str(e)}")
        return unauthorized_response(message=str(e))

    except Exception as e:
        # If other exceptions occur, log error and return appropriate error response
        logger.error(f"An unexpected error occurred while getting user profile: {str(e)}")
        return error_response(message="An unexpected error occurred", error_type=ErrorType.SERVER)


@auth_bp.route('/password/reset', methods=['POST'])
def request_password_reset() -> Tuple[Dict[str, Any], int]:
    """Request a password reset email for a user account

    Returns:
        Tuple[Dict[str, Any], int]: JSON response confirming request and HTTP status code
    """
    try:
        # Extract request data from request.json
        request_data = request.get_json()

        # Validate request data using PasswordResetRequestSchema
        validated_data = PasswordResetRequestSchema().load(request_data)

        # Extract email from validated data
        email = validated_data['email']

        # Call auth_service.request_password_reset with email
        auth_service = get_auth_service()
        auth_service.request_password_reset(email)

        # Return success_response with confirmation message (regardless of email existence)
        return success_response(message="Password reset request initiated successfully. Please check your email for further instructions.")

    except ValidationError as e:
        # If validation fails, return validation_error_response with errors
        logger.warning(f"Validation error during password reset request: {str(e)}")
        return validation_error_response(errors=e.messages)

    except Exception as e:
        # If exceptions occur, log error but still return success response for security
        logger.error(f"An unexpected error occurred during password reset request: {str(e)}")
        return success_response(message="Password reset request initiated successfully. Please check your email for further instructions.")


def get_auth_service() -> AuthService:
    """Helper function to get the authentication service instance from app context

    Returns:
        AuthService: Authentication service instance
    """
    # Get auth_service from current_app.extensions
    auth_service = current_app.extensions['auth_service']

    # Return the auth_service instance
    return auth_service


def _extract_token_from_header() -> Optional[str]:
    """Extract JWT token from Authorization header

    Returns:
        Optional[str]: Token string if present, None otherwise
    """
    # Get Authorization header from request.headers
    auth_header = request.headers.get('Authorization')

    # If header not present, return None
    if not auth_header:
        return None

    # Check if header starts with 'Bearer '
    if not auth_header.startswith('Bearer '):
        return None

    # Extract and return token part after 'Bearer '
    return auth_header[7:]