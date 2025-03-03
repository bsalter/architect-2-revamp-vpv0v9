"""
Defines Marshmallow schemas for user-related data validation and serialization in the Interaction Management System.
Includes schemas for user creation, updating, profile access, site association management, and paginated user listings.
Implements validation rules for user data integrity and enforces site-scoped access control.
"""

from marshmallow import Schema, fields, validates, validates_schema, ValidationError, post_load, pre_load, post_dump
# marshmallow version 3.20.1
from typing import Dict, List, Any, Optional

from ...utils.enums import UserRole
from .auth_schemas import EMAIL_REGEX, USERNAME_REGEX, PASSWORD_MIN_LENGTH

# Constants for validation
USERNAME_MIN_LENGTH = 3
USERNAME_MAX_LENGTH = 50
EMAIL_MAX_LENGTH = 100


class UserSchema(Schema):
    """Schema for complete user serialization and deserialization with all fields."""
    id = fields.Integer()
    username = fields.String()
    email = fields.String()
    password = fields.String()
    last_login = fields.DateTime()
    created_at = fields.DateTime()
    updated_at = fields.DateTime()
    sites = fields.List(fields.Nested("SiteSchema", exclude=("users",)))
    
    def __init__(self, *args, **kwargs):
        """Initialize the user schema with settings for load and dump operations."""
        super().__init__(*args, **kwargs)
        # Password should never be returned in responses
        self.load_only = ['password']
        # These fields are read-only and should not be modifiable in requests
        self.dump_only = ['id', 'created_at', 'updated_at', 'last_login']
    
    @validates('username')
    def validate_username(self, username: str) -> str:
        """Validate username format and uniqueness."""
        if not username or username.strip() == '':
            raise ValidationError("Username is required")
        
        if len(username) < USERNAME_MIN_LENGTH or len(username) > USERNAME_MAX_LENGTH:
            raise ValidationError(f"Username must be between {USERNAME_MIN_LENGTH} and {USERNAME_MAX_LENGTH} characters")
        
        if not USERNAME_REGEX.match(username):
            raise ValidationError("Username must contain only letters, numbers, and underscores")
        
        return username
    
    @validates('email')
    def validate_email(self, email: str) -> str:
        """Validate email format and uniqueness."""
        if not email or email.strip() == '':
            raise ValidationError("Email is required")
        
        if len(email) > EMAIL_MAX_LENGTH:
            raise ValidationError(f"Email cannot exceed {EMAIL_MAX_LENGTH} characters")
        
        if not EMAIL_REGEX.match(email):
            raise ValidationError("Invalid email format")
        
        return email


class UserCreateSchema(Schema):
    """Schema for validating user creation requests with password requirements."""
    username = fields.String(required=True)
    email = fields.String(required=True)
    password = fields.String(required=True)
    confirm_password = fields.String(required=True)
    site_ids = fields.List(fields.Integer(), required=False)
    site_roles = fields.Dict(keys=fields.String(), values=fields.String(), required=False)
    
    def __init__(self, *args, **kwargs):
        """Initialize the user creation schema."""
        super().__init__(*args, **kwargs)
        self.load_only = ['password', 'confirm_password']
    
    @validates('password')
    def validate_password(self, password: str) -> str:
        """Validate password complexity requirements."""
        if not password or password.strip() == '':
            raise ValidationError("Password is required")
        
        if len(password) < PASSWORD_MIN_LENGTH:
            raise ValidationError(f"Password must be at least {PASSWORD_MIN_LENGTH} characters long")
        
        # Check for uppercase letter
        if not any(char.isupper() for char in password):
            raise ValidationError("Password must contain at least one uppercase letter")
        
        # Check for lowercase letter
        if not any(char.islower() for char in password):
            raise ValidationError("Password must contain at least one lowercase letter")
        
        # Check for digit
        if not any(char.isdigit() for char in password):
            raise ValidationError("Password must contain at least one digit")
        
        # Check for special character
        if not any(not char.isalnum() for char in password):
            raise ValidationError("Password must contain at least one special character")
        
        return password
    
    @validates_schema
    def validate_passwords_match(self, data: Dict, **kwargs) -> Dict:
        """Validate that password and confirm_password match."""
        password = data.get('password')
        confirm_password = data.get('confirm_password')
        
        if password and confirm_password and password != confirm_password:
            raise ValidationError("Passwords do not match", field_name="confirm_password")
        
        return data
    
    @validates('site_roles')
    def validate_site_roles(self, site_roles: Dict) -> Dict:
        """Validate site roles are valid UserRole values."""
        if not site_roles:
            return site_roles
        
        for site_id, role in site_roles.items():
            try:
                # Validate that site_id is a valid integer (when deserialized from JSON)
                int(site_id)
            except (ValueError, TypeError):
                raise ValidationError(f"Invalid site ID: {site_id}")
            
            # Validate that the role is valid
            if not UserRole.is_valid(role):
                valid_roles = ", ".join([UserRole.SITE_ADMIN.value, UserRole.EDITOR.value, UserRole.VIEWER.value])
                raise ValidationError(f"Invalid role: {role}. Must be one of: {valid_roles}")
        
        return site_roles


