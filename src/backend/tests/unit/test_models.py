"""
Unit tests for verifying the behavior of database model classes including BaseModel, User, Site, UserSite, Interaction, and InteractionHistory.
Tests focus on model initialization, property validation, model methods, and relationship handling.
"""
import datetime
import unittest.mock
import pytest  # pytest^7.0.0

from ..models.base import BaseModel  # src/backend/models/base.py
from ..models.user import User  # src/backend/models/user.py
from ..models.site import Site  # src/backend/models/site.py
from ..models.interaction import Interaction  # src/backend/models/interaction.py
from ..models.interaction_history import InteractionHistory, create_history_record, CHANGE_TYPE_CREATE, CHANGE_TYPE_UPDATE, CHANGE_TYPE_DELETE  # src/backend/models/interaction_history.py
from ..utils.enums import InteractionType, UserRole, Timezone  # src/backend/utils/enums.py
from .conftest import db_setup, UserFactory, SiteFactory, InteractionFactory, InteractionHistoryFactory  # src/backend/tests/conftest.py


def test_base_model_initialization():
    """Tests that the BaseModel correctly initializes with default values"""
    # Create an instance of BaseModel
    base_model = BaseModel(created_at=datetime.datetime.utcnow(), updated_at=datetime.datetime.utcnow())

    # Assert that id is None before database persistence
    assert base_model.id is None, "ID should be None before database persistence"

    # Assert that created_at is set to a valid datetime
    assert isinstance(base_model.created_at, datetime.datetime), "created_at should be a datetime object"

    # Assert that updated_at is set to the same value as created_at initially
    assert isinstance(base_model.updated_at, datetime.datetime), "updated_at should be a datetime object"


def test_base_model_to_dict():
    """Tests that the BaseModel to_dict method correctly serializes the model"""
    # Create an instance of BaseModel
    base_model = BaseModel(created_at=datetime.datetime.utcnow(), updated_at=datetime.datetime.utcnow())

    # Call to_dict() on the instance
    model_dict = base_model.to_dict()

    # Assert the resulting dictionary contains expected keys (id, created_at, updated_at)
    assert 'id' in model_dict, "ID should be in the dictionary"
    assert 'created_at' in model_dict, "created_at should be in the dictionary"
    assert 'updated_at' in model_dict, "updated_at should be in the dictionary"

    # Assert datetime fields are serialized as ISO format strings
    assert isinstance(model_dict['created_at'], str), "created_at should be an ISO format string"
    assert isinstance(model_dict['updated_at'], str), "updated_at should be an ISO format string"


def test_base_model_update_timestamp():
    """Tests that the update_timestamp method updates the updated_at field"""
    # Create an instance of BaseModel
    base_model = BaseModel(created_at=datetime.datetime.utcnow(), updated_at=datetime.datetime.utcnow())

    # Store original updated_at value
    original_updated_at = base_model.updated_at

    # Call update_timestamp() method
    base_model.update_timestamp()

    # Assert that updated_at has changed
    assert base_model.updated_at != original_updated_at, "updated_at should be updated"

    # Assert that updated_at is now after the original value
    assert base_model.updated_at > original_updated_at, "updated_at should be later than original"


def test_user_initialization(db_setup):
    """Tests that the User model initializes with correct values"""
    # Create a User instance with test data
    user = User(username='testuser', email='test@example.com', password='password')

    # Assert username and email match provided values
    assert user.username == 'testuser', "Username should match provided value"
    assert user.email == 'test@example.com', "Email should match provided value"

    # Assert password_hash is set (not None or empty)
    assert user.password_hash is not None, "Password hash should be set"

    # Assert last_login is initially None
    assert user.last_login is None, "Last login should be initially None"

    # Assert created_at and updated_at are set
    assert user.created_at is not None, "Created at should be set"
    assert user.updated_at is not None, "Updated at should be set"


def test_user_password_handling(db_setup):
    """Tests password hashing and verification in the User model"""
    # Create a User instance with a known password
    user = User(username='testuser', email='test@example.com', password='password')

    # Assert that password_hash is not the plaintext password
    assert user.password_hash != 'password', "Password hash should not be the plaintext password"

    # Verify that check_password returns True for the correct password
    assert user.check_password('password') is True, "check_password should return True for correct password"

    # Verify that check_password returns False for an incorrect password
    assert user.check_password('wrongpassword') is False, "check_password should return False for incorrect password"


