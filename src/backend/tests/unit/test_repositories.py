"""
Unit tests for repository classes that verify correct data access operations,
site-scoping enforcement, and transaction management. Tests focus on the
BaseRepository, InteractionRepository, and other repository implementations to
ensure they correctly handle CRUD operations with proper site isolation.
"""

import pytest  # pytest version 7.3.1
import sqlalchemy  # sqlalchemy version 2.0.19
from typing import Dict, List, Optional, Tuple, Any, Union  # standard library
from datetime import datetime  # standard library
from unittest import mock  # standard library

from ..repositories.base_repository import BaseRepository  # src/backend/repositories/base_repository.py
from ..repositories.interaction_repository import InteractionRepository  # src/backend/repositories/interaction_repository.py
from ..repositories.user_repository import UserRepository  # src/backend/repositories/user_repository.py
from ..repositories.site_repository import SiteRepository  # src/backend/repositories/site_repository.py
from ..repositories.connection_manager import ConnectionManager  # src/backend/repositories/connection_manager.py
from ..auth.site_context_service import SiteContextService  # src/backend/auth/site_context_service.py
from ..models.user import User  # src/backend/models/user.py
from ..models.site import Site  # src/backend/models/site.py
from ..models.interaction import Interaction  # src/backend/models/interaction.py
from .factories import UserFactory, SiteFactory, InteractionFactory  # src/backend/tests/factories.py
from ..utils.error_util import NotFoundError, DatabaseError, SiteContextError, ValidationError  # src/backend/utils/error_util.py
from ..utils.enums import InteractionType  # src/backend/utils/enums.py


@pytest.fixture
def mock_connection_manager():
    """Pytest fixture that creates a mocked ConnectionManager for testing repositories"""
    mock_conn_manager = mock.Mock(spec=ConnectionManager)
    mock_session = mock.Mock()
    mock_conn_manager.get_session.return_value = mock_session
    mock_conn_manager.transaction_context.return_value = mock.MagicMock()
    return mock_conn_manager


@pytest.fixture
def mock_site_context_service():
    """Pytest fixture that creates a mocked SiteContextService for testing site-scoped repositories"""
    mock_site_context = mock.Mock(spec=SiteContextService)
    mock_site_context.get_current_site_id.return_value = 1
    mock_site_context.apply_site_scope_to_query.return_value = mock.Mock()
    return mock_site_context


def test_base_repository_initialization(mock_connection_manager):
    """Test proper initialization of BaseRepository"""
    class TestModel:
        id = 1
        site_id = sqlalchemy.Column(sqlalchemy.Integer)

    class TestRepository(BaseRepository):
        def __init__(self, connection_manager):
            super().__init__(TestModel, connection_manager=connection_manager)

    repo = TestRepository(mock_connection_manager)
    assert repo._model_class == TestModel
    assert repo._site_column_name == 'site_id'
    assert repo._connection_manager == mock_connection_manager
    assert repo._get_current_site_id is not None
    assert repo._apply_site_scope_to_query is not None


def test_base_repository_get_query(mock_connection_manager, mock_site_context_service):
    """Test query creation with site-scoping applied"""
    class TestModel:
        id = 1
        site_id = sqlalchemy.Column(sqlalchemy.Integer)

    class TestRepository(BaseRepository):
        def __init__(self, connection_manager, site_context_service):
            super().__init__(TestModel, connection_manager=connection_manager,
                             get_current_site_id=site_context_service.get_current_site_id,
                             apply_site_scope_to_query=site_context_service.apply_site_scope_to_query)

    repo = TestRepository(mock_connection_manager, mock_site_context_service)
    mock_session = mock_connection_manager.get_session.return_value
    mock_query = mock.Mock()
    mock_session.query.return_value = mock_query
    mock_site_context_service.apply_site_scope_to_query.return_value = mock_query

    query = repo.get_query()

    mock_session.query.assert_called_with(TestModel)
    mock_site_context_service.apply_site_scope_to_query.assert_called_with(mock_query)
    assert query == mock_query


