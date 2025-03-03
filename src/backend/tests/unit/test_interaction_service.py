import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timedelta

from src.backend.services.interaction_service import InteractionService, CACHE_ENABLED  # InteractionService class being tested
from src.backend.utils.error_util import ValidationError, NotFoundError, SiteContextError  # Testing validation error handling
from src.backend.models.interaction_history import CHANGE_TYPE_CREATE, CHANGE_TYPE_UPDATE, CHANGE_TYPE_DELETE  # Constants for testing audit logging
from src.backend.models.interaction import Interaction  # For creating test interaction instances

# pytest version: 7.3.1
# unittest.mock version: N/A
# datetime version: N/A

def create_interaction_service_with_mocks():
    """Helper function to create an InteractionService instance with mocked dependencies for testing"""
    # Create mock objects for all dependencies: interaction_repository, site_context_service, user_context_service, validator, audit_logger, cache_service
    interaction_repository = Mock()
    site_context_service = Mock()
    user_context_service = Mock()
    validator = Mock()
    audit_logger = Mock()
    cache_service = Mock()

    # Configure basic mock behaviors like returning specific IDs
    user_context_service.get_current_user_id.return_value = 1
    site_context_service.get_current_site_id.return_value = 1
    interaction_repository.create_interaction.return_value.id = 1
    interaction_repository.update_interaction.return_value.id = 1

    # Create an InteractionService instance with these mocks
    service = InteractionService(
        interaction_repository=interaction_repository,
        site_context_service=site_context_service,
        user_context_service=user_context_service,
        validator=validator,
        audit_logger=audit_logger
    )

    # Return a tuple with the service and all mocks for test assertions
    return service, interaction_repository, site_context_service, user_context_service, validator, audit_logger, cache_service

@pytest.mark.unit
def test_create_interaction_success():
    """Tests that an interaction is successfully created with valid data"""
    # Set up test data for a valid interaction
    valid_data = {
        "site_id": 1,
        "title": "Test Interaction",
        "type": "Meeting",
        "lead": "John Doe",
        "start_datetime": datetime(2024, 1, 1, 10, 0, 0),
        "end_datetime": datetime(2024, 1, 1, 11, 0, 0),
        "timezone": "UTC",
        "description": "Test description",
        "created_by": 1
    }

    # Create service with mocked dependencies
    service, interaction_repository, _, _, validator, audit_logger, cache_service = create_interaction_service_with_mocks()

    # Set up mock behaviors for validation and repository
    validator.validate_create.return_value = valid_data
    interaction_repository.create_interaction.return_value = Mock(id=1, to_dict=lambda: valid_data)

    # Call service.create_interaction with valid data
    created_interaction = service.create_interaction(valid_data)

    # Assert repository.create_interaction was called with correct data
    interaction_repository.create_interaction.assert_called_once_with(valid_data)

    # Assert audit logger was called with correct parameters
    audit_logger.log_interaction_history.assert_called_once()

    # Assert cache service stored the created interaction
    if CACHE_ENABLED:
        cache_service.store_interaction.assert_called_once()

    # Assert the returned data matches expected format
    assert created_interaction == valid_data

@pytest.mark.unit
def test_create_interaction_validation_error():
    """Tests that ValidationError is raised when attempting to create an interaction with invalid data"""
    # Set up test data for an invalid interaction
    invalid_data = {
        "site_id": 1,
        "title": "",  # Invalid title
        "type": "Invalid",
        "lead": "John Doe",
        "start_datetime": datetime(2024, 1, 1, 10, 0, 0),
        "end_datetime": datetime(2024, 1, 1, 11, 0, 0),
        "timezone": "UTC",
        "description": "Test description",
        "created_by": 1
    }

    # Create service with mocked dependencies
    service, interaction_repository, _, _, validator, audit_logger, cache_service = create_interaction_service_with_mocks()

    # Configure validator mock to raise ValidationError
    validator.validate_create.side_effect = ValidationError("Validation failed")

    # Use pytest.raises to verify ValidationError is raised
    with pytest.raises(ValidationError):
        # Call service.create_interaction with invalid data
        service.create_interaction(invalid_data)

    # Assert repository.create_interaction was not called
    interaction_repository.create_interaction.assert_not_called()

    # Assert audit logger was not called
    audit_logger.log_interaction_history.assert_not_called()

    # Assert cache service was not called
    cache_service.store_interaction.assert_not_called()

