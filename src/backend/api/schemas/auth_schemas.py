"""
Defines Marshmallow schemas for authentication-related requests and responses in the Interaction Management System.
These schemas validate input data and serialize output data for authentication endpoints including login, token refresh,
logout, and password reset. They also support the site-scoping access control feature.
"""

from marshmallow import Schema, fields, validates, validates_schema, ValidationError, post_load, post_dump
# marshmallow version 3.20.1
from typing import Dict, List, Any, Optional  # standard library
import re  # standard library

from ...auth.site_context_service import SiteContext

# Regular expressions for validation
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
USERNAME_REGEX = re.compile(r'^[a-zA-Z0-9_]{3,50}$')
PASSWORD_MIN_LENGTH = 10


class LoginSchema(Schema):
    """Schema for validating user login requests"""
    username = fields.String(required=True)
    password = fields.String(required=True)
    
    def __init__(self, *args, **kwargs):
        """Initialize the login schema"""
        super().__init__(*args, **kwargs)
    
    @validates('username')
    def validate_username(self, username: str) -> str:
        """Validate username format"""
        if not username or username.strip() == '':
            raise ValidationError('Username is required')
        
        if not USERNAME_REGEX.match(username):
            raise ValidationError('Username must be between 3-50 characters and can only contain letters, numbers, and underscores')
        
        return username
    
    @validates('password')
    def validate_password(self, password: str) -> str:
        """Validate password is provided"""
        if not password or password.strip() == '':
            raise ValidationError('Password is required')
        
        return password


class TokenSchema(Schema):
    """Schema for serializing authentication token response data"""
    access_token = fields.String(required=True)
    refresh_token = fields.String(required=True)
    expires_in = fields.Integer(required=True)
    user = fields.Dict(required=True)
    site_ids = fields.List(fields.Integer(), required=True)
    site_context = fields.Dict(required=False)
    token_type = fields.String(required=True, default="Bearer")
    
    def __init__(self, *args, **kwargs):
        """Initialize the token schema"""
        super().__init__(*args, **kwargs)
    
    @post_dump
    def format_site_context(self, data: Dict) -> Dict:
        """Format the site context object to a serializable dictionary"""
        if 'site_context' in data and isinstance(data['site_context'], SiteContext):
            data['site_context'] = data['site_context'].to_dict()
        return data


class RefreshSchema(Schema):
    """Schema for validating token refresh requests"""
    refresh_token = fields.String(required=True)
    
    def __init__(self, *args, **kwargs):
        """Initialize the refresh schema"""
        super().__init__(*args, **kwargs)
    
    @validates('refresh_token')
    def validate_refresh_token(self, refresh_token: str) -> str:
        """Validate refresh token is provided"""
        if not refresh_token or refresh_token.strip() == '':
            raise ValidationError('Refresh token is required')
        
        return refresh_token


class LogoutSchema(Schema):
    """Schema for validating logout requests"""
    token = fields.String(required=True)
    
    def __init__(self, *args, **kwargs):
        """Initialize the logout schema"""
        super().__init__(*args, **kwargs)


class SiteSelectionSchema(Schema):
    """Schema for validating site selection requests"""
    site_id = fields.Integer(required=True)
    
    def __init__(self, *args, **kwargs):
        """Initialize the site selection schema"""
        super().__init__(*args, **kwargs)
    
    @validates('site_id')
    def validate_site_id(self, site_id: int) -> int:
        """Validate site ID is provided and is a positive integer"""
        if site_id is None:
            raise ValidationError('Site ID is required')
        
        if not isinstance(site_id, int) or site_id <= 0:
            raise ValidationError('Site ID must be a positive integer')
        
        return site_id


class PasswordResetRequestSchema(Schema):
    """Schema for validating password reset requests"""
    email = fields.String(required=True)
    
    def __init__(self, *args, **kwargs):
        """Initialize the password reset request schema"""
        super().__init__(*args, **kwargs)
    
    @validates('email')
    def validate_email(self, email: str) -> str:
        """Validate email format"""
        if not email or email.strip() == '':
            raise ValidationError('Email is required')
        
        if not EMAIL_REGEX.match(email):
            raise ValidationError('Invalid email format')
        
        return email


class PasswordResetConfirmSchema(Schema):
    """Schema for validating password reset confirmation requests"""
    token = fields.String(required=True)
    new_password = fields.String(required=True)
    confirm_password = fields.String(required=True)
    
    def __init__(self, *args, **kwargs):
        """Initialize the password reset confirmation schema"""
        super().__init__(*args, **kwargs)
    
    @validates('token')
    def validate_token(self, token: str) -> str:
        """Validate reset token is provided"""
        if not token or token.strip() == '':
            raise ValidationError('Reset token is required')
        
        return token
    
    @validates('new_password')
    def validate_new_password(self, password: str) -> str:
        """Validate new password format and strength"""
        if not password or password.strip() == '':
            raise ValidationError('New password is required')
        
        if len(password) < PASSWORD_MIN_LENGTH:
            raise ValidationError(f'Password must be at least {PASSWORD_MIN_LENGTH} characters long')
        
        # Check for password complexity
        character_types = 0
        if re.search(r'[A-Z]', password): character_types += 1
        if re.search(r'[a-z]', password): character_types += 1
        if re.search(r'[0-9]', password): character_types += 1
        if re.search(r'[^A-Za-z0-9]', password): character_types += 1
        
        if character_types < 3:
            raise ValidationError('Password must contain at least 3 of the following: uppercase letters, lowercase letters, numbers, and special characters')
        
        return password
    
    @validates_schema
    def validate_passwords_match(self, data: Dict, **kwargs) -> Dict:
        """Validate that new password and confirmation password match"""
        new_password = data.get('new_password')
        confirm_password = data.get('confirm_password')
        
        if new_password and confirm_password and new_password != confirm_password:
            raise ValidationError('Passwords do not match', field_name='confirm_password')
        
        return data