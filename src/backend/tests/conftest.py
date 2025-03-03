"""
Central pytest configuration file for the Interaction Management System tests.
Defines common fixtures and setup/teardown functions that are shared across unit, integration, and end-to-end tests.
"""
import os  # standard library
import tempfile  # standard library
import typing  # standard library
import datetime  # standard library
from unittest import mock  # standard library

import pytest  # pytest==7.3.1
import flask  # flask==2.3.2
import sqlalchemy  # sqlalchemy==2.0.19

from ..extensions import db  # src/backend/extensions.py
from ..app import create_app  # src/backend/app.py
from ..config import TestConfig  # src/backend/config.py
from ..models.base import Base  # src/backend/models/base.py
from .factories import UserFactory, SiteFactory  # src/backend/tests/factories.py


@pytest.fixture
def app() -> flask.Flask:
    """Creates and configures a Flask application instance for testing"""
    # Create Flask application using create_app factory function
    app = create_app()

    # Configure application with TestingConfig
    app.config.from_object(TestConfig)

    # Set up application context
    with app.app_context():
        # Yield the application for tests
        yield app

    # Tear down application context after tests complete


@pytest.fixture
def client(app: flask.Flask) -> flask.testing.FlaskClient:
    """Creates a Flask test client for making test requests to the application"""
    # Get test client from Flask application
    client = app.test_client()

    # Configure client to preserve context between requests
    client.preserve_context = False

    # Yield client for tests
    yield client

    # No specific cleanup required


@pytest.fixture(scope='session')
def test_db_url() -> str:
    """Generates a SQLite database URL for testing"""
    # Create temporary file for SQLite database
    temp_file = tempfile.NamedTemporaryFile(delete=False)

    # Generate SQLite URL from the temporary file path
    test_db_url = f'sqlite:///{temp_file.name}'

    # Yield the database URL
    yield test_db_url

    # Close and remove the temporary file after tests complete
    temp_file.close()
    os.unlink(temp_file.name)


@pytest.fixture(scope='session')
def db_engine(test_db_url: str) -> sqlalchemy.engine.Engine:
    """Creates a SQLAlchemy engine for test database connection"""
    # Create SQLAlchemy engine from test database URL
    engine = sqlalchemy.create_engine(test_db_url)

    # Create all database tables using Base.metadata.create_all
    Base.metadata.create_all(engine)

    # Yield the engine for tests
    yield engine

    # Drop all tables using Base.metadata.drop_all
    Base.metadata.drop_all(engine)

    # Dispose the engine after tests complete
    engine.dispose()


@pytest.fixture
def db_setup(db_engine: sqlalchemy.engine.Engine) -> None:
    """Sets up a clean database session for each test and handles transaction management"""
    # Create a database connection from engine
    connection = db_engine.connect()

    # Begin a transaction
    transaction = connection.begin()

    # Configure database session to use the connection
    db.session = db.sessionmaker(bind=db_engine)()
    db.session.configure(bind=connection)

    # Yield None to allow test to run
    yield

    # Rollback the transaction to clean up after test
    transaction.rollback()

    # Close the database connection
    connection.close()


@pytest.fixture
def test_user(db_setup: None) -> User:
    """Creates a standard test user for authentication tests"""
    # Create user with UserFactory with standardized test data
    user = UserFactory.create()

    # Set user password with known test password
    user.set_password('test_password')

    # Add user to database session
    db.session.add(user)

    # Commit changes to database
    db.session.commit()

    # Yield the user instance
    yield user

    # No explicit cleanup needed (handled by db_setup rollback)


@pytest.fixture
def test_site(db_setup: None) -> Site:
    """Creates a standard test site for site-scoped tests"""
    # Create site with SiteFactory with standardized test data
    site = SiteFactory.create()

    # Add site to database session
    db.session.add(site)

    # Commit changes to database
    db.session.commit()

    # Yield the site instance
    yield site

    # No explicit cleanup needed (handled by db_setup rollback)


@pytest.fixture
def test_user_site(test_user: User, test_site: Site, role: str, db_setup: None) -> UserSite:
    """Creates a user-site association with a specific role"""
    # Create UserSite instance with provided user, site, and role
    user_site = UserSite(user_id=test_user.id, site_id=test_site.id, role=role)

    # Add association to database session
    db.session.add(user_site)

    # Commit changes to database
    db.session.commit()

    # Yield the user_site instance
    yield user_site

    # No explicit cleanup needed (handled by db_setup rollback)


@pytest.fixture
def mock_user_context_service(test_user: User) -> mock.Mock:
    """Creates a mocked UserContextService for testing"""
    # Create a Mock object for UserContextService
    mock_service = mock.Mock()

    # Configure get_current_user to return test_user
    mock_service.get_current_user.return_value = test_user

    # Configure get_user_id to return test_user.id
    mock_service.get_user_id.return_value = test_user.id

    # Return the mock service
    return mock_service


@pytest.fixture
def mock_site_context_service(test_site: Site) -> mock.Mock:
    """Creates a mocked SiteContextService for testing"""
    # Create a Mock object for SiteContextService
    mock_service = mock.Mock()

    # Configure get_current_site to return test_site
    mock_service.get_current_site.return_value = test_site

    # Configure get_site_id to return test_site.id
    mock_service.get_site_id.return_value = test_site.id

    # Configure get_user_sites to return [test_site]
    mock_service.get_user_sites.return_value = [test_site]

    # Configure get_user_site_ids to return [test_site.id]
    mock_service.get_user_site_ids.return_value = [test_site.id]

    # Return the mock service
    return mock_service


@pytest.fixture
def mock_permission_service() -> mock.Mock:
    """Creates a mocked PermissionService for testing"""
    # Create a Mock object for PermissionService
    mock_service = mock.Mock()

    # Configure has_permission to return True by default
    mock_service.has_permission.return_value = True

    # Configure validate_site_access to return True by default
    mock_service.validate_site_access.return_value = True

    # Return the mock service
    return mock_service