@pytest.mark.unit
def test_create_interaction_site_context_error():
    """Tests that SiteContextError is properly handled when site context is invalid"""
    # Set up test data for a valid interaction
    valid_data = {
        "site_id": 1,
        "title": "Test Interaction",
        "type": "Meeting",
        "lead": "John Doe",
        "start_datetime": datetime(2024, 1, 1, 10, 0, 0),
        "end_datetime": datetime(2024, 1, 1, 11, 0, 0),
        "timezone": "UTC",
        "description": "Test description",
        "created_by": 1
    }

    # Create service with mocked dependencies
    service, interaction_repository, site_context_service, _, validator, audit_logger, cache_service = create_interaction_service_with_mocks()

    # Configure site_context_service mock to raise SiteContextError
    site_context_service.get_current_site_id.side_effect = SiteContextError("Invalid site context")

    # Use pytest.raises to verify SiteContextError is raised
    with pytest.raises(SiteContextError):
        # Call service.create_interaction with valid data
        service.create_interaction(valid_data)

    # Assert repository.create_interaction was not called
    interaction_repository.create_interaction.assert_not_called()

    # Assert audit logger was not called
    audit_logger.log_interaction_history.assert_not_called()

    # Assert cache service was not called
    cache_service.store_interaction.assert_not_called()

@pytest.mark.unit
def test_get_interaction_success():
    """Tests that an interaction is successfully retrieved by ID"""
    # Create service with mocked dependencies
    service, interaction_repository, _, _, _, audit_logger, cache_service = create_interaction_service_with_mocks()

    # Set up mock interaction data to be returned by repository
    interaction_data = {"id": 1, "title": "Test Interaction"}
    interaction_repository.find_by_id.return_value = Mock(id=1, to_dict=lambda: interaction_data)

    # Call service.get_interaction with valid ID
    retrieved_interaction = service.get_interaction(1)

    # Assert repository.find_by_id was called with correct ID
    interaction_repository.find_by_id.assert_called_once_with(1)

    # Assert audit logger logged data access
    audit_logger.log_data_access.assert_called_once()

    # Assert returned data matches expected format
    assert retrieved_interaction == interaction_data

    # Assert cache service was used to store the interaction
    if CACHE_ENABLED:
        cache_service.store_interaction.assert_called_once()

@pytest.mark.unit
def test_get_interaction_not_found():
    """Tests that None is returned when getting a non-existent interaction"""
    # Create service with mocked dependencies
    service, interaction_repository, _, _, _, audit_logger, cache_service = create_interaction_service_with_mocks()

    # Configure repository.find_by_id to return None
    interaction_repository.find_by_id.return_value = None

    # Call service.get_interaction with non-existent ID
    with pytest.raises(NotFoundError):
        service.get_interaction(1)

    # Assert repository.find_by_id was called with correct ID
    interaction_repository.find_by_id.assert_called_once_with(1)

    # Assert audit logger was not called
    audit_logger.log_data_access.assert_not_called()

    # Assert cache service was not called to store anything
    cache_service.store_interaction.assert_not_called()

