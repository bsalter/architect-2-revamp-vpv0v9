"""
Provides pytest fixtures for Interaction model testing, offering standardized test data for various 
interaction scenarios including different types, date ranges, and timezone configurations. These 
fixtures support unit tests, integration tests, and API tests requiring interaction data.
"""

import datetime
import pytz  # version 2023.3
import pytest  # version 7.3.1

from ...models.interaction import Interaction
from ...utils.enums import InteractionType, Timezone
from ...utils.datetime_util import get_utc_datetime, localize_datetime
from ..factories import InteractionFactory
from ...extensions import db


def create_interaction(site_id, title, type_value, lead, start_datetime, end_datetime, timezone, 
                      created_by, location, description, notes):
    """
    Helper function to create an interaction instance with the given parameters
    
    Args:
        site_id (int): The ID of the site
        title (str): Title of the interaction
        type_value (str): Type of interaction (must be a valid InteractionType)
        lead (str): Person leading the interaction
        start_datetime (datetime): Start date and time
        end_datetime (datetime): End date and time
        timezone (str): Timezone identifier
        created_by (int): ID of the user creating the interaction
        location (str): Location of the interaction
        description (str): Detailed description
        notes (str): Additional notes
        
    Returns:
        Interaction: Created Interaction instance
    """
    interaction = Interaction(
        site_id=site_id,
        title=title,
        type=type_value,
        lead=lead,
        start_datetime=start_datetime,
        end_datetime=end_datetime,
        timezone=timezone,
        created_by=created_by,
        location=location,
        description=description,
        notes=notes
    )
    
    # Add to database session and commit
    db.session.add(interaction)
    db.session.commit()
    
    return interaction


@pytest.fixture
def interaction(test_site, test_user, db_setup):
    """
    Fixture providing a basic interaction instance for tests
    
    Args:
        test_site (fixture): Fixture providing a test site
        test_user (fixture): Fixture providing a test user
        db_setup (fixture): Fixture setting up the database
        
    Returns:
        Interaction: Standard interaction instance for testing
    """
    # Get current UTC time for consistent test data
    now = get_utc_datetime(datetime.datetime.utcnow())
    end_time = get_utc_datetime(now + datetime.timedelta(hours=1))
    
    # Create a standard interaction using the helper function
    interaction = create_interaction(
        site_id=test_site.id,
        title="Test Interaction",
        type_value=InteractionType.MEETING.value,
        lead="Test Lead",
        start_datetime=now,
        end_datetime=end_time,
        timezone="UTC",
        created_by=test_user.id,
        location="Test Location",
        description="This is a test interaction for unit testing",
        notes="Additional test notes"
    )
    
    yield interaction
    # No cleanup needed as db_setup fixture will handle it


@pytest.fixture
def meeting_interaction(test_site, test_user, db_setup):
    """
    Fixture providing a meeting-type interaction for tests
    
    Args:
        test_site (fixture): Fixture providing a test site
        test_user (fixture): Fixture providing a test user
        db_setup (fixture): Fixture setting up the database
        
    Returns:
        Interaction: Meeting interaction instance for testing
    """
    now = get_utc_datetime(datetime.datetime.utcnow())
    end_time = get_utc_datetime(now + datetime.timedelta(hours=1))
    
    interaction = create_interaction(
        site_id=test_site.id,
        title="Team Planning Meeting",
        type_value=InteractionType.MEETING.value,
        lead="Meeting Organizer",
        start_datetime=now,
        end_datetime=end_time,
        timezone="Eastern",
        created_by=test_user.id,
        location="Conference Room A",
        description="Weekly team planning meeting to discuss project status and upcoming tasks",
        notes="Bring project documentation and status reports"
    )
    
    yield interaction


