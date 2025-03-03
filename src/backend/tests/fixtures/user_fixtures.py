"""
Provides pytest fixtures specifically for user-related testing in the Interaction Management System.
These fixtures generate test user instances with various roles and site associations to facilitate
unit and integration testing of user-scoped functionality.
"""

# External imports
import pytest  # version 7.3.1
from typing import Dict, List, Tuple, Optional  # standard library
from unittest.mock import Mock  # standard library

# Internal imports
from ../../models/user import User
from ../../models/user_site import UserSite
from ../factories import UserFactory, UserSiteFactory
from ../../extensions import db
from ../../utils/enums import UserRole


@pytest.fixture
def test_user_data() -> Dict[str, str]:
    """
    Provides standard test user data for creating test users.
    
    Returns:
        dict: Dictionary with user attributes
    """
    return {
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'Password123!'
    }


@pytest.fixture
def test_admin_user_data() -> Dict[str, str]:
    """
    Provides test admin user data for creating admin test users.
    
    Returns:
        dict: Dictionary with admin user attributes
    """
    return {
        'username': 'adminuser',
        'email': 'admin@example.com',
        'password': 'AdminPass123!'
    }


@pytest.fixture
def multiple_test_users(db_setup) -> List[User]:
    """
    Creates multiple test user instances for testing multi-user functionality.
    
    Returns:
        list: List of User instances
    """
    users = []
    # Create 3 users with different usernames
    for i in range(3):
        user = UserFactory(username=f"testuser{i}", email=f"test{i}@example.com")
        user.set_password("TestPass123!")
        users.append(user)
    
    # Add users to database session
    for user in users:
        db.session.add(user)
    
    db.session.commit()
    return users


@pytest.fixture
def admin_user(db_setup) -> User:
    """
    Creates an admin user for testing administrative functions.
    
    Returns:
        User: Admin User instance
    """
    user = UserFactory(username="adminuser", email="admin@example.com")
    user.set_password("AdminPass123!")
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def editor_user(db_setup) -> User:
    """
    Creates an editor user for testing editor permissions.
    
    Returns:
        User: Editor User instance
    """
    user = UserFactory(username="editoruser", email="editor@example.com")
    user.set_password("EditorPass123!")
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def viewer_user(db_setup) -> User:
    """
    Creates a viewer user for testing viewer permissions.
    
    Returns:
        User: Viewer User instance
    """
    user = UserFactory(username="vieweruser", email="viewer@example.com")
    user.set_password("ViewerPass123!")
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def test_user_with_sites(test_sites, db_setup) -> User:
    """
    Creates a test user with associated sites for testing site access control.
    
    Args:
        test_sites: List of test site instances
        
    Returns:
        User: User instance with site associations
    """
    user = UserFactory(username="siteuser", email="site@example.com")
    user.set_password("SitePass123!")
    db.session.add(user)
    db.session.flush()  # Get the user ID
    
    # Create user-site associations with different roles
    for i, site in enumerate(test_sites):
        # Cycle through different roles
        role = [UserRole.SITE_ADMIN.value, UserRole.EDITOR.value, UserRole.VIEWER.value][i % 3]
        user_site = UserSiteFactory(user_id=user.id, site_id=site.id, role=role)
        db.session.add(user_site)
    
    db.session.commit()
    return user


@pytest.fixture
def system_admin_user(db_setup) -> User:
    """
    Creates a system admin user for testing cross-site administration.
    
    Returns:
        User: System Admin User instance
    """
    user = UserFactory(username="sysadmin", email="sysadmin@example.com")
    user.set_password("SysAdminPass123!")
    # Set system admin flag if your model supports it
    # This would depend on how your application implements system admin status
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def mock_user_repository() -> Mock:
    """
    Creates a mocked UserRepository for testing service layer.
    
    Returns:
        unittest.mock.Mock: Mocked UserRepository
    """
    mock_repo = Mock()
    
    # Configure find methods
    test_user = UserFactory.build()
    mock_repo.find_by_id.return_value = test_user
    mock_repo.find_by_username.return_value = test_user
    mock_repo.find_by_email.return_value = test_user
    
    # Configure authentication to return a user or raise AuthenticationError
    def authenticate_side_effect(username, password):
        if username == "testuser" and password == "Password123!":
            return test_user
        else:
            from ...exceptions import AuthenticationError
            raise AuthenticationError("Invalid credentials")
    
    mock_repo.authenticate.side_effect = authenticate_side_effect
    
    # Configure CRUD operations
    mock_repo.create.return_value = test_user
    mock_repo.update.return_value = test_user
    mock_repo.delete.return_value = True
    
    # Configure site access methods
    mock_repo.get_user_sites.return_value = [1, 2, 3]  # Site IDs
    mock_repo.add_user_to_site.return_value = True
    mock_repo.remove_user_from_site.return_value = True
    mock_repo.update_user_role.return_value = True
    
    return mock_repo


