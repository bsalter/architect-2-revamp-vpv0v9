"""
Core authentication service that orchestrates the authentication flow, integrating with Auth0, managing tokens, and enforcing site-scoped access control. Acts as the central service for user authentication, session management, and site context switching.
"""

from typing import Dict, List, Optional, Any, Union

from ..auth.auth0 import Auth0Client  # Auth0Client: Integration with Auth0 authentication service
from ..auth.token_service import TokenService  # TokenService: JWT token management and validation
from ..auth.user_context_service import UserContextService  # UserContextService: User context management throughout request lifecycle
from ..auth.site_context_service import SiteContextService  # SiteContextService: Site context management for site-scoped access
from ..repositories.user_repository import UserRepository  # UserRepository: Data access for user information and authentication
from ..auth.permission_service import PermissionService  # PermissionService: Authorization and permission checking
from ..utils.error_util import AuthenticationError, SiteContextError  # AuthenticationError, SiteContextError: Authentication-specific error handling
from ..logging.audit_logger import audit_logger  # audit_logger: Audit logging for authentication events
from ..logging.structured_logger import StructuredLogger  # StructuredLogger: Structured logging for authentication operations

# Initialize structured logger
logger = StructuredLogger(__name__)

class AuthService:
    """
    Core service for authentication and site context management that coordinates between various authentication components
    """

    def __init__(
        self,
        auth0_client: Auth0Client,
        token_service: TokenService,
        user_context_service: UserContextService,
        site_context_service: SiteContextService,
        user_repository: UserRepository,
        permission_service: PermissionService = None
    ):
        """
        Initialize the authentication service with necessary dependencies
        """
        self._auth0_client = auth0_client
        self._token_service = token_service
        self._user_context_service = user_context_service
        self._site_context_service = site_context_service
        self._user_repository = user_repository
        self._permission_service = permission_service

        logger.info("AuthService initialized")

    def login(self, username: str, password: str) -> Dict[str, Any]:
        """
        Authenticate user and initialize session context
        """
        try:
            logger.debug(f"Attempting authentication for user: {username}")

            # Try to authenticate with Auth0
            try:
                auth_result = self._auth0_client.authenticate(username, password)
                logger.debug(f"Auth0 authentication successful for user: {username}")
            except AuthenticationError:
                # If Auth0 authentication fails, try local authentication
                logger.debug(f"Auth0 authentication failed, attempting local authentication for user: {username}")
                user = self._user_repository.authenticate(username, password)
                auth_result = {
                    'access_token': self._token_service.create_access_token(user.to_dict(), user.get_site_ids()),
                    'id_token': None,  # No ID token for local auth
                    'refresh_token': self._token_service.create_refresh_token(str(user.id)),
                    'expires_in': 3600,  # Example expiration time
                    'user': user.to_dict(),
                    'site_access': user.get_site_ids()
                }
                logger.debug(f"Local authentication successful for user: {username}")

            # Extract token payload and user information from authentication result
            token_payload = self._token_service.extract_token_payload(auth_result['access_token'])
            user_info = auth_result['user']

            # Set user context from token
            self._user_context_service.set_user_context_from_token(token_payload)

            # Get user's available sites for site selection
            available_sites = auth_result['site_access']

            # If user has only one site, automatically set site context
            if len(available_sites) == 1:
                self._site_context_service.set_site_context(available_sites[0])
                logger.debug(f"Automatically set site context to site ID: {available_sites[0]} for user: {username}")

            # Audit log the login event
            audit_logger.log_authentication(
                action='login',
                username=username,
                success=True,
                details={'user_id': user_info['user_id']}
            )

            logger.info(f"User {username} successfully logged in")
            return {
                'access_token': auth_result['access_token'],
                'id_token': auth_result['id_token'],
                'refresh_token': auth_result['refresh_token'],
                'expires_in': auth_result['expires_in'],
                'user': user_info,
                'site_access': available_sites
            }

        except AuthenticationError as e:
            # Audit log the failed login event
            audit_logger.log_authentication(
                action='login',
                username=username,
                success=False,
                details={'error': str(e)}
            )
            logger.warning(f"Authentication failed for user {username}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"An unexpected error occurred during login for user {username}: {str(e)}")
            raise AuthenticationError(f"An unexpected error occurred during login: {str(e)}")

    def logout(self, token: str) -> bool:
        """
        Terminate user session and invalidate token
        """
        try:
            logger.debug("Attempting logout")

            # Validate token
            token_payload = self._token_service.validate_token(token)
            if not token_payload:
                raise AuthenticationError("Invalid token")

            # Blacklist token
            self._token_service.blacklist_token(token)

            # Clear user context
            self._user_context_service.clear_user_context()

            # Clear site context
            self._site_context_service.clear_site_context()

            # Audit log the logout event
            user_id = token_payload.get('sub')
            audit_logger.log_authentication(
                action='logout',
                username=token_payload.get('username', 'unknown'),
                success=True,
                details={'user_id': user_id}
            )

            logger.info("Logout successful")
            return True

        except AuthenticationError as e:
            logger.warning(f"Logout failed: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"An unexpected error occurred during logout: {str(e)}")
            raise AuthenticationError(f"An unexpected error occurred during logout: {str(e)}")

    def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Obtain new access token using refresh token
        """
        try:
            logger.debug("Attempting token refresh")

            # Refresh token using token service
            refreshed_token = self._token_service.refresh_access_token(refresh_token)

            # Extract token payload
            token_payload = self._token_service.extract_token_payload(refreshed_token['access_token'])

            # Update user context with new token data
            self._user_context_service.set_user_context_from_token(token_payload)

            logger.info("Token refresh successful")
            return refreshed_token

        except AuthenticationError as e:
            logger.warning(f"Token refresh failed: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"An unexpected error occurred during token refresh: {str(e)}")
            raise AuthenticationError(f"An unexpected error occurred during token refresh: {str(e)}")

    def validate_token(self, token: str) -> Dict[str, Any]:
        """
        Validate JWT token and establish user context if valid
        """
        try:
            logger.debug("Validating token")

            # Validate token using token service
            token_payload = self._token_service.validate_token(token)
            if not token_payload:
                raise AuthenticationError("Invalid token")

            # Set user context from token
            self._user_context_service.set_user_context_from_token(token_payload)

            logger.info("Token validation successful")
            return token_payload

        except AuthenticationError as e:
            logger.warning(f"Token validation failed: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"An unexpected error occurred during token validation: {str(e)}")
            raise AuthenticationError(f"An unexpected error occurred during token validation: {str(e)}")

    def switch_site(self, site_id: int, token: str = None) -> Dict[str, Any]:
        """
        Switch the active site context for the current user session
        """
        try:
            logger.debug(f"Attempting to switch site to ID: {site_id}")

            # If token provided, validate before proceeding
            if token:
                self.validate_token(token)

            # Verify user has access to requested site
            if not self._site_context_service.verify_site_access(site_id):
                raise SiteContextError(f"User does not have access to site {site_id}")

            # Clear current site context
            self._site_context_service.clear_site_context()

            # Set new site context
            self._site_context_service.set_site_context(site_id)

            # Get updated site context information
            site_context = self._site_context_service.get_current_site_context()

            # Audit log the site switch event
            user_id = self._user_context_service.get_current_user_id()
            audit_logger.log_authorization(
                action='switch_site',
                resource_type='site',
                resource_id=str(site_id),
                success=True,
                details={'user_id': user_id}
            )

            logger.info(f"Successfully switched site to ID: {site_id}")
            return site_context.to_dict()

        except SiteContextError as e:
            logger.warning(f"Site switch failed: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"An unexpected error occurred during site switch: {str(e)}")
            raise SiteContextError(f"An unexpected error occurred during site switch: {str(e)}")

    def get_current_user(self) -> Dict[str, Any]:
        """
        Get the current authenticated user's information
        """
        try:
            logger.debug("Attempting to get current user")

            # Get current user from user context service
            user = self._user_context_service.get_current_user()
            if not user:
                raise AuthenticationError("No authenticated user found")

            # Convert user model to dictionary representation
            user_data = user.to_dict()

            logger.info(f"Successfully retrieved current user: {user.username} (ID: {user.id})")
            return user_data

        except AuthenticationError as e:
            logger.warning(f"Failed to get current user: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"An unexpected error occurred while getting current user: {str(e)}")
            raise AuthenticationError(f"An unexpected error occurred while getting current user: {str(e)}")

    def get_available_sites(self) -> List[Dict[str, Any]]:
        """
        Get all sites available to the current authenticated user
        """
        try:
            logger.debug("Attempting to get available sites")

            # Check if user is authenticated
            if not self._user_context_service.is_authenticated():
                logger.warning("Cannot get available sites - user not authenticated")
                return []

            # Use site context service to get available sites
            sites = self._site_context_service.get_available_sites()

            logger.info(f"Successfully retrieved {len(sites)} available sites")
            return sites

        except Exception as e:
            logger.error(f"An unexpected error occurred while getting available sites: {str(e)}")
            return []

    def request_password_reset(self, email: str) -> bool:
        """
        Initiate password reset process for a user
        """
        try:
            logger.debug(f"Attempting password reset request for email: {email}")

            # Attempt to find user by email
            user = self._user_repository.find_by_email(email)

            # Initiate password reset process
            if user:
                # For Auth0 users, call appropriate Auth0 endpoint
                if self._auth0_client:
                    self._auth0_client.request_password_reset(email)
                    logger.debug(f"Password reset requested via Auth0 for email: {email}")
                else:
                    # For local users, generate reset token and send email
                    logger.warning("Local password reset not implemented")
            else:
                logger.debug(f"No user found with email: {email}")

            # Always return True regardless of whether email exists for security
            logger.info("Password reset request completed (email details redacted in logs)")
            return True

        except Exception as e:
            logger.error(f"An unexpected error occurred during password reset request: {str(e)}")
            return True

    def is_authenticated(self) -> bool:
        """
        Check if current request has a valid authenticated user
        """
        try:
            # Delegate to user_context_service.is_authenticated()
            is_authenticated = self._user_context_service.is_authenticated()

            logger.debug(f"Authentication check: {'authenticated' if is_authenticated else 'not authenticated'}")
            return is_authenticated
        except Exception as e:
            logger.error(f"An unexpected error occurred during authentication check: {str(e)}")
            return False