class UserUpdateSchema(Schema):
    """Schema for validating user update requests with optional fields."""
    username = fields.String()
    email = fields.String()
    password = fields.String()
    confirm_password = fields.String()
    site_ids = fields.List(fields.Integer())
    site_roles = fields.Dict(keys=fields.String(), values=fields.String())
    
    def __init__(self, *args, **kwargs):
        """Initialize the user update schema with partial loading."""
        super().__init__(*args, **kwargs)
        self.partial = True  # Allow partial updates
        self.load_only = ['password', 'confirm_password']
    
    @validates_schema
    def validate_password_update(self, data: Dict, **kwargs) -> Dict:
        """Validate password update when provided."""
        password = data.get('password')
        confirm_password = data.get('confirm_password')
        
        # Only perform validation if password is being updated
        if password:
            # Require confirmation password
            if not confirm_password:
                raise ValidationError("Confirm password is required when updating password", field_name="confirm_password")
            
            # Check passwords match
            if password != confirm_password:
                raise ValidationError("Passwords do not match", field_name="confirm_password")
            
            # Validate password complexity
            if len(password) < PASSWORD_MIN_LENGTH:
                raise ValidationError(f"Password must be at least {PASSWORD_MIN_LENGTH} characters long")
            
            # Check for uppercase letter
            if not any(char.isupper() for char in password):
                raise ValidationError("Password must contain at least one uppercase letter")
            
            # Check for lowercase letter
            if not any(char.islower() for char in password):
                raise ValidationError("Password must contain at least one lowercase letter")
            
            # Check for digit
            if not any(char.isdigit() for char in password):
                raise ValidationError("Password must contain at least one digit")
            
            # Check for special character
            if not any(not char.isalnum() for char in password):
                raise ValidationError("Password must contain at least one special character")
        
        return data
    
    @validates('site_roles')
    def validate_site_roles(self, site_roles: Dict) -> Dict:
        """Validate site roles are valid UserRole values when provided."""
        if not site_roles:
            return site_roles
        
        for site_id, role in site_roles.items():
            try:
                # Validate that site_id is a valid integer (when deserialized from JSON)
                int(site_id)
            except (ValueError, TypeError):
                raise ValidationError(f"Invalid site ID: {site_id}")
            
            # Validate that the role is valid
            if not UserRole.is_valid(role):
                valid_roles = ", ".join([UserRole.SITE_ADMIN.value, UserRole.EDITOR.value, UserRole.VIEWER.value])
                raise ValidationError(f"Invalid role: {role}. Must be one of: {valid_roles}")
        
        return site_roles


class UserProfileSchema(Schema):
    """Schema for serializing user profile data without sensitive information."""
    id = fields.Integer()
    username = fields.String()
    email = fields.String()
    last_login = fields.DateTime()
    created_at = fields.DateTime()
    site_ids = fields.List(fields.Integer())
    
    def __init__(self, *args, **kwargs):
        """Initialize the user profile schema."""
        super().__init__(*args, **kwargs)
        self.dump_only = ['id', 'username', 'email', 'last_login', 'created_at', 'site_ids']
    
    @post_dump
    def format_site_ids(self, data: Dict) -> Dict:
        """Extract site IDs from user's site associations."""
        if 'sites' in data:
            data['site_ids'] = [site['id'] for site in data['sites']]
        return data


class UserSiteSchema(Schema):
    """Schema for user-site association data with role information."""
    user_id = fields.Integer(required=True)
    site_id = fields.Integer(required=True)
    role = fields.String(required=True)
    created_at = fields.DateTime()
    updated_at = fields.DateTime()
    
    def __init__(self, *args, **kwargs):
        """Initialize the user-site schema."""
        super().__init__(*args, **kwargs)
        self.dump_only = ['created_at', 'updated_at']
    
    @validates('role')
    def validate_role(self, role: str) -> str:
        """Validate that role is a valid UserRole value."""
        if not role or role.strip() == '':
            raise ValidationError("Role is required")
        
        if not UserRole.is_valid(role):
            valid_roles = ", ".join([UserRole.SITE_ADMIN.value, UserRole.EDITOR.value, UserRole.VIEWER.value])
            raise ValidationError(f"Invalid role: {role}. Must be one of: {valid_roles}")
        
        return role


class UserListSchema(Schema):
    """Schema for paginated user listings with metadata."""
    users = fields.List(fields.Nested(UserSchema))
    total = fields.Integer()
    page = fields.Integer()
    per_page = fields.Integer()
    pages = fields.Integer()
    
    def __init__(self, *args, **kwargs):
        """Initialize the user list schema."""
        super().__init__(*args, **kwargs)