@pytest.mark.unit
def test_get_interaction_site_context_error():
    """Tests SiteContextError handling when retrieving an interaction with invalid site context"""
    # Create service with mocked dependencies
    service, interaction_repository, site_context_service, _, _, audit_logger, cache_service = create_interaction_service_with_mocks()

    # Configure repository.find_by_id to raise SiteContextError
    interaction_repository.find_by_id.side_effect = SiteContextError("Invalid site context")

    # Use pytest.raises to verify SiteContextError is raised
    with pytest.raises(SiteContextError):
        # Call service.get_interaction with valid ID
        service.get_interaction(1)

    # Assert audit logger was not called
    audit_logger.log_data_access.assert_not_called()

    # Assert cache service was not called
    cache_service.store_interaction.assert_not_called()

@pytest.mark.unit
@patch('src.backend.services.interaction_service.CACHE_ENABLED', True)
def test_get_interaction_from_cache():
    """Tests that interaction is retrieved from cache when available"""
    # Create service with mocked dependencies
    service, interaction_repository, _, _, _, _, cache_service = create_interaction_service_with_mocks()

    # Configure cache_service.get_interaction to return cached interaction data
    cached_interaction_data = {"id": 1, "title": "Cached Interaction"}
    cache_service.get_interaction.return_value = cached_interaction_data

    # Call service.get_interaction with valid ID
    retrieved_interaction = service.get_interaction(1)

    # Assert cache_service.get_interaction was called with correct ID
    cache_service.get_interaction.assert_called_once_with(1)

    # Assert repository.find_by_id was not called
    interaction_repository.find_by_id.assert_not_called()

    # Assert returned data matches expected cached data
    assert retrieved_interaction == cached_interaction_data

@pytest.mark.unit
def test_get_interaction_by_id_success():
    """Tests that get_interaction_by_id successfully returns an interaction"""
    # Create service with mocked dependencies
    service, interaction_repository, _, _, _, _, _ = create_interaction_service_with_mocks()

    # Set up mock interaction data to be returned by repository
    interaction_data = {"id": 1, "title": "Test Interaction"}
    interaction_repository.find_by_id.return_value = Mock(id=1, to_dict=lambda: interaction_data)

    # Call service.get_interaction_by_id with valid ID
    retrieved_interaction = service.get_interaction_by_id(1)

    # Assert repository.find_by_id was called with correct ID
    interaction_repository.find_by_id.assert_called_once_with(1)

    # Assert returned data matches expected format
    assert retrieved_interaction == interaction_data

@pytest.mark.unit
def test_get_interaction_by_id_not_found():
    """Tests that NotFoundError is raised when interaction doesn't exist"""
    # Create service with mocked dependencies
    service, interaction_repository, _, _, _, _, _ = create_interaction_service_with_mocks()

    # Configure repository.find_by_id to return None
    interaction_repository.find_by_id.return_value = None

    # Use pytest.raises to verify NotFoundError is raised
    with pytest.raises(NotFoundError):
        # Call service.get_interaction_by_id with non-existent ID
        service.get_interaction_by_id(1)

@pytest.mark.unit
def test_update_interaction_success():
    """Tests that an interaction is successfully updated with valid data"""
    # Set up test data for updating an interaction
    update_data = {"title": "Updated Interaction Title"}
    existing_data = {"id": 1, "title": "Original Title", "site_id": 1}

    # Create service with mocked dependencies
    service, interaction_repository, _, _, validator, audit_logger, cache_service = create_interaction_service_with_mocks()

    # Set up mock behaviors for validation, repository, and existing interaction
    validator.validate_update.return_value = update_data
    interaction_repository.find_by_id.return_value = Mock(id=1, to_dict=lambda: existing_data)
    interaction_repository.update_interaction.return_value = Mock(id=1, to_dict=lambda: {**existing_data, **update_data})

    # Call service.update_interaction with valid ID and data
    updated_interaction = service.update_interaction(1, update_data)

    # Assert repository.update_interaction was called with correct data
    interaction_repository.update_interaction.assert_called_once_with(1, update_data)

    # Assert audit logger was called with correct parameters
    audit_logger.log_interaction_history.assert_called_once()

    # Assert cache service invalidated and stored the updated interaction
    if CACHE_ENABLED:
        cache_service.invalidate_interaction.assert_called_once()
        cache_service.store_interaction.assert_called_once()

    # Assert the returned data matches expected format
    assert updated_interaction == {**existing_data, **update_data}

