"""
Provides pytest fixtures specifically for site-related testing in the Interaction Management System.

These fixtures generate test site instances with various configurations to facilitate
unit and integration testing of site-scoped functionality.
"""

import pytest
from typing import Dict, List, Tuple
from unittest.mock import Mock

from ...models.site import Site
from ...models.user_site import UserSite
from ..factories import SiteFactory, UserSiteFactory
from ...extensions import db


@pytest.fixture
def test_site_data() -> Dict:
    """
    Provides standard test site data for creating test sites.
    
    Returns:
        dict: Dictionary with site attributes
    """
    return {
        'name': 'Test Site',
        'description': 'A test site for testing purposes'
    }


@pytest.fixture
def another_test_site_data() -> Dict:
    """
    Provides alternative test site data for creating additional test sites.
    
    Returns:
        dict: Dictionary with site attributes
    """
    return {
        'name': 'Another Test Site',
        'description': 'Another test site for multi-site testing'
    }


@pytest.fixture
def multiple_test_sites(db_setup) -> List[Site]:
    """
    Creates multiple test site instances for testing multi-site functionality.
    
    Returns:
        list: List of Site instances
    """
    # Create list to hold site instances
    sites = []
    
    # Create 3 sites with different names using SiteFactory
    sites = SiteFactory.create_batch_with_users(size=3, users=[])
    
    # Add sites to database session
    db.session.add_all(sites)
    # Commit the transaction
    db.session.commit()
    
    # Return the list of site instances
    return sites


@pytest.fixture
def test_site_with_users(multiple_test_users, db_setup) -> Site:
    """
    Creates a test site with associated users for testing site-user relationships.
    
    Args:
        multiple_test_users: List of test users
        db_setup: Database fixture
        
    Returns:
        Site: Site instance with user associations
    """
    # Create a test site using SiteFactory
    site = SiteFactory(name="Site With Users")
    
    # Create UserSite associations for each test user with different roles
    roles = ['admin', 'editor', 'viewer']
    for i, user in enumerate(multiple_test_users):
        # Cycle through roles for different users
        role = roles[i % len(roles)]
        user_site = UserSiteFactory(user=user, site=site, role=role)
        
    # Add site and associations to database session
    db.session.add(site)
    # Commit the transaction
    db.session.commit()
    
    # Return the site instance
    return site


@pytest.fixture
def mock_site_repository() -> Mock:
    """
    Creates a mocked SiteRepository for testing service layer.
    
    Returns:
        unittest.mock.Mock: Mocked SiteRepository
    """
    # Create a Mock object for SiteRepository
    mock_repo = Mock()
    
    # Create a test site that we'll use for returns
    test_site = Site(name="Test Site")
    
    # Configure find_by_id to return a test Site instance
    mock_repo.find_by_id.return_value = test_site
    
    # Configure find_by_name to return a test Site instance
    mock_repo.find_by_name.return_value = test_site
    
    # Configure get_all to return a list of test Site instances
    sites = [
        Site(name="Site 1"),
        Site(name="Site 2"),
        Site(name="Site 3")
    ]
    mock_repo.get_all.return_value = sites
    
    # Configure create_site to return a new test Site instance
    new_site = Site(name="New Site")
    mock_repo.create_site.return_value = new_site
    
    # Configure update_site to return an updated Site instance
    updated_site = Site(name="Updated Site")
    mock_repo.update_site.return_value = updated_site
    
    # Configure delete_site to return True
    mock_repo.delete_site.return_value = True
    
    # Configure get_sites_for_user to return a list of sites
    mock_repo.get_sites_for_user.return_value = [
        Site(name="User's Site 1"),
        Site(name="User's Site 2")
    ]
    
    # Configure get_users_for_site to return a list of users with roles
    mock_repo.get_users_for_site.return_value = [
        {"user_id": 1, "username": "user1", "role": "admin"},
        {"user_id": 2, "username": "user2", "role": "editor"},
        {"user_id": 3, "username": "user3", "role": "viewer"}
    ]
    
    # Configure user_has_site_access to return True for valid combinations
    mock_repo.user_has_site_access.return_value = True
    
    # Configure get_user_role_for_site to return appropriate role
    mock_repo.get_user_role_for_site.return_value = "editor"
    
    # Return the mock SiteRepository
    return mock_repo


