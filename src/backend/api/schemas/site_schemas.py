"""
Site Schemas Module

This module defines Marshmallow schemas for site-related data structures, providing
validation, serialization, and deserialization for Site API endpoints. These schemas
enforce validation rules for site fields and support the site-scoped access control
mechanism that is central to the application's multi-tenant architecture.
"""

import marshmallow as ma  # marshmallow 3.20.1
from marshmallow import fields, validates, pre_load, post_load, INCLUDE
from ...utils.validation_util import ValidationError, sanitize_input
from ...utils.enums import UserRole
from ...utils.string_util import is_empty, is_valid_length

# Constants for site field validation
SITE_NAME_MIN_LENGTH = 3
SITE_NAME_MAX_LENGTH = 100
SITE_DESCRIPTION_MAX_LENGTH = 500


class SiteBaseSchema(ma.Schema):
    """
    Base schema for site data, defining common fields and validations used across site schemas.
    """
    name = fields.String(required=True)
    description = fields.String(required=False, allow_none=True)

    def __init__(self, **kwargs):
        """
        Initializes the schema with marshmallow options.
        """
        # Allow unknown fields by default
        super().__init__(unknown=INCLUDE, **kwargs)

    @validates('name')
    def validate_name(self, name):
        """
        Validates that the site name meets length requirements.
        """
        if is_empty(name):
            raise ValidationError("Site name is required.")
        
        if not is_valid_length(name, SITE_NAME_MIN_LENGTH, SITE_NAME_MAX_LENGTH):
            raise ValidationError(f"Site name must be between {SITE_NAME_MIN_LENGTH} and {SITE_NAME_MAX_LENGTH} characters.")
        
        return name

    @validates('description')
    def validate_description(self, description):
        """
        Validates that the site description meets length requirements if provided.
        """
        if description is None or is_empty(description):
            return description
        
        if not is_valid_length(description, 0, SITE_DESCRIPTION_MAX_LENGTH):
            raise ValidationError(f"Site description must be at most {SITE_DESCRIPTION_MAX_LENGTH} characters.")
        
        return description

    @pre_load
    def sanitize_data(self, data, **kwargs):
        """
        Sanitizes input data to prevent security issues.
        """
        return sanitize_input(data)


class SiteCreateSchema(SiteBaseSchema):
    """
    Schema for validating site creation requests.
    """
    def __init__(self, **kwargs):
        """
        Initializes the schema with marshmallow options.
        """
        super().__init__(**kwargs)


class SiteUpdateSchema(SiteBaseSchema):
    """
    Schema for validating site update requests.
    """
    def __init__(self, **kwargs):
        """
        Initializes the schema with marshmallow options.
        """
        # Set partial=True to allow partial updates
        super().__init__(partial=True, **kwargs)


class SiteSchema(SiteBaseSchema):
    """
    Schema for serializing site response data.
    """
    id = fields.Integer(required=True)
    created_at = fields.DateTime(required=True, format='iso')
    updated_at = fields.DateTime(required=True, format='iso')
    user_count = fields.Integer(dump_only=True)
    interaction_count = fields.Integer(dump_only=True)

    def __init__(self, **kwargs):
        """
        Initializes the schema with marshmallow options.
        """
        super().__init__(**kwargs)


class SiteBriefSchema(ma.Schema):
    """
    Schema for serializing minimal site information, used in lists and dropdowns.
    """
    id = fields.Integer(required=True)
    name = fields.String(required=True)

    def __init__(self, **kwargs):
        """
        Initializes the schema with marshmallow options.
        """
        super().__init__(**kwargs)


class SiteListSchema(ma.Schema):
    """
    Schema for serializing a list of sites with pagination metadata.
    """
    sites = fields.List(fields.Nested(SiteSchema), required=True)
    pagination = fields.Dict(required=True)

    def __init__(self, **kwargs):
        """
        Initializes the schema with marshmallow options.
        """
        super().__init__(**kwargs)


class SiteUserAssignSchema(ma.Schema):
    """
    Schema for validating user assignment to sites with roles.
    """
    user_id = fields.Integer(required=True)
    role = fields.String(required=True)

    def __init__(self, **kwargs):
        """
        Initializes the schema with marshmallow options.
        """
        super().__init__(unknown=INCLUDE, **kwargs)

    @validates('role')
    def validate_role(self, role):
        """
        Validates that the user role is a valid role from the UserRole enum.
        """
        if role is None or is_empty(role):
            raise ValidationError("Role is required.")
        
        if not UserRole.is_valid(role):
            valid_roles = UserRole.get_values()
            raise ValidationError(f"Invalid role. Must be one of: {', '.join(valid_roles)}")
        
        return role

    @validates('user_id')
    def validate_user_id(self, user_id):
        """
        Validates that the user_id is a positive integer.
        """
        if user_id is None or user_id <= 0:
            raise ValidationError("User ID must be a positive integer.")
        
        return user_id


class UserSiteSchema(ma.Schema):
    """
    Schema for serializing user-site relationship data with role information.
    """
    user_id = fields.Integer(required=True)
    site_id = fields.Integer(required=True)
    role = fields.String(required=True)
    created_at = fields.DateTime(required=True, format='iso')
    updated_at = fields.DateTime(required=True, format='iso')

    def __init__(self, **kwargs):
        """
        Initializes the schema with marshmallow options.
        """
        super().__init__(**kwargs)


class SiteContextSchema(ma.Schema):
    """
    Schema for serializing the current site context information.
    """
    site_id = fields.Integer(required=True)
    name = fields.String(required=True)
    role = fields.String(required=True)

    def __init__(self, **kwargs):
        """
        Initializes the schema with marshmallow options.
        """
        super().__init__(**kwargs)