@pytest.fixture
def mock_user_service(mock_user_repository) -> Mock:
    """
    Creates a mocked UserService for testing controllers.
    
    Args:
        mock_user_repository: Mocked user repository
        
    Returns:
        unittest.mock.Mock: Mocked UserService
    """
    mock_service = Mock()
    
    # User retrieval methods
    test_user = UserFactory.build()
    mock_service.get_user_by_id.return_value = test_user
    mock_service.get_users_by_site.return_value = UserFactory.create_batch_with_sites(3, [])
    
    # Authentication and authorization methods
    mock_service.authenticate_user.return_value = {
        'token': 'fake-jwt-token',
        'user': test_user.to_dict()
    }
    
    mock_service.validate_token.return_value = {
        'user_id': 1,
        'username': 'testuser',
        'sites': [1, 2, 3]
    }
    
    # CRUD operations
    mock_service.create_user.return_value = test_user
    mock_service.update_user.return_value = test_user
    mock_service.delete_user.return_value = True
    
    # Site management methods
    mock_service.add_user_to_site.return_value = True
    mock_service.remove_user_from_site.return_value = True
    mock_service.update_user_role.return_value = True
    mock_service.get_user_sites.return_value = [{'id': 1, 'name': 'Site 1'}, {'id': 2, 'name': 'Site 2'}]
    
    return mock_service


@pytest.fixture
def user_with_multiple_roles(test_user, multiple_test_sites, db_setup) -> Tuple[User, Dict[int, str]]:
    """
    Creates a user with different roles across multiple sites.
    
    Args:
        test_user: Test user instance
        multiple_test_sites: List of test site instances
        
    Returns:
        tuple: Tuple of (User, dict of site_id:role)
    """
    # Dictionary to track role assignments for verification
    site_roles = {}
    
    # Assign different roles to the user for different sites
    roles = [UserRole.SITE_ADMIN.value, UserRole.EDITOR.value, UserRole.VIEWER.value]
    
    for i, site in enumerate(multiple_test_sites):
        role = roles[i % len(roles)]
        user_site = UserSiteFactory(user_id=test_user.id, site_id=site.id, role=role)
        site_roles[site.id] = role
        db.session.add(user_site)
    
    db.session.commit()
    return test_user, site_roles


@pytest.fixture
def users_with_same_site(test_site, db_setup) -> List[User]:
    """
    Creates multiple users with access to the same site.
    
    Args:
        test_site: Test site instance
        
    Returns:
        list: List of User instances with access to the site
    """
    users = []
    roles = [UserRole.SITE_ADMIN.value, UserRole.EDITOR.value, UserRole.VIEWER.value]
    
    # Create 3 users with different roles for the same site
    for i in range(3):
        user = UserFactory(username=f"siteuser{i}", email=f"site{i}@example.com")
        user.set_password(f"SitePass{i}123!")
        db.session.add(user)
        db.session.flush()  # Get the user ID
        
        # Assign role to user for the site
        user_site = UserSiteFactory(user_id=user.id, site_id=test_site.id, role=roles[i])
        db.session.add(user_site)
        
        users.append(user)
    
    db.session.commit()
    return users


@pytest.fixture
def test_password_reset_token(test_user) -> str:
    """
    Provides a fixture for testing password reset functionality.
    
    Args:
        test_user: Test user instance
        
    Returns:
        str: Test reset token
    """
    # Generate a realistic token
    return "reset-token-123456789abcdef"


@pytest.fixture
def test_expired_password_reset_token(test_user) -> str:
    """
    Provides an expired reset token for testing token expiration.
    
    Args:
        test_user: Test user instance
        
    Returns:
        str: Expired reset token
    """
    # Generate a realistic but expired token
    return "expired-token-987654321fedcba"