def test_base_repository_get_by_id(mock_connection_manager, mock_site_context_service):
    """Test retrieval of model by ID with site-scoping"""
    class TestModel:
        id = 1
        site_id = sqlalchemy.Column(sqlalchemy.Integer)

    class TestRepository(BaseRepository):
        def __init__(self, connection_manager, site_context_service):
            super().__init__(TestModel, connection_manager=connection_manager,
                             get_current_site_id=site_context_service.get_current_site_id,
                             apply_site_scope_to_query=site_context_service.apply_site_scope_to_query)

    repo = TestRepository(mock_connection_manager, mock_site_context_service)
    mock_query = mock.Mock()
    mock_query.filter.return_value.first.return_value = TestModel()
    repo.get_query = mock.Mock(return_value=mock_query)

    result = repo.get_by_id(1)

    repo.get_query.assert_called()
    mock_query.filter.assert_called_with(TestModel.id == 1)
    mock_query.filter.return_value.first.assert_called()
    assert isinstance(result, TestModel)

    mock_query.filter.return_value.first.return_value = None
    result = repo.get_by_id(999)
    assert result is None


def test_base_repository_find_by_id(mock_connection_manager, mock_site_context_service):
    """Test finding model by ID with exception for missing records"""
    class TestModel:
        id = 1
        site_id = sqlalchemy.Column(sqlalchemy.Integer)

    class TestRepository(BaseRepository):
        def __init__(self, connection_manager, site_context_service):
            super().__init__(TestModel, connection_manager=connection_manager,
                             get_current_site_id=site_context_service.get_current_site_id,
                             apply_site_scope_to_query=site_context_service.apply_site_scope_to_query)

    repo = TestRepository(mock_connection_manager, mock_site_context_service)
    mock_query = mock.Mock()
    mock_query.filter.return_value.first.return_value = TestModel()
    repo.get_by_id = mock.Mock(return_value=TestModel())

    result = repo.find_by_id(1)

    repo.get_by_id.assert_called_with(1)
    assert isinstance(result, TestModel)

    repo.get_by_id = mock.Mock(return_value=None)
    with pytest.raises(NotFoundError):
        repo.find_by_id(999)


def test_base_repository_get_all(mock_connection_manager, mock_site_context_service):
    """Test retrieval of all models with filtering and pagination"""
    class TestModel:
        id = 1
        site_id = sqlalchemy.Column(sqlalchemy.Integer)
        name = sqlalchemy.Column(sqlalchemy.String)

    class TestRepository(BaseRepository):
        def __init__(self, connection_manager, site_context_service):
            super().__init__(TestModel, connection_manager=connection_manager,
                             get_current_site_id=site_context_service.get_current_site_id,
                             apply_site_scope_to_query=site_context_service.apply_site_scope_to_query)

        def apply_filters(self, query, filters):
            return query

    repo = TestRepository(mock_connection_manager, mock_site_context_service)
    mock_query = mock.Mock()
    mock_query.offset.return_value.limit.return_value.all.return_value = [TestModel(), TestModel()]
    mock_query.count.return_value = 2
    repo.get_query = mock.Mock(return_value=mock_query)

    results, count = repo.get_all()

    repo.get_query.assert_called()
    mock_query.offset.assert_called_with(0)
    mock_query.limit.assert_called_with(20)
    mock_query.offset.return_value.limit.return_value.all.assert_called()
    assert len(results) == 2
    assert count == 2

    filters = {'name': 'test'}
    sort_by = 'name'
    sort_desc = True
    results, count = repo.get_all(filters=filters, page=2, per_page=10, sort_by=sort_by, sort_desc=sort_desc)

    repo.get_query.assert_called()
    mock_query.offset.assert_called_with(10)
    mock_query.limit.assert_called_with(10)
    mock_query.offset.return_value.limit.return_value.all.assert_called()
    assert len(results) == 2
    assert count == 2