@pytest.fixture
def call_interaction(test_site, test_user, db_setup):
    """
    Fixture providing a call-type interaction for tests
    
    Args:
        test_site (fixture): Fixture providing a test site
        test_user (fixture): Fixture providing a test user
        db_setup (fixture): Fixture setting up the database
        
    Returns:
        Interaction: Call interaction instance for testing
    """
    now = get_utc_datetime(datetime.datetime.utcnow())
    # Call is shorter duration than meeting (30 minutes)
    end_time = get_utc_datetime(now + datetime.timedelta(minutes=30))
    
    interaction = create_interaction(
        site_id=test_site.id,
        title="Client Update Call",
        type_value=InteractionType.CALL.value,
        lead="Account Manager",
        start_datetime=now,
        end_datetime=end_time,
        timezone="Pacific",
        created_by=test_user.id,
        location="Phone Bridge",
        description="Monthly status update call with client to review progress",
        notes="Dial-in: 555-123-4567, Access code: 98765"
    )
    
    yield interaction


@pytest.fixture
def email_interaction(test_site, test_user, db_setup):
    """
    Fixture providing an email-type interaction for tests
    
    Args:
        test_site (fixture): Fixture providing a test site
        test_user (fixture): Fixture providing a test user
        db_setup (fixture): Fixture setting up the database
        
    Returns:
        Interaction: Email interaction instance for testing
    """
    now = get_utc_datetime(datetime.datetime.utcnow())
    # Email interactions typically have very short duration
    end_time = get_utc_datetime(now + datetime.timedelta(minutes=5))
    
    interaction = create_interaction(
        site_id=test_site.id,
        title="Project Requirements Email",
        type_value=InteractionType.EMAIL.value,
        lead="Project Manager",
        start_datetime=now,
        end_datetime=end_time,
        timezone="UTC",
        created_by=test_user.id,
        location=None,  # Emails typically don't have a location
        description="Email sent to stakeholders with updated project requirements document",
        notes="CC'd: dev-team@example.com, design-team@example.com"
    )
    
    yield interaction


@pytest.fixture
def past_interaction(test_site, test_user, db_setup):
    """
    Fixture providing an interaction with dates in the past
    
    Args:
        test_site (fixture): Fixture providing a test site
        test_user (fixture): Fixture providing a test user
        db_setup (fixture): Fixture setting up the database
        
    Returns:
        Interaction: Past interaction instance for testing
    """
    # Create dates 7 days in the past
    now = get_utc_datetime(datetime.datetime.utcnow())
    start_time = get_utc_datetime(now - datetime.timedelta(days=7))
    end_time = get_utc_datetime(start_time + datetime.timedelta(hours=1))
    
    interaction = create_interaction(
        site_id=test_site.id,
        title="Previous Strategy Session",
        type_value=InteractionType.MEETING.value,
        lead="Strategy Director",
        start_datetime=start_time,
        end_datetime=end_time,
        timezone="UTC",
        created_by=test_user.id,
        location="Executive Boardroom",
        description="Past strategy session to define quarterly objectives",
        notes="Action items were distributed via email on the following day"
    )
    
    yield interaction


@pytest.fixture
def future_interaction(test_site, test_user, db_setup):
    """
    Fixture providing an interaction with dates in the future
    
    Args:
        test_site (fixture): Fixture providing a test site
        test_user (fixture): Fixture providing a test user
        db_setup (fixture): Fixture setting up the database
        
    Returns:
        Interaction: Future interaction instance for testing
    """
    # Create dates 7 days in the future
    now = get_utc_datetime(datetime.datetime.utcnow())
    start_time = get_utc_datetime(now + datetime.timedelta(days=7))
    end_time = get_utc_datetime(start_time + datetime.timedelta(hours=1))
    
    interaction = create_interaction(
        site_id=test_site.id,
        title="Upcoming Product Launch",
        type_value=InteractionType.MEETING.value,
        lead="Product Manager",
        start_datetime=start_time,
        end_datetime=end_time,
        timezone="Central",
        created_by=test_user.id,
        location="Main Conference Hall",
        description="Product launch meeting to coordinate final preparations",
        notes="All teams should prepare status reports before the meeting"
    )
    
    yield interaction