@pytest.mark.unit
def test_update_interaction_validation_error():
    """Tests that ValidationError is raised when updating with invalid data"""
    # Set up test data for an invalid interaction update
    update_data = {"title": ""}  # Invalid title

    # Create service with mocked dependencies
    service, interaction_repository, _, _, validator, audit_logger, cache_service = create_interaction_service_with_mocks()

    # Configure validator mock to raise ValidationError
    validator.validate_update.side_effect = ValidationError("Validation failed")

    # Use pytest.raises to verify ValidationError is raised
    with pytest.raises(ValidationError):
        # Call service.update_interaction with invalid data
        service.update_interaction(1, update_data)

    # Assert repository.update_interaction was not called
    interaction_repository.update_interaction.assert_not_called()

    # Assert audit logger was not called
    audit_logger.log_interaction_history.assert_not_called()

    # Assert cache service did not invalidate or store anything
    cache_service.invalidate_interaction.assert_not_called()
    cache_service.store_interaction.assert_not_called()

@pytest.mark.unit
def test_update_interaction_not_found():
    """Tests that NotFoundError is raised when updating a non-existent interaction"""
    # Set up test data for updating an interaction
    update_data = {"title": "Updated Interaction Title"}

    # Create service with mocked dependencies
    service, interaction_repository, _, _, _, audit_logger, cache_service = create_interaction_service_with_mocks()

    # Configure repository.find_by_id to return None
    interaction_repository.find_by_id.side_effect = NotFoundError("Interaction not found")

    # Use pytest.raises to verify NotFoundError is raised
    with pytest.raises(NotFoundError):
        # Call service.update_interaction with non-existent ID
        service.update_interaction(1, update_data)

    # Assert repository.update_interaction was not called
    interaction_repository.update_interaction.assert_not_called()

    # Assert audit logger was not called
    audit_logger.log_interaction_history.assert_not_called()

    # Assert cache service did not store or invalidate anything
    cache_service.invalidate_interaction.assert_not_called()
    cache_service.store_interaction.assert_not_called()

@pytest.mark.unit
def test_update_interaction_site_context_error():
    """Tests SiteContextError handling when updating an interaction with invalid site context"""
    # Set up test data for updating an interaction
    update_data = {"title": "Updated Interaction Title"}

    # Create service with mocked dependencies
    service, interaction_repository, site_context_service, _, _, audit_logger, cache_service = create_interaction_service_with_mocks()

    # Configure repository.find_by_id to raise SiteContextError
    interaction_repository.find_by_id.side_effect = SiteContextError("Invalid site context")

    # Use pytest.raises to verify SiteContextError is raised
    with pytest.raises(SiteContextError):
        # Call service.update_interaction with valid ID and data
        service.update_interaction(1, update_data)

    # Assert repository.update_interaction was not called
    interaction_repository.update_interaction.assert_not_called()

    # Assert audit logger was not called
    audit_logger.log_interaction_history.assert_not_called()

    # Assert cache service did not store or invalidate anything
    cache_service.invalidate_interaction.assert_not_called()
    cache_service.store_interaction.assert_not_called()

@pytest.mark.unit
def test_delete_interaction_success():
    """Tests that an interaction is successfully deleted"""
    # Create service with mocked dependencies
    service, interaction_repository, _, _, _, audit_logger, cache_service = create_interaction_service_with_mocks()

    # Set up mock behaviors for repository and existing interaction
    interaction_repository.find_by_id.return_value = Mock(id=1, to_dict=lambda: {"id": 1, "title": "Test"})
    interaction_repository.delete.return_value = True

    # Call service.delete_interaction with valid ID
    deletion_result = service.delete_interaction(1)

    # Assert repository.delete was called with correct ID
    interaction_repository.delete.assert_called_once_with(1)

    # Assert audit logger was called with correct parameters
    audit_logger.log_interaction_history.assert_called_once()

    # Assert cache service invalidated the deleted interaction
    if CACHE_ENABLED:
        cache_service.invalidate_interaction.assert_called_once()

    # Assert True was returned indicating successful deletion
    assert deletion_result is True