def test_user_to_dict(db_setup):
    """Tests that the User to_dict method correctly serializes without exposing password_hash"""
    # Create a User instance with test data
    user = User(username='testuser', email='test@example.com', password='password')

    # Call to_dict() on the instance
    user_dict = user.to_dict()

    # Assert the resulting dictionary contains expected user properties
    assert 'id' in user_dict, "ID should be in the dictionary"
    assert 'username' in user_dict, "Username should be in the dictionary"
    assert 'email' in user_dict, "Email should be in the dictionary"
    assert 'created_at' in user_dict, "created_at should be in the dictionary"
    assert 'updated_at' in user_dict, "updated_at should be in the dictionary"

    # Assert that password_hash is not included in the dictionary
    assert 'password_hash' not in user_dict, "Password hash should not be in the dictionary"


def test_user_update_last_login(db_setup):
    """Tests that update_last_login correctly updates the login timestamp"""
    # Create a User instance with last_login initially None
    user = User(username='testuser', email='test@example.com', password='password')
    user.last_login = None

    # Call update_last_login() method
    user.update_last_login()

    # Assert that last_login is now a valid datetime
    assert isinstance(user.last_login, datetime.datetime), "last_login should be a datetime object"

    # Assert that last_login is close to current time
    now = datetime.datetime.utcnow()
    time_difference = abs((user.last_login - now).total_seconds())
    assert time_difference < 5, "last_login should be close to current time"


def test_user_site_access(db_setup):
    """Tests site access functionality in the User model"""
    # Create User instance
    user = UserFactory.create()

    # Create Site instances
    site1 = SiteFactory.create()
    site2 = SiteFactory.create()

    # Associate user with one site but not another
    user.sites.append(site1)
    db.session.commit()

    # Test has_site_access() returns True for associated site
    assert user.has_site_access(site1.id) is True, "has_site_access should return True for associated site"

    # Test has_site_access() returns False for non-associated site
    assert user.has_site_access(site2.id) is False, "has_site_access should return False for non-associated site"

    # Test get_site_ids() returns correct list of site IDs
    site_ids = user.get_site_ids()
    assert len(site_ids) == 1, "get_site_ids should return a list with one element"
    assert site_ids[0] == site1.id, "get_site_ids should return the correct site ID"


def test_user_role_for_site(db_setup):
    """Tests role-based permissions for sites in the User model"""
    # Create User and Site instances
    user = UserFactory.create()
    site = SiteFactory.create()

    # Associate user with site with a specific role
    user_site = UserSite(user_id=user.id, site_id=site.id, role=UserRole.EDITOR.value)
    db.session.add(user_site)
    db.session.commit()

    # Test get_role_for_site() returns the correct role
    role = user.get_role_for_site(site.id)
    assert role == UserRole.EDITOR.value, "get_role_for_site should return the correct role"

    # Test has_role() returns correct results for different role checks
    assert user.has_role(site.id, UserRole.VIEWER.value) is True, "has_role should return True for lower roles"
    assert user.has_role(site.id, UserRole.EDITOR.value) is True, "has_role should return True for the same role"
    assert user.has_role(site.id, UserRole.SITE_ADMIN.value) is False, "has_role should return False for higher roles"

    # Test convenience methods (is_site_admin, is_editor, is_viewer)
    assert user.is_site_admin(site.id) is False, "is_site_admin should return False"
    assert user.is_editor(site.id) is True, "is_editor should return True"
    assert user.is_viewer(site.id) is True, "is_viewer should return True"


def test_site_initialization(db_setup):
    """Tests that the Site model initializes with correct values"""
    # Create a Site instance with test data
    site = Site(name='Test Site', description='A test site')

    # Assert name and description match provided values
    assert site.name == 'Test Site', "Name should match provided value"
    assert site.description == 'A test site', "Description should match provided value"

    # Assert created_at and updated_at are set
    assert site.created_at is not None, "Created at should be set"
    assert site.updated_at is not None, "Updated at should be set"

    # Assert relationships (users, interactions) are initialized as empty lists
    assert site.users.count() == 0, "Users relationship should be initialized as an empty list"
    assert site.interactions.count() == 0, "Interactions relationship should be initialized as an empty list"