def test_base_repository_create(mock_connection_manager, mock_site_context_service):
    """Test creation of new model with site association"""
    class TestModel:
        id = 1
        site_id = sqlalchemy.Column(sqlalchemy.Integer)

        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)

    class TestRepository(BaseRepository):
        def __init__(self, connection_manager, site_context_service):
            super().__init__(TestModel, connection_manager=connection_manager,
                             get_current_site_id=site_context_service.get_current_site_id,
                             apply_site_scope_to_query=site_context_service.apply_site_scope_to_query)

    repo = TestRepository(mock_connection_manager, mock_site_context_service)
    mock_session = mock_connection_manager.get_session.return_value
    mock_site_context_service.get_current_site_id.return_value = 1
    data = {'name': 'test'}

    result = repo.create(data)

    mock_site_context_service.get_current_site_id.assert_called()
    assert data['site_id'] == 1
    mock_session.add.assert_called()
    mock_session.commit.assert_called()
    mock_session.refresh.assert_called()
    assert isinstance(result, TestModel)
    assert result.name == 'test'
    assert result.site_id == 1


def test_base_repository_update(mock_connection_manager, mock_site_context_service):
    """Test updating an existing model with site-scoping validation"""
    class TestModel:
        id = 1
        site_id = sqlalchemy.Column(sqlalchemy.Integer)
        name = 'old_name'

    class TestRepository(BaseRepository):
        def __init__(self, connection_manager, site_context_service):
            super().__init__(TestModel, connection_manager=connection_manager,
                             get_current_site_id=site_context_service.get_current_site_id,
                             apply_site_scope_to_query=site_context_service.apply_site_scope_to_query)

    repo = TestRepository(mock_connection_manager, mock_site_context_service)
    mock_session = mock_connection_manager.get_session.return_value
    mock_find_by_id = mock.Mock(return_value=TestModel())
    repo.find_by_id = mock_find_by_id
    data = {'name': 'new_name'}

    result = repo.update(1, data)

    mock_find_by_id.assert_called_with(1)
    assert result.name == 'new_name'
    mock_session.commit.assert_called()

    repo.find_by_id = mock.Mock(side_effect=NotFoundError("Not found"))
    with pytest.raises(NotFoundError):
        repo.update(999, data)


def test_base_repository_delete(mock_connection_manager, mock_site_context_service):
    """Test deletion of a model by ID with site-scoping"""
    class TestModel:
        id = 1
        site_id = sqlalchemy.Column(sqlalchemy.Integer)

    class TestRepository(BaseRepository):
        def __init__(self, connection_manager, site_context_service):
            super().__init__(TestModel, connection_manager=connection_manager,
                             get_current_site_id=site_context_service.get_current_site_id,
                             apply_site_scope_to_query=site_context_service.apply_site_scope_to_query)

    repo = TestRepository(mock_connection_manager, mock_site_context_service)
    mock_session = mock_connection_manager.get_session.return_value
    mock_get_by_id = mock.Mock(return_value=TestModel())
    repo.get_by_id = mock_get_by_id

    result = repo.delete(1)

    mock_get_by_id.assert_called_with(1)
    mock_session.delete.assert_called()
    mock_session.commit.assert_called()
    assert result is True

    repo.get_by_id = mock.Mock(return_value=None)
    result = repo.delete(999)
    assert result is False


def test_interaction_repository_init(mock_connection_manager, mock_site_context_service):
    """Test proper initialization of InteractionRepository"""
    repo = InteractionRepository(mock_connection_manager, mock_site_context_service)
    assert repo._model_class == Interaction
    assert repo._site_column_name == 'site_id'
    assert repo._connection_manager == mock_connection_manager
    assert repo._site_context_service == mock_site_context_service
    assert repo._get_current_site_id == mock_site_context_service.get_current_site_id
    assert repo._apply_site_scope_to_query == mock_site_context_service.apply_site_scope_to_query


