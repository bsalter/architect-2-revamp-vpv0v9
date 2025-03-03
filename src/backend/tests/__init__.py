"""
Interaction Management System - Test Package

This package contains tests for the Interaction Management System backend.
It provides common test functionality and ensures that pytest can discover
all test modules within this package.
"""

import pytest  # pytest 7.3.1

# Version identifier for the test suite
TEST_VERSION = "1.0.0"

# This file purposely does not define additional functionality,
# as it primarily serves to mark the directory as a pytest package
# and provide the TEST_VERSION global for test modules to reference.

# Test modules can access TEST_VERSION to ensure they're running
# against the expected test framework version.