@pytest.mark.unit
def test_delete_interaction_not_found():
    """Tests that NotFoundError is raised when deleting a non-existent interaction"""
    # Create service with mocked dependencies
    service, interaction_repository, _, _, _, audit_logger, cache_service = create_interaction_service_with_mocks()

    # Configure repository.find_by_id to return None
    interaction_repository.find_by_id.side_effect = NotFoundError("Interaction not found")

    # Use pytest.raises to verify NotFoundError is raised
    with pytest.raises(NotFoundError):
        # Call service.delete_interaction with non-existent ID
        service.delete_interaction(1)

    # Assert repository.delete was not called
    interaction_repository.delete.assert_not_called()

    # Assert audit logger was not called
    audit_logger.log_interaction_history.assert_not_called()

    # Assert cache service did not invalidate anything
    cache_service.invalidate_interaction.assert_not_called()

@pytest.mark.unit
def test_delete_interaction_site_context_error():
    """Tests SiteContextError handling when deleting an interaction with invalid site context"""
    # Create service with mocked dependencies
    service, interaction_repository, site_context_service, _, _, audit_logger, cache_service = create_interaction_service_with_mocks()

    # Configure repository.find_by_id to raise SiteContextError
    interaction_repository.find_by_id.side_effect = SiteContextError("Invalid site context")

    # Use pytest.raises to verify SiteContextError is raised
    with pytest.raises(SiteContextError):
        # Call service.delete_interaction with valid ID
        service.delete_interaction(1)

    # Assert repository.delete was not called
    interaction_repository.delete.assert_not_called()

    # Assert audit logger was not called
    audit_logger.log_interaction_history.assert_not_called()

    # Assert cache service did not invalidate anything
    cache_service.invalidate_interaction.assert_not_called()

@pytest.mark.unit
def test_get_upcoming_interactions():
    """Tests retrieving upcoming interactions"""
    # Create service with mocked dependencies
    service, interaction_repository, _, _, _, audit_logger, _ = create_interaction_service_with_mocks()

    # Set up mock behaviors for repository to return upcoming interactions
    upcoming_interactions = [
        Mock(id=1, title="Upcoming 1", to_dict=lambda: {"id": 1, "title": "Upcoming 1"}),
        Mock(id=2, title="Upcoming 2", to_dict=lambda: {"id": 2, "title": "Upcoming 2"})
    ]
    interaction_repository.get_upcoming_interactions.return_value = upcoming_interactions

    # Call service.get_upcoming_interactions with limit parameter
    limit = 5
    retrieved_interactions = service.get_upcoming_interactions(limit)

    # Assert repository.get_upcoming_interactions was called with correct limit
    interaction_repository.get_upcoming_interactions.assert_called_once_with(limit)

    # Assert audit logger logged data access
    audit_logger.log_data_access.assert_called_once()

    # Assert returned data matches expected format and count
    assert len(retrieved_interactions) == len(upcoming_interactions)
    assert retrieved_interactions == [{"id": 1, "title": "Upcoming 1"}, {"id": 2, "title": "Upcoming 2"}]