def test_interaction_repository_validate_interaction(mock_connection_manager, mock_site_context_service):
    """Test validation of interaction data before saving"""
    repo = InteractionRepository(mock_connection_manager, mock_site_context_service)
    valid_data = {
        'title': 'Test Interaction',
        'type': InteractionType.MEETING.value,
        'lead': 'Test Lead',
        'start_datetime': datetime.now(),
        'end_datetime': datetime.now() + sqlalchemy.timedelta(hours=1),
        'timezone': 'UTC',
        'description': 'Test Description'
    }
    validated_data = repo.validate_interaction(valid_data)
    assert validated_data == valid_data

    invalid_data = valid_data.copy()
    del invalid_data['title']
    with pytest.raises(ValidationError):
        repo.validate_interaction(invalid_data)

    invalid_data = valid_data.copy()
    invalid_data['title'] = 'a' * 200
    with pytest.raises(ValidationError):
        repo.validate_interaction(invalid_data)

    invalid_data = valid_data.copy()
    invalid_data['type'] = 'Invalid'
    with pytest.raises(ValidationError):
        repo.validate_interaction(invalid_data)

    invalid_data = valid_data.copy()
    invalid_data['end_datetime'] = datetime.now() - sqlalchemy.timedelta(hours=2)
    with pytest.raises(ValidationError):
        repo.validate_interaction(invalid_data)


def test_interaction_repository_create_interaction(mock_connection_manager, mock_site_context_service):
    """Test creation of interaction with validation"""
    repo = InteractionRepository(mock_connection_manager, mock_site_context_service)
    repo.validate_interaction = mock.Mock(return_value={'validated': True})
    repo.create = mock.Mock(return_value=Interaction())
    valid_data = {'title': 'Test Interaction', 'type': InteractionType.MEETING.value, 'lead': 'Test Lead',
                  'start_datetime': datetime.now(), 'end_datetime': datetime.now() + sqlalchemy.timedelta(hours=1),
                  'timezone': 'UTC', 'description': 'Test Description'}

    result = repo.create_interaction(valid_data)

    repo.validate_interaction.assert_called_with(valid_data)
    repo.create.assert_called()
    assert isinstance(result, Interaction)

    repo.validate_interaction = mock.Mock(side_effect=ValidationError("Invalid data"))
    with pytest.raises(ValidationError):
        repo.create_interaction(valid_data)


def test_interaction_repository_update_interaction(mock_connection_manager, mock_site_context_service):
    """Test updating an interaction with validation"""
    repo = InteractionRepository(mock_connection_manager, mock_site_context_service)
    repo.validate_interaction = mock.Mock(return_value={'validated': True})
    repo.find_by_id = mock.Mock(return_value=Interaction())
    repo.update = mock.Mock(return_value=Interaction())
    valid_data = {'title': 'Test Interaction', 'type': InteractionType.MEETING.value, 'lead': 'Test Lead',
                  'start_datetime': datetime.now(), 'end_datetime': datetime.now() + sqlalchemy.timedelta(hours=1),
                  'timezone': 'UTC', 'description': 'Test Description'}

    result = repo.update_interaction(1, valid_data)

    repo.find_by_id.assert_called_with(1)
    repo.validate_interaction.assert_called()
    repo.update.assert_called()
    assert isinstance(result, Interaction)

    repo.validate_interaction = mock.Mock(side_effect=ValidationError("Invalid data"))
    with pytest.raises(ValidationError):
        repo.update_interaction(1, valid_data)

    repo.find_by_id = mock.Mock(side_effect=NotFoundError("Not found"))
    with pytest.raises(NotFoundError):
        repo.update_interaction(999, valid_data)