def test_site_to_dict(db_setup):
    """Tests that the Site to_dict method correctly serializes the model"""
    # Create a Site instance with test data
    site = Site(name='Test Site', description='A test site')

    # Call to_dict() on the instance
    site_dict = site.to_dict()

    # Assert the resulting dictionary contains expected site properties
    assert 'id' in site_dict, "ID should be in the dictionary"
    assert 'name' in site_dict, "Name should be in the dictionary"
    assert 'description' in site_dict, "Description should be in the dictionary"
    assert 'created_at' in site_dict, "created_at should be in the dictionary"
    assert 'updated_at' in site_dict, "updated_at should be in the dictionary"

    # Assert datetime fields are serialized as ISO format strings
    assert isinstance(site_dict['created_at'], str), "created_at should be an ISO format string"
    assert isinstance(site_dict['updated_at'], str), "updated_at should be an ISO format string"


def test_site_update(db_setup):
    """Tests that the update method updates site properties correctly"""
    # Create a Site instance with initial data
    site = Site(name='Original Name', description='Original Description')
    db.session.add(site)
    db.session.commit()

    # Call update() with new values
    new_data = {'name': 'New Name', 'description': 'New Description'}
    site.update(new_data)

    # Assert properties are updated to new values
    assert site.name == 'New Name', "Name should be updated"
    assert site.description == 'New Description', "Description should be updated"

    # Assert updated_at timestamp is updated
    assert site.updated_at > site.created_at, "Updated at should be updated"


def test_site_user_relationship(db_setup):
    """Tests the relationship between Site and User models"""
    # Create Site and User instances
    site = SiteFactory.create()
    user1 = UserFactory.create()
    user2 = UserFactory.create()

    # Associate users with site
    site.users.append(user1)
    site.users.append(user2)
    db.session.commit()

    # Test get_users() returns correct list of users
    users = site.get_users()
    assert len(users) == 2, "get_users should return a list with two elements"
    assert user1 in users, "user1 should be in the list"
    assert user2 in users, "user2 should be in the list"

    # Test get_user_count() returns correct count
    assert site.get_user_count() == 2, "get_user_count should return 2"

    # Verify bidirectional relationship access
    assert site in user1.sites.all(), "Site should be in user1's sites"
    assert site in user2.sites.all(), "Site should be in user2's sites"


def test_site_interaction_relationship(db_setup):
    """Tests the relationship between Site and Interaction models"""
    # Create Site, User, and Interaction instances
    site = SiteFactory.create()
    user = UserFactory.create()
    interaction1 = InteractionFactory.create(site_id=site.id, created_by=user.id)
    interaction2 = InteractionFactory.create(site_id=site.id, created_by=user.id)

    # Associate interactions with site
    db.session.add_all([interaction1, interaction2])
    db.session.commit()

    # Test get_interactions() returns correct list of interactions
    interactions = site.get_interactions().all()
    assert len(interactions) == 2, "get_interactions should return a list with two elements"
    assert interaction1 in interactions, "interaction1 should be in the list"
    assert interaction2 in interactions, "interaction2 should be in the list"

    # Test get_interaction_count() returns correct count
    assert site.get_interaction_count() == 2, "get_interaction_count should return 2"

    # Verify site_id is set properly on interactions
    assert interaction1.site_id == site.id, "interaction1 should have the correct site_id"
    assert interaction2.site_id == site.id, "interaction2 should have the correct site_id"


def test_interaction_initialization(db_setup):
    """Tests that the Interaction model initializes with required values"""
    # Create a Site and User for foreign keys
    site = SiteFactory.create()
    user = UserFactory.create()

    # Create an Interaction instance with test data
    start_time = datetime.datetime.utcnow()
    end_time = start_time + datetime.timedelta(hours=1)
    interaction = Interaction(
        site_id=site.id,
        title='Test Interaction',
        type=InteractionType.MEETING.value,
        lead='Test Lead',
        start_datetime=start_time,
        end_datetime=end_time,
        timezone='UTC',
        created_by=user.id,
        description='Test Description'
    )

    # Assert all properties match provided values
    assert interaction.site_id == site.id, "Site ID should match provided value"
    assert interaction.title == 'Test Interaction', "Title should match provided value"
    assert interaction.type == InteractionType.MEETING.value, "Type should match provided value"
    assert interaction.lead == 'Test Lead', "Lead should match provided value"
    assert interaction.start_datetime == start_time, "Start datetime should match provided value"
    assert interaction.end_datetime == end_time, "End datetime should match provided value"
    assert interaction.timezone == 'UTC', "Timezone should match provided value"
    assert interaction.created_by == user.id, "Created by should match provided value"
    assert interaction.description == 'Test Description', "Description should match provided value"

    # Assert created_at and updated_at are set
    assert interaction.created_at is not None, "Created at should be set"
    assert interaction.updated_at is not None, "Updated at should be set"


