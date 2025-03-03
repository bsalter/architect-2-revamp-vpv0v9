"""
Test factories for the Interaction Management System.

This module provides factory classes for creating test instances of model objects with
default values for testing purposes. These factories are used in tests to generate
realistic test data consistently across test cases.
"""

import factory
import random
import string
import datetime
import pytz  # version 2023.3
from faker import Faker  # version 19.3.0

from ..models.user import User
from ..models.site import Site
from ..models.user_site import UserSite
from ..models.interaction import Interaction
from ..models.interaction_history import (
    InteractionHistory, 
    CHANGE_TYPE_CREATE, 
    CHANGE_TYPE_UPDATE, 
    CHANGE_TYPE_DELETE
)
from ..utils.enums import (
    InteractionType, 
    UserRole, 
    Timezone
)
from ..utils.datetime_util import get_utc_datetime


class UserFactory(factory.Factory):
    """
    Factory for creating User model instances for tests.
    
    Generates users with realistic usernames, emails, and other required fields
    for testing.
    """
    
    class Meta:
        model = User
    
    # Create a Faker instance with a fixed seed for reproducible tests
    faker = Faker()
    Faker.seed(12345)
    
    username = factory.LazyFunction(lambda: UserFactory.faker.user_name())
    email = factory.LazyFunction(lambda: UserFactory.faker.email())
    # Use a consistent password hash for testing
    password_hash = 'pbkdf2:sha256:150000$test$testpasswordhash'
    created_at = factory.LazyFunction(lambda: get_utc_datetime(datetime.datetime.utcnow()))
    last_login = factory.LazyFunction(
        lambda: get_utc_datetime(datetime.datetime.utcnow()) if random.choice([True, False]) else None
    )
    
    @classmethod
    def create_batch_with_sites(cls, size, sites, role=UserRole.VIEWER.value):
        """
        Create multiple users with associated sites.
        
        Args:
            size (int): Number of users to create
            sites (list): List of Site objects to associate with users
            role (str): Role to assign to users for these sites
            
        Returns:
            list: List of created User instances
        """
        users = cls.create_batch(size=size)
        for user in users:
            for site in sites:
                UserSiteFactory(
                    user=user,
                    site=site,
                    role=role
                )
        return users


class SiteFactory(factory.Factory):
    """
    Factory for creating Site model instances for tests.
    
    Generates sites with realistic names and descriptions for testing.
    """
    
    class Meta:
        model = Site
    
    # Create a Faker instance with a fixed seed for reproducible tests
    faker = Faker()
    Faker.seed(12345)
    
    name = factory.LazyFunction(lambda: SiteFactory.faker.company())
    description = factory.LazyFunction(lambda: SiteFactory.faker.text(max_nb_chars=200))
    created_at = factory.LazyFunction(lambda: get_utc_datetime(datetime.datetime.utcnow()))
    
    @classmethod
    def create_batch_with_users(cls, size, users, role=UserRole.VIEWER.value):
        """
        Create multiple sites with associated users.
        
        Args:
            size (int): Number of sites to create
            users (list): List of User objects to associate with sites
            role (str): Role to assign to users for these sites
            
        Returns:
            list: List of created Site instances
        """
        sites = cls.create_batch(size=size)
        for site in sites:
            for user in users:
                UserSiteFactory(
                    user=user,
                    site=site,
                    role=role
                )
        return sites


class UserSiteFactory(factory.Factory):
    """
    Factory for creating UserSite association instances for tests.
    
    Links users to sites with specific roles for testing site-scoped functionality.
    """
    
    class Meta:
        model = UserSite
    
    user = factory.SubFactory(UserFactory)
    site = factory.SubFactory(SiteFactory)
    role = UserRole.VIEWER.value


class InteractionFactory(factory.Factory):
    """
    Factory for creating Interaction model instances for tests.
    
    Generates interactions with realistic titles, descriptions, and temporal data
    for testing the interaction management functionality.
    """
    
    class Meta:
        model = Interaction
    
    # Create a Faker instance with a fixed seed for reproducible tests
    faker = Faker()
    Faker.seed(12345)
    
    site_id = factory.SubFactory(SiteFactory)
    title = factory.LazyFunction(lambda: InteractionFactory.faker.sentence(nb_words=6)[:-1])
    type = factory.LazyFunction(lambda: random.choice(InteractionType.get_values()))
    lead = factory.LazyFunction(lambda: InteractionFactory.faker.name())
    
    # Generate a recent datetime for start time
    start_datetime = factory.LazyFunction(
        lambda: get_utc_datetime(InteractionFactory.faker.date_time_between(
            start_date='-10d', end_date='+30d'
        ))
    )
    
    # End time is 1 hour after start time
    @factory.lazy_attribute
    def end_datetime(self):
        return get_utc_datetime(self.start_datetime + datetime.timedelta(hours=1))
    
    # Random timezone from common zones
    timezone = factory.LazyFunction(
        lambda: random.choice(list(Timezone.COMMON_ZONES.keys()))
    )
    
    # Generate a location or None for virtual meetings
    @factory.lazy_attribute
    def location(self):
        if random.choice([True, False, False]):  # 1/3 chance of being virtual
            return None
        return InteractionFactory.faker.address().split('\n')[0]
    
    description = factory.LazyFunction(
        lambda: InteractionFactory.faker.paragraph(nb_sentences=3)
    )
    
    # Notes field is optional
    @factory.lazy_attribute
    def notes(self):
        if random.choice([True, False]):
            return InteractionFactory.faker.text(max_nb_chars=200)
        return None
    
    created_by = factory.SubFactory(UserFactory)
    created_at = factory.LazyFunction(lambda: get_utc_datetime(datetime.datetime.utcnow()))
    updated_at = factory.LazyFunction(lambda: get_utc_datetime(datetime.datetime.utcnow()))
    
    @classmethod
    def create_batch_for_site(cls, size, site, user):
        """
        Create multiple interactions for a specific site.
        
        Args:
            size (int): Number of interactions to create
            site (Site): Site to associate interactions with
            user (User): User who creates the interactions
            
        Returns:
            list: List of created Interaction instances
        """
        return cls.create_batch(
            size=size,
            site_id=site.id,
            created_by=user.id
        )


class InteractionHistoryFactory(factory.Factory):
    """
    Factory for creating InteractionHistory model instances for tests.
    
    Generates history records for interactions to test audit trail functionality.
    """
    
    class Meta:
        model = InteractionHistory
    
    interaction_id = factory.SubFactory(InteractionFactory)
    changed_by = factory.SubFactory(UserFactory)
    created_at = factory.LazyFunction(lambda: get_utc_datetime(datetime.datetime.utcnow()))
    change_type = factory.LazyFunction(
        lambda: random.choice([CHANGE_TYPE_CREATE, CHANGE_TYPE_UPDATE, CHANGE_TYPE_DELETE])
    )
    
    @factory.lazy_attribute
    def before_state(self):
        """Generate appropriate before_state based on change_type"""
        if self.change_type == CHANGE_TYPE_CREATE:
            return None
        
        # For update and delete, generate a sample interaction state
        interaction = InteractionFactory.build()
        return interaction.to_dict()
    
    @factory.lazy_attribute
    def after_state(self):
        """Generate appropriate after_state based on change_type"""
        if self.change_type == CHANGE_TYPE_DELETE:
            return None
        
        # For create and update, generate a sample interaction state
        interaction = InteractionFactory.build()
        return interaction.to_dict()