def test_interaction_repository_find_by_date_range(mock_connection_manager, mock_site_context_service):
    """Test finding interactions within a date range"""
    repo = InteractionRepository(mock_connection_manager, mock_site_context_service)
    mock_query = mock.Mock()
    mock_query.offset.return_value.limit.return_value.all.return_value = [Interaction(), Interaction()]
    mock_query.count.return_value = 2
    repo.get_query = mock.Mock(return_value=mock_query)
    start_date = datetime.now()
    end_date = datetime.now() + sqlalchemy.timedelta(days=1)

    interactions, count = repo.find_by_date_range(start_date, end_date)

    repo.get_query.assert_called()
    mock_query.filter.assert_called()
    mock_query.offset.assert_called_with(0)
    mock_query.limit.assert_called_with(20)
    assert len(interactions) == 2
    assert count == 2

    with pytest.raises(ValidationError):
        repo.find_by_date_range(end_date, start_date)


def test_interaction_repository_find_by_type(mock_connection_manager, mock_site_context_service):
    """Test finding interactions by type"""
    repo = InteractionRepository(mock_connection_manager, mock_site_context_service)
    mock_query = mock.Mock()
    mock_query.offset.return_value.limit.return_value.all.return_value = [Interaction(), Interaction()]
    mock_query.count.return_value = 2
    repo.get_query = mock.Mock(return_value=mock_query)

    interactions, count = repo.find_by_type(InteractionType.MEETING.value)

    repo.get_query.assert_called()
    mock_query.filter.assert_called()
    mock_query.offset.assert_called_with(0)
    mock_query.limit.assert_called_with(20)
    assert len(interactions) == 2
    assert count == 2

    with pytest.raises(ValidationError):
        repo.find_by_type('Invalid')


def test_interaction_repository_find_by_lead(mock_connection_manager, mock_site_context_service):
    """Test finding interactions by lead person"""
    repo = InteractionRepository(mock_connection_manager, mock_site_context_service)
    mock_query = mock.Mock()
    mock_query.offset.return_value.limit.return_value.all.return_value = [Interaction(), Interaction()]
    mock_query.count.return_value = 2
    repo.get_query = mock.Mock(return_value=mock_query)

    interactions, count = repo.find_by_lead('Test Lead')

    repo.get_query.assert_called()
    mock_query.filter.assert_called()
    mock_query.offset.assert_called_with(0)
    mock_query.limit.assert_called_with(20)
    assert len(interactions) == 2
    assert count == 2

    with pytest.raises(ValidationError):
        repo.find_by_lead('')


def test_interaction_repository_search(mock_connection_manager, mock_site_context_service):
    """Test searching interactions across all fields"""
    repo = InteractionRepository(mock_connection_manager, mock_site_context_service)
    mock_query = mock.Mock()
    mock_query.offset.return_value.limit.return_value.all.return_value = [Interaction(), Interaction()]
    mock_query.count.return_value = 2
    repo.get_query = mock.Mock(return_value=mock_query)

    interactions, count = repo.search('Test')

    repo.get_query.assert_called()
    mock_query.filter.assert_called()
    mock_query.offset.assert_called_with(0)
    mock_query.limit.assert_called_with(20)
    assert len(interactions) == 2
    assert count == 2

    with pytest.raises(ValidationError):
        repo.search('')


def test_interaction_repository_advanced_search(mock_connection_manager, mock_site_context_service):
    """Test advanced search with multiple filter criteria"""
    repo = InteractionRepository(mock_connection_manager, mock_site_context_service)
    mock_query = mock.Mock()
    mock_query.offset.return_value.limit.return_value.all.return_value = [Interaction(), Interaction()]
    mock_query.count.return_value = 2
    repo.get_query = mock.Mock(return_value=mock_query)
    filters = {'title': 'Test', 'type': InteractionType.MEETING.value}

    interactions, count = repo.advanced_search(filters)

    repo.get_query.assert_called()
    mock_query.filter.assert_called()
    mock_query.offset.assert_called_with(0)
    mock_query.limit.assert_called_with(20)
    assert len(interactions) == 2
    assert count == 2