def test_interaction_validation(db_setup):
    """Tests that the Interaction validate method enforces data rules"""
    # Create valid Interaction instance
    site = SiteFactory.create()
    user = UserFactory.create()
    start_time = datetime.datetime.utcnow()
    end_time = start_time + datetime.timedelta(hours=1)
    interaction = Interaction(
        site_id=site.id,
        title='Test Interaction',
        type=InteractionType.MEETING.value,
        lead='Test Lead',
        start_datetime=start_time,
        end_datetime=end_time,
        timezone='UTC',
        created_by=user.id,
        description='Test Description'
    )

    # Assert validate() returns (True, '')
    is_valid, error_message = interaction.validate()
    assert is_valid is True, "validate() should return True for valid data"
    assert error_message == '', "validate() should return an empty error message for valid data"

    # Test invalid cases: empty title, invalid type, end before start, etc.
    invalid_cases = [
        {'title': ''},
        {'type': 'Invalid'},
        {'end_datetime': start_time - datetime.timedelta(hours=2)},
        {'timezone': 'Invalid/Timezone'},
        {'description': ''}
    ]

    for case in invalid_cases:
        # Create a new Interaction instance with the invalid data
        invalid_interaction = Interaction(
            site_id=site.id,
            title=case.get('title', 'Test Interaction'),
            type=case.get('type', InteractionType.MEETING.value),
            lead=case.get('lead', 'Test Lead'),
            start_datetime=case.get('start_datetime', start_time),
            end_datetime=case.get('end_datetime', end_time),
            timezone=case.get('timezone', 'UTC'),
            created_by=user.id,
            description=case.get('description', 'Test Description')
        )

        # Assert validate() returns (False, error_message) for each invalid case
        is_valid, error_message = invalid_interaction.validate()
        assert is_valid is False, f"validate() should return False for invalid case: {case}"
        assert error_message != '', f"validate() should return an error message for invalid case: {case}"


def test_interaction_to_dict(db_setup):
    """Tests that the Interaction to_dict method correctly serializes the model"""
    # Create a Site and User for foreign keys
    site = SiteFactory.create()
    user = UserFactory.create()

    # Create an Interaction instance with test data
    start_time = datetime.datetime.utcnow()
    end_time = start_time + datetime.timedelta(hours=1)
    interaction = Interaction(
        site_id=site.id,
        title='Test Interaction',
        type=InteractionType.MEETING.value,
        lead='Test Lead',
        start_datetime=start_time,
        end_datetime=end_time,
        timezone='UTC',
        created_by=user.id,
        description='Test Description'
    )

    # Call to_dict() on the instance
    interaction_dict = interaction.to_dict()

    # Assert the resulting dictionary contains all expected interaction properties
    assert 'id' in interaction_dict, "ID should be in the dictionary"
    assert 'site_id' in interaction_dict, "Site ID should be in the dictionary"
    assert 'title' in interaction_dict, "Title should be in the dictionary"
    assert 'type' in interaction_dict, "Type should be in the dictionary"
    assert 'lead' in interaction_dict, "Lead should be in the dictionary"
    assert 'start_datetime' in interaction_dict, "Start datetime should be in the dictionary"
    assert 'end_datetime' in interaction_dict, "End datetime should be in the dictionary"
    assert 'timezone' in interaction_dict, "Timezone should be in the dictionary"
    assert 'location' in interaction_dict, "Location should be in the dictionary"
    assert 'description' in interaction_dict, "Description should be in the dictionary"
    assert 'notes' in interaction_dict, "Notes should be in the dictionary"
    assert 'created_by' in interaction_dict, "Created by should be in the dictionary"
    assert 'created_at' in interaction_dict, "created_at should be in the dictionary"
    assert 'updated_at' in interaction_dict, "updated_at should be in the dictionary"

    # Assert datetime fields are serialized as ISO format strings
    assert isinstance(interaction_dict['start_datetime'], str), "start_datetime should be an ISO format string"
    assert isinstance(interaction_dict['end_datetime'], str), "end_datetime should be an ISO format string"
    assert isinstance(interaction_dict['created_at'], str), "created_at should be an ISO format string"
    assert isinstance(interaction_dict['updated_at'], str), "updated_at should be an ISO format string"


