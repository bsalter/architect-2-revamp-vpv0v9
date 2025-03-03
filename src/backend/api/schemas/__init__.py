"""
Initializes the API schemas package and re-exports all schema classes to simplify imports throughout the application.
Provides centralized access to marshmallow schemas for authentication, users, sites, interactions, and search functionality.
"""

from .auth_schemas import (
    LoginSchema,
    TokenSchema,
    RefreshSchema,
    LogoutSchema,
    PasswordResetRequestSchema,
)
from .user_schemas import (
    UserSchema,
    UserCreateSchema,
    UserUpdateSchema,
    UserProfileSchema,
    UserSiteSchema,
    UserListSchema,
)
from .site_schemas import (
    SiteSchema,
    SiteCreateSchema,
    SiteUpdateSchema,
    SiteBriefSchema,
    SiteUserAssignSchema,
    SiteListSchema,
)
from .interaction_schemas import (
    InteractionBaseSchema,
    InteractionCreateSchema,
    InteractionUpdateSchema,
    InteractionResponseSchema,
    InteractionDetailSchema,
    InteractionListSchema,
)
from .search_schemas import (
    FilterSchema,
    SortSchema,
    PaginationSchema,
    DateRangeSchema,
    SearchSchema,
    SearchResultsSchema,
    AdvancedSearchSchema,
)

__all__ = [
    "LoginSchema",
    "TokenSchema",
    "RefreshSchema",
    "LogoutSchema",
    "PasswordResetRequestSchema",
    "UserSchema",
    "UserCreateSchema",
    "UserUpdateSchema",
    "UserProfileSchema",
    "UserSiteSchema",
    "UserListSchema",
    "SiteSchema",
    "SiteCreateSchema",
    "SiteUpdateSchema",
    "SiteBriefSchema",
    "SiteUserAssignSchema",
    "SiteListSchema",
    "InteractionBaseSchema",
    "InteractionCreateSchema",
    "InteractionUpdateSchema",
    "InteractionResponseSchema",
    "InteractionDetailSchema",
    "InteractionListSchema",
    "FilterSchema",
    "SortSchema",
    "PaginationSchema",
    "DateRangeSchema",
    "SearchSchema",
    "SearchResultsSchema",
    "AdvancedSearchSchema",
]