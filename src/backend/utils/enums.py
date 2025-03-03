from enum import Enum, unique
from datetime import datetime
import pytz  # version 2023.3

@unique
class InteractionType(Enum):
    """
    Enumeration of allowed interaction types in the system.
    
    This enum defines standardized interaction type options for the application
    to ensure consistency in data entry and validation.
    """
    MEETING = 'Meeting'
    CALL = 'Call'
    EMAIL = 'Email'
    OTHER = 'Other'

    @classmethod
    def get_values(cls):
        """
        Returns a list of all valid interaction type values.
        
        Returns:
            list: List of string values representing valid interaction types
        """
        return [member.value for member in cls]

    @classmethod
    def is_valid(cls, value):
        """
        Checks if a given string is a valid interaction type.
        
        Args:
            value (str): The value to check
            
        Returns:
            bool: True if value is a valid interaction type, False otherwise
        """
        return value in cls.get_values()


@unique
class UserRole(Enum):
    """
    Enumeration of user roles for site-based authorization.
    
    This enum defines the role hierarchy used for permission-based access control
    throughout the application.
    """
    SITE_ADMIN = 'admin'
    EDITOR = 'editor'
    VIEWER = 'viewer'

    @classmethod
    def get_values(cls):
        """
        Returns a list of all valid user role values.
        
        Returns:
            list: List of string values representing valid user roles
        """
        return [member.value for member in cls]

    @classmethod
    def is_valid(cls, value):
        """
        Checks if a given string is a valid user role.
        
        Args:
            value (str): The value to check
            
        Returns:
            bool: True if value is a valid user role, False otherwise
        """
        return value in cls.get_values()

    @classmethod
    def has_permission(cls, user_role, required_role):
        """
        Checks if one role has sufficient permissions compared to a required role.
        
        Implements role hierarchy where SITE_ADMIN > EDITOR > VIEWER.
        
        Args:
            user_role (str or UserRole): The user's role
            required_role (str or UserRole): The required role for an operation
            
        Returns:
            bool: True if user_role has sufficient permissions, False otherwise
        """
        # Define role hierarchy: SITE_ADMIN > EDITOR > VIEWER
        role_hierarchy = {
            cls.SITE_ADMIN.value: 3,
            cls.EDITOR.value: 2,
            cls.VIEWER.value: 1
        }
        
        # Convert strings to role values if needed
        user_role_value = user_role if isinstance(user_role, str) else user_role.value
        required_role_value = required_role if isinstance(required_role, str) else required_role.value
        
        # Check if roles are valid
        if user_role_value not in role_hierarchy or required_role_value not in role_hierarchy:
            return False
            
        # Compare role hierarchy positions
        return role_hierarchy[user_role_value] >= role_hierarchy[required_role_value]


class Timezone:
    """
    Utility class for timezone handling based on IANA timezone database.
    
    Provides methods for validating, converting, and listing timezones
    to ensure consistent timezone handling throughout the application.
    """
    
    # Common timezones with friendly names
    COMMON_ZONES = {
        'Eastern': 'America/New_York',
        'Central': 'America/Chicago',
        'Mountain': 'America/Denver',
        'Pacific': 'America/Los_Angeles',
        'UTC': 'UTC'
    }
    
    @staticmethod
    def is_valid(timezone_id):
        """
        Checks if a timezone identifier is valid in the IANA database.
        
        Args:
            timezone_id (str): The timezone identifier to check
            
        Returns:
            bool: True if timezone is valid, False otherwise
        """
        try:
            pytz.timezone(timezone_id)
            return True
        except pytz.exceptions.UnknownTimeZoneError:
            return False
    
    @classmethod
    def get_iana(cls, timezone_name):
        """
        Gets the IANA timezone identifier from a display name or abbreviation.
        
        Args:
            timezone_name (str): A timezone name, abbreviation, or IANA identifier
            
        Returns:
            str: IANA timezone identifier or 'UTC' if not found
        """
        if timezone_name in cls.COMMON_ZONES:
            return cls.COMMON_ZONES[timezone_name]
        
        # Check if it's already a valid IANA identifier
        if cls.is_valid(timezone_name):
            return timezone_name
            
        # Default to UTC if not found
        return 'UTC'
    
    @staticmethod
    def get_all_timezones():
        """
        Returns a list of all available IANA timezone identifiers.
        
        Returns:
            list: List of all timezone identifiers from the IANA database
        """
        return pytz.all_timezones
    
    @classmethod
    def get_common_timezones(cls):
        """
        Returns a dictionary of common timezone display names mapped to IANA identifiers.
        
        Returns:
            dict: Dictionary of timezone display names to IANA identifiers
        """
        return cls.COMMON_ZONES


@unique
class SortDirection(Enum):
    """
    Enumeration of allowed sort directions for queries.
    
    This enum standardizes sort direction options for consistent query behavior.
    """
    ASC = 'ASC'
    DESC = 'DESC'
    
    @classmethod
    def get_values(cls):
        """
        Returns a list of all valid sort direction values.
        
        Returns:
            list: List of string values representing valid sort directions
        """
        return [member.value for member in cls]
    
    @classmethod
    def is_valid(cls, value):
        """
        Checks if a given string is a valid sort direction.
        
        Args:
            value (str): The value to check
            
        Returns:
            bool: True if value is a valid sort direction, False otherwise
        """
        return value in cls.get_values()


@unique
class ErrorType(Enum):
    """
    Enumeration of error types for consistent error handling.
    
    This enum categorizes errors for consistent handling and reporting
    throughout the application.
    """
    VALIDATION = 'validation'
    AUTHENTICATION = 'authentication'
    AUTHORIZATION = 'authorization'
    NOT_FOUND = 'not_found'
    CONFLICT = 'conflict'
    SERVER = 'server'