@pytest.fixture
def multiple_interactions(test_site, test_user, db_setup):
    """
    Fixture providing multiple interaction instances for list testing
    
    Args:
        test_site (fixture): Fixture providing a test site
        test_user (fixture): Fixture providing a test user
        db_setup (fixture): Fixture setting up the database
        
    Returns:
        list: List of interaction instances
    """
    # Use the factory to create a batch of interactions
    interactions = InteractionFactory.create_batch_for_site(
        size=10,
        site=test_site,
        user=test_user
    )
    
    yield interactions


@pytest.fixture
def timezone_interactions(test_site, test_user, db_setup):
    """
    Fixture providing interactions with different timezone configurations
    
    Args:
        test_site (fixture): Fixture providing a test site
        test_user (fixture): Fixture providing a test user
        db_setup (fixture): Fixture setting up the database
        
    Returns:
        list: List of interactions in different timezones
    """
    now = get_utc_datetime(datetime.datetime.utcnow())
    interactions = []
    
    # Create an interaction for each timezone in the common zones
    for tz_name, tz_id in Timezone.COMMON_ZONES.items():
        # Create localized datetime objects for the timezone
        local_start = localize_datetime(now, tz_id)
        local_end = localize_datetime(now + datetime.timedelta(hours=1), tz_id)
        
        interaction = create_interaction(
            site_id=test_site.id,
            title=f"Timezone Test: {tz_name}",
            type_value=InteractionType.MEETING.value,
            lead="Timezone Tester",
            start_datetime=local_start,
            end_datetime=local_end,
            timezone=tz_name,
            created_by=test_user.id,
            location=f"{tz_name} Location",
            description=f"Test interaction in {tz_name} timezone",
            notes=f"Timezone identifier: {tz_id}"
        )
        
        interactions.append(interaction)
    
    yield interactions


@pytest.fixture
def invalid_interaction_data():
    """
    Fixture providing various sets of invalid interaction data for negative testing
    
    Returns:
        list: List of invalid interaction data dictionaries
    """
    now = datetime.datetime.utcnow()
    
    return [
        # Missing required fields
        {
            'site_id': 1,
            'title': None,  # Missing title
            'type': InteractionType.MEETING.value,
            'lead': 'Test Lead',
            'start_datetime': now,
            'end_datetime': now + datetime.timedelta(hours=1),
            'timezone': 'UTC',
            'created_by': 1
        },
        # Invalid interaction type
        {
            'site_id': 1,
            'title': 'Test Interaction',
            'type': 'InvalidType',  # Invalid type
            'lead': 'Test Lead',
            'start_datetime': now,
            'end_datetime': now + datetime.timedelta(hours=1),
            'timezone': 'UTC',
            'created_by': 1
        },
        # End date before start date
        {
            'site_id': 1,
            'title': 'Test Interaction',
            'type': InteractionType.MEETING.value,
            'lead': 'Test Lead',
            'start_datetime': now,
            'end_datetime': now - datetime.timedelta(hours=1),  # End before start
            'timezone': 'UTC',
            'created_by': 1
        },
        # Invalid timezone
        {
            'site_id': 1,
            'title': 'Test Interaction',
            'type': InteractionType.MEETING.value,
            'lead': 'Test Lead',
            'start_datetime': now,
            'end_datetime': now + datetime.timedelta(hours=1),
            'timezone': 'NonExistentTimezone',  # Invalid timezone
            'created_by': 1
        },
        # Missing site_id
        {
            'site_id': None,  # Missing site_id
            'title': 'Test Interaction',
            'type': InteractionType.MEETING.value,
            'lead': 'Test Lead',
            'start_datetime': now,
            'end_datetime': now + datetime.timedelta(hours=1),
            'timezone': 'UTC',
            'created_by': 1
        }
    ]