@pytest.mark.unit
def test_get_recent_interactions():
    """Tests retrieving recent interactions"""
    # Create service with mocked dependencies
    service, interaction_repository, _, _, _, audit_logger, _ = create_interaction_service_with_mocks()

    # Set up mock behaviors for repository to return recent interactions
    recent_interactions = [
        Mock(id=3, title="Recent 1", to_dict=lambda: {"id": 3, "title": "Recent 1"}),
        Mock(id=4, title="Recent 2", to_dict=lambda: {"id": 4, "title": "Recent 2"})
    ]
    interaction_repository.get_recent_interactions.return_value = recent_interactions

    # Call service.get_recent_interactions with limit parameter
    limit = 5
    retrieved_interactions = service.get_recent_interactions(limit)

    # Assert repository.get_recent_interactions was called with correct limit
    interaction_repository.get_recent_interactions.assert_called_once_with(limit)

    # Assert audit logger logged data access
    audit_logger.log_data_access.assert_called_once()

    # Assert returned data matches expected format and count
    assert len(retrieved_interactions) == len(recent_interactions)
    assert retrieved_interactions == [{"id": 3, "title": "Recent 1"}, {"id": 4, "title": "Recent 2"}]

@pytest.mark.unit
def test_format_interaction():
    """Tests the internal _format_interaction method"""
    # Create service with mocked dependencies
    service, _, _, _, _, _, _ = create_interaction_service_with_mocks()

    # Create a mock interaction with known properties
    mock_interaction = Mock(
        id=1,
        site_id=1,
        title="Test Interaction",
        type="Meeting",
        lead="John Doe",
        start_datetime=datetime(2024, 1, 1, 10, 0, 0),
        end_datetime=datetime(2024, 1, 1, 11, 0, 0),
        timezone="UTC",
        location="Test Location",
        description="Test Description",
        notes="Test Notes",
        created_by=1,
        created_at=datetime(2024, 1, 1, 9, 0, 0),
        updated_at=datetime(2024, 1, 1, 9, 30, 0),
        to_dict=lambda: {
            "id": 1,
            "site_id": 1,
            "title": "Test Interaction",
            "type": "Meeting",
            "lead": "John Doe",
            "start_datetime": datetime(2024, 1, 1, 10, 0, 0).isoformat(),
            "end_datetime": datetime(2024, 1, 1, 11, 0, 0).isoformat(),
            "timezone": "UTC",
            "location": "Test Location",
            "description": "Test Description",
            "notes": "Test Notes",
            "created_by": 1,
            "created_at": datetime(2024, 1, 1, 9, 0, 0).isoformat(),
            "updated_at": datetime(2024, 1, 1, 9, 30, 0).isoformat()
        }
    )

    # Create a test method to access the private _format_interaction method
    test_method = service._format_interaction

    # Call the test method with the mock interaction
    formatted_interaction = test_method(mock_interaction)

    # Assert the returned dictionary has all expected fields
    assert "id" in formatted_interaction
    assert "site_id" in formatted_interaction
    assert "title" in formatted_interaction
    assert "type" in formatted_interaction
    assert "lead" in formatted_interaction
    assert "start_datetime" in formatted_interaction
    assert "end_datetime" in formatted_interaction
    assert "timezone" in formatted_interaction
    assert "location" in formatted_interaction
    assert "description" in formatted_interaction
    assert "notes" in formatted_interaction
    assert "created_by" in formatted_interaction
    assert "created_at" in formatted_interaction
    assert "updated_at" in formatted_interaction

    # Assert datetime fields are converted to ISO format strings
    assert isinstance(formatted_interaction["start_datetime"], str)
    assert isinstance(formatted_interaction["end_datetime"], str)
    assert isinstance(formatted_interaction["created_at"], str)
    assert isinstance(formatted_interaction["updated_at"], str)

    # Assert all interaction properties are correctly represented
    assert formatted_interaction["id"] == 1
    assert formatted_interaction["site_id"] == 1
    assert formatted_interaction["title"] == "Test Interaction"
    assert formatted_interaction["type"] == "Meeting"
    assert formatted_interaction["lead"] == "John Doe"
    assert formatted_interaction["timezone"] == "UTC"
    assert formatted_interaction["location"] == "Test Location"
    assert formatted_interaction["description"] == "Test Description"
    assert formatted_interaction["notes"] == "Test Notes"
    assert formatted_interaction["created_by"] == 1