@pytest.fixture
def mock_site_service(mock_site_repository) -> Mock:
    """
    Creates a mocked SiteService for testing controllers.
    
    Args:
        mock_site_repository: Mocked repository object
        
    Returns:
        unittest.mock.Mock: Mocked SiteService
    """
    # Create a Mock object for SiteService with mock_site_repository
    mock_service = Mock()
    
    # Configure get_site_by_id to return a test Site instance
    test_site = Site(name="Test Site")
    mock_service.get_site_by_id.return_value = test_site
    
    # Configure get_site_by_name to return a test Site instance
    mock_service.get_site_by_name.return_value = test_site
    
    # Configure get_all_sites to return a list of sites
    mock_service.get_all_sites.return_value = [
        Site(name="Site 1"),
        Site(name="Site 2"),
        Site(name="Site 3")
    ]
    
    # Configure get_user_sites to return a list of sites for a user
    mock_service.get_user_sites.return_value = [
        Site(name="User's Site 1"),
        Site(name="User's Site 2")
    ]
    
    # Configure create_site to return a new site instance
    mock_service.create_site.return_value = Site(name="New Site")
    
    # Configure update_site to return an updated site instance
    mock_service.update_site.return_value = Site(name="Updated Site")
    
    # Configure delete_site to return True
    mock_service.delete_site.return_value = True
    
    # Configure get_site_users to return a list of users for a site
    mock_service.get_site_users.return_value = [
        {"user_id": 1, "username": "user1", "role": "admin"},
        {"user_id": 2, "username": "user2", "role": "editor"},
        {"user_id": 3, "username": "user3", "role": "viewer"}
    ]
    
    # Configure user_has_site_access to return True for valid combinations
    mock_service.user_has_site_access.return_value = True
    
    # Return the mock SiteService
    return mock_service


@pytest.fixture
def sites_with_same_user(test_user, db_setup) -> List[Site]:
    """
    Creates multiple sites with access for the same user.
    
    Args:
        test_user: User instance
        db_setup: Database fixture
        
    Returns:
        list: List of Site instances accessible by the user
    """
    # Create multiple sites with SiteFactory
    sites = []
    for i in range(3):
        site = SiteFactory(name=f"User Site {i+1}")
        sites.append(site)
    
    # Create UserSite associations between test_user and each site
    roles = ['admin', 'editor', 'viewer']
    for i, site in enumerate(sites):
        # Assign different roles to different sites
        role = roles[i % len(roles)]
        UserSiteFactory(user=test_user, site=site, role=role)
    
    # Add sites and associations to database session
    db.session.add_all(sites)
    # Commit the transaction
    db.session.commit()
    
    # Return list of sites
    return sites


@pytest.fixture
def site_with_multiple_roles(test_site, multiple_test_users, db_setup) -> Tuple[Site, Dict]:
    """
    Creates a site with users having different roles.
    
    Args:
        test_site: Site instance
        multiple_test_users: List of user instances
        db_setup: Database fixture
        
    Returns:
        tuple: Tuple of (Site, dict of user_id:role)
    """
    # Create UserSite associations between test_site and each user with different roles
    roles = ['admin', 'editor', 'viewer']
    role_mapping = {}
    
    for i, user in enumerate(multiple_test_users):
        # Cycle through roles for different users
        role = roles[i % len(roles)]
        UserSiteFactory(user=user, site=test_site, role=role)
        role_mapping[user.id] = role
    
    # Add associations to database session
    # Commit the transaction
    db.session.commit()
    
    # Return tuple of site and role mapping dictionary
    return (test_site, role_mapping)