def test_interaction_duration(db_setup):
    """Tests that get_duration_minutes calculates the correct duration"""
    # Create Interaction with known start and end times (1 hour apart)
    site = SiteFactory.create()
    user = UserFactory.create()
    start_time = datetime.datetime.utcnow()
    end_time = start_time + datetime.timedelta(hours=1)
    interaction = Interaction(
        site_id=site.id,
        title='Test Interaction',
        type=InteractionType.MEETING.value,
        lead='Test Lead',
        start_datetime=start_time,
        end_datetime=end_time,
        timezone='UTC',
        created_by=user.id,
        description='Test Description'
    )

    # Call get_duration_minutes()
    duration = interaction.get_duration_minutes()

    # Assert result is 60 minutes
    assert duration == 60, "Duration should be 60 minutes"

    # Test with different durations (30 min, 2 hours, etc.)
    end_time = start_time + datetime.timedelta(minutes=30)
    interaction.end_datetime = end_time
    duration = interaction.get_duration_minutes()
    assert duration == 30, "Duration should be 30 minutes"

    end_time = start_time + datetime.timedelta(hours=2)
    interaction.end_datetime = end_time
    duration = interaction.get_duration_minutes()
    assert duration == 120, "Duration should be 120 minutes"


def test_interaction_update(db_setup):
    """Tests that the update method updates interaction properties correctly"""
    # Create an Interaction instance with initial data
    site = SiteFactory.create()
    user = UserFactory.create()
    start_time = datetime.datetime.utcnow()
    end_time = start_time + datetime.timedelta(hours=1)
    interaction = Interaction(
        site_id=site.id,
        title='Original Title',
        type=InteractionType.MEETING.value,
        lead='Original Lead',
        start_datetime=start_time,
        end_datetime=end_time,
        timezone='UTC',
        created_by=user.id,
        description='Original Description'
    )
    db.session.add(interaction)
    db.session.commit()

    # Call update() with new values
    new_data = {
        'title': 'New Title',
        'type': InteractionType.CALL.value,
        'lead': 'New Lead',
        'start_datetime': start_time + datetime.timedelta(days=1),
        'end_datetime': end_time + datetime.timedelta(days=1),
        'timezone': 'America/Los_Angeles',
        'description': 'New Description'
    }
    interaction.update(new_data)

    # Assert properties are updated to new values
    assert interaction.title == 'New Title', "Title should be updated"
    assert interaction.type == InteractionType.CALL.value, "Type should be updated"
    assert interaction.lead == 'New Lead', "Lead should be updated"
    assert interaction.start_datetime == start_time + datetime.timedelta(days=1), "Start datetime should be updated"
    assert interaction.end_datetime == end_time + datetime.timedelta(days=1), "End datetime should be updated"
    assert interaction.timezone == 'America/Los_Angeles', "Timezone should be updated"
    assert interaction.description == 'New Description', "Description should be updated"

    # Assert updated_at timestamp is updated
    assert interaction.updated_at > interaction.created_at, "Updated at should be updated"

    # Test that validation rules are still enforced during update
    with pytest.raises(ValueError):
        interaction.update({'end_datetime': start_time - datetime.timedelta(hours=1)})


def test_interaction_history_initialization(db_setup):
    """Tests that the InteractionHistory model initializes correctly"""
    # Create Interaction and User instances for foreign keys
    site = SiteFactory.create()
    user = UserFactory.create()
    interaction = InteractionFactory.create(site_id=site.id, created_by=user.id)

    # Create InteractionHistory instance with test data
    history = InteractionHistory(
        interaction_id=interaction.id,
        changed_by=user.id,
        change_type=CHANGE_TYPE_CREATE,
        before_state={'title': 'Old Title'},
        after_state={'title': 'New Title'}
    )

    # Assert all properties match provided values
    assert history.interaction_id == interaction.id, "Interaction ID should match provided value"
    assert history.changed_by == user.id, "Changed by should match provided value"
    assert history.change_type == CHANGE_TYPE_CREATE, "Change type should match provided value"
    assert history.before_state == {'title': 'Old Title'}, "Before state should match provided value"
    assert history.after_state == {'title': 'New Title'}, "After state should match provided value"

    # Assert created_at is set
    assert history.created_at is not None, "Created at should be set"