@pytest.mark.unit
def test_format_interaction_list():
    """Tests the internal _format_interaction_list method"""
    # Create service with mocked dependencies
    service, _, _, _, _, _, _ = create_interaction_service_with_mocks()

    # Create multiple mock interactions with known properties
    mock_interaction1 = Mock(
        id=1,
        site_id=1,
        title="Test Interaction 1",
        type="Meeting",
        lead="John Doe",
        start_datetime=datetime(2024, 1, 1, 10, 0, 0),
        end_datetime=datetime(2024, 1, 1, 11, 0, 0),
        timezone="UTC",
        location="Test Location",
        description="Test Description",
        notes="Test Notes",
        created_by=1,
        created_at=datetime(2024, 1, 1, 9, 0, 0),
        updated_at=datetime(2024, 1, 1, 9, 30, 0),
        to_dict=lambda: {
            "id": 1,
            "site_id": 1,
            "title": "Test Interaction 1",
            "type": "Meeting",
            "lead": "John Doe",
            "start_datetime": datetime(2024, 1, 1, 10, 0, 0).isoformat(),
            "end_datetime": datetime(2024, 1, 1, 11, 0, 0).isoformat(),
            "timezone": "UTC",
            "location": "Test Location",
            "description": "Test Description",
            "notes": "Test Notes",
            "created_by": 1,
            "created_at": datetime(2024, 1, 1, 9, 0, 0).isoformat(),
            "updated_at": datetime(2024, 1, 1, 9, 30, 0).isoformat()
        }
    )
    mock_interaction2 = Mock(
        id=2,
        site_id=1,
        title="Test Interaction 2",
        type="Call",
        lead="Jane Smith",
        start_datetime=datetime(2024, 1, 2, 14, 0, 0),
        end_datetime=datetime(2024, 1, 2, 15, 0, 0),
        timezone="UTC",
        location="Virtual",
        description="Another Test Description",
        notes="Another Test Notes",
        created_by=2,
        created_at=datetime(2024, 1, 2, 13, 0, 0),
        updated_at=datetime(2024, 1, 2, 13, 30, 0),
        to_dict=lambda: {
            "id": 2,
            "site_id": 1,
            "title": "Test Interaction 2",
            "type": "Call",
            "lead": "Jane Smith",
            "start_datetime": datetime(2024, 1, 2, 14, 0, 0).isoformat(),
            "end_datetime": datetime(2024, 1, 2, 15, 0, 0).isoformat(),
            "timezone": "UTC",
            "location": "Virtual",
            "description": "Another Test Description",
            "notes": "Another Test Notes",
            "created_by": 2,
            "created_at": datetime(2024, 1, 2, 13, 0, 0).isoformat(),
            "updated_at": datetime(2024, 1, 2, 13, 30, 0).isoformat()
        }
    )
    mock_interactions = [mock_interaction1, mock_interaction2]

    # Create a test method to access the private _format_interaction_list method
    test_method = service._format_interaction_list

    # Call the test method with the list of mock interactions
    formatted_interactions = test_method(mock_interactions)

    # Assert the returned list has the correct length
    assert len(formatted_interactions) == 2

    # Assert each item in the list has all expected fields
    for interaction in formatted_interactions:
        assert "id" in interaction
        assert "site_id" in interaction
        assert "title" in interaction
        assert "type" in interaction
        assert "lead" in interaction
        assert "start_datetime" in interaction
        assert "end_datetime" in interaction
        assert "timezone" in interaction
        assert "location" in interaction
        assert "description" in interaction
        assert "notes" in interaction
        assert "created_by" in interaction
        assert "created_at" in interaction
        assert "updated_at" in interaction

    # Assert all interaction properties are correctly represented in each list item
    assert formatted_interactions[0]["id"] == 1
    assert formatted_interactions[0]["title"] == "Test Interaction 1"
    assert formatted_interactions[1]["id"] == 2
    assert formatted_interactions[1]["type"] == "Call"