def test_interaction_repository_get_upcoming_interactions(mock_connection_manager, mock_site_context_service):
    """Test retrieving upcoming interactions"""
    repo = InteractionRepository(mock_connection_manager, mock_site_context_service)
    mock_query = mock.Mock()
    mock_query.order_by.return_value.limit.return_value.all.return_value = [Interaction(), Interaction()]
    repo.get_query = mock.Mock(return_value=mock_query)

    with mock.patch('src.backend.repositories.interaction_repository.datetime') as mock_datetime:
        mock_datetime.utcnow.return_value = datetime(2024, 1, 1)
        interactions = repo.get_upcoming_interactions()

    repo.get_query.assert_called()
    mock_query.filter.assert_called()
    mock_query.order_by.return_value.limit.return_value.all.assert_called()
    assert len(interactions) == 2


def test_interaction_repository_get_recent_interactions(mock_connection_manager, mock_site_context_service):
    """Test retrieving recently past interactions"""
    repo = InteractionRepository(mock_connection_manager, mock_site_context_service)
    mock_query = mock.Mock()
    mock_query.order_by.return_value.limit.return_value.all.return_value = [Interaction(), Interaction()]
    repo.get_query = mock.Mock(return_value=mock_query)

    with mock.patch('src.backend.repositories.interaction_repository.datetime') as mock_datetime:
        mock_datetime.utcnow.return_value = datetime(2024, 1, 1)
        interactions = repo.get_recent_interactions()

    repo.get_query.assert_called()
    mock_query.filter.assert_called()
    mock_query.order_by.return_value.limit.return_value.all.assert_called()
    assert len(interactions) == 2


def test_site_context_enforcement(mock_connection_manager, mock_site_context_service):
    """Test that site context is properly enforced in repositories"""
    class TestModel:
        id = 1
        site_id = sqlalchemy.Column(sqlalchemy.Integer)

    class TestRepository(BaseRepository):
        def __init__(self, connection_manager, site_context_service):
            super().__init__(TestModel, connection_manager=connection_manager,
                             get_current_site_id=site_context_service.get_current_site_id,
                             apply_site_scope_to_query=site_context_service.apply_site_scope_to_query)

    repo = TestRepository(mock_connection_manager, mock_site_context_service)
    mock_query = mock.Mock()
    mock_query.filter.return_value.first.return_value = TestModel()
    repo.get_query = mock.Mock(return_value=mock_query)

    repo.get_all()
    mock_site_context_service.apply_site_scope_to_query.assert_called()

    repo.get_by_id(1)
    mock_site_context_service.apply_site_scope_to_query.assert_called()

    repo.find_by_id(1)
    mock_site_context_service.apply_site_scope_to_query.assert_called()

    mock_site_context_service.get_current_site_id.return_value = None
    repo.get_by_id(1)
    mock_site_context_service.apply_site_scope_to_query.assert_called()


def test_transaction_management(mock_connection_manager, mock_site_context_service):
    """Test transaction management in repositories"""
    class TestModel:
        id = 1
        site_id = sqlalchemy.Column(sqlalchemy.Integer)

    class TestRepository(BaseRepository):
        def __init__(self, connection_manager, site_context_service):
            super().__init__(TestModel, connection_manager=connection_manager,
                             get_current_site_id=site_context_service.get_current_site_id,
                             apply_site_scope_to_query=site_context_service.apply_site_scope_to_query)

    repo = TestRepository(mock_connection_manager, mock_site_context_service)
    mock_session = mock_connection_manager.get_session.return_value
    mock_transaction_context = mock.MagicMock()
    mock_connection_manager.transaction_context.return_value = mock_transaction_context

    repo.create({})
    mock_connection_manager.transaction_context.assert_called()

    repo.update(1, {})
    mock_connection_manager.transaction_context.assert_called()

    repo.delete(1)
    mock_connection_manager.transaction_context.assert_called()

    mock_transaction_context.__enter__.side_effect = Exception("Transaction failed")
    with pytest.raises(Exception):
        repo.create({})