def test_interaction_history_to_dict(db_setup):
    """Tests that the InteractionHistory to_dict method correctly serializes the model"""
    # Create Interaction and User instances for foreign keys
    site = SiteFactory.create()
    user = UserFactory.create()
    interaction = InteractionFactory.create(site_id=site.id, created_by=user.id)

    # Create InteractionHistory instance with test data
    history = InteractionHistory(
        interaction_id=interaction.id,
        changed_by=user.id,
        change_type=CHANGE_TYPE_CREATE,
        before_state={'title': 'Old Title'},
        after_state={'title': 'New Title'}
    )

    # Call to_dict() on the instance
    history_dict = history.to_dict()

    # Assert the resulting dictionary contains all expected history properties
    assert 'id' in history_dict, "ID should be in the dictionary"
    assert 'interaction_id' in history_dict, "Interaction ID should be in the dictionary"
    assert 'changed_by' in history_dict, "Changed by should be in the dictionary"
    assert 'change_type' in history_dict, "Change type should be in the dictionary"
    assert 'before_state' in history_dict, "Before state should be in the dictionary"
    assert 'after_state' in history_dict, "After state should be in the dictionary"
    assert 'created_at' in history_dict, "created_at should be in the dictionary"
    assert 'updated_at' in history_dict, "updated_at should be in the dictionary"

    # Assert state snapshots are included in serialized form
    assert history_dict['before_state'] == {'title': 'Old Title'}, "Before state should be serialized"
    assert history_dict['after_state'] == {'title': 'New Title'}, "After state should be serialized"


def test_interaction_history_get_changes(db_setup):
    """Tests that get_changes correctly calculates differences between states"""
    # Create InteractionHistory with before and after states
    site = SiteFactory.create()
    user = UserFactory.create()
    interaction = InteractionFactory.create(site_id=site.id, created_by=user.id)
    history = InteractionHistory(
        interaction_id=interaction.id,
        changed_by=user.id,
        change_type=CHANGE_TYPE_UPDATE,
        before_state={'title': 'Old Title', 'description': 'Old Description'},
        after_state={'title': 'New Title', 'description': 'Old Description'}
    )

    # Call get_changes()
    changes = history.get_changes()

    # Assert only changed fields are included in result
    assert 'title' in changes, "Title should be in changes"
    assert 'description' not in changes, "Description should not be in changes"
    assert changes['title']['old'] == 'Old Title', "Old title should match before_state"
    assert changes['title']['new'] == 'New Title', "New title should match after_state"

    # Test different change types (create, update, delete)
    history.change_type = CHANGE_TYPE_CREATE
    history.before_state = None
    changes = history.get_changes()
    assert 'title' in changes, "Title should be in changes for create"
    assert 'description' in changes, "Description should be in changes for create"

    history.change_type = CHANGE_TYPE_DELETE
    history.after_state = None
    changes = history.get_changes()
    assert 'title' in changes, "Title should be in changes for delete"
    assert 'description' in changes, "Description should be in changes for delete"


def test_create_history_record_function(db_setup):
    """Tests the create_history_record utility function"""
    # Create Interaction and User instances
    site = SiteFactory.create()
    user = UserFactory.create()
    interaction = InteractionFactory.create(site_id=site.id, created_by=user.id)

    # Call create_history_record() with create type
    history_record = create_history_record(interaction, user.id, CHANGE_TYPE_CREATE)

    # Verify resulting history record has correct properties
    assert history_record.interaction_id == interaction.id, "Interaction ID should match"
    assert history_record.changed_by == user.id, "Changed by should match"
    assert history_record.change_type == CHANGE_TYPE_CREATE, "Change type should match"
    assert history_record.before_state is None, "Before state should be None for create"
    assert history_record.after_state == interaction.to_dict(), "After state should match interaction"

    # Test with different change types (update, delete)
    history_record = create_history_record(interaction, user.id, CHANGE_TYPE_UPDATE, before_state={'title': 'Old'})
    assert history_record.change_type == CHANGE_TYPE_UPDATE, "Change type should match"
    assert history_record.before_state == {'title': 'Old'}, "Before state should match provided value"

    history_record = create_history_record(interaction, user.id, CHANGE_TYPE_DELETE, before_state={'title': 'Old'})
    assert history_record.change_type == CHANGE_TYPE_DELETE, "Change type should match"
    assert history_record.after_state is None, "After state should be None for delete"