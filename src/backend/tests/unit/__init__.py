"""
Initializes the unit test package for the Interaction Management System.
This file marks the unit test directory as a Python package and imports common fixtures, mocks, and utilities required for unit testing backend components.
"""
import pytest  # pytest==^7.0.0

from ..conftest import db_setup  # src/backend/tests/conftest.py
from ..conftest import test_user  # src/backend/tests/conftest.py
from ..conftest import test_site  # src/backend/tests/conftest.py
from ..conftest import mock_user_context_service  # src/backend/tests/conftest.py
from ..conftest import mock_site_context_service  # src/backend/tests/conftest.py
from ..conftest import mock_permission_service  # src/backend/tests/conftest.py

UNIT_TEST_VERSION = "1.0.0"