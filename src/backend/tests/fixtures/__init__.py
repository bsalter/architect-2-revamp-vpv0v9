"""
Initializes the test fixtures package, making fixtures for authentication, users, sites, and interactions available for import throughout the test suite. Acts as the central point of access for all test fixtures in the Interaction Management System.
"""

import pytest  # version 7.3.1

from .auth_fixtures import *  # Import all authentication-related test fixtures
from .user_fixtures import *  # Import all user-related test fixtures
from .site_fixtures import *  # Import all site-related test fixtures
from .interaction_fixtures import *  # Import all interaction-related test fixtures

FIXTURES_VERSION = "1.0.0"