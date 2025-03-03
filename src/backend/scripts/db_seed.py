#!/usr/bin/env python3
"""
Database Seeding Script for the Interaction Management System.

This script populates the application database with initial data for development,
testing, and demonstration purposes. It creates users, sites, user-site associations,
and sample interactions with appropriate relationships.

Usage:
    python db_seed.py [--clean] [--count COUNT] [--env ENV]

Options:
    --clean         Drop all existing data before seeding
    --count COUNT   Number of interactions to create per site (default: 10)
    --env ENV       Environment to run in (development, staging, testing, production)
                    Default is development
"""

import argparse
import datetime
import random
import logging
import pytz  # version 2023.3
import sys
from datetime import datetime, timedelta

from ..models.user import User
from ..models.site import Site
from ..models.interaction import Interaction
from ..repositories.connection_manager import ConnectionManager
from ..utils.enums import InteractionType, UserRole, Timezone
from ..utils.datetime_util import get_utc_datetime
from ..config import BASE_DIR, CONFIG

# Configure logger
logger = logging.getLogger(__name__)

# Default admin password - would be changed in production
DEFAULT_ADMIN_PASSWORD = "Admin123!"

def create_users(session):
    """
    Create user accounts for testing including administrators and regular users.
    
    Args:
        session: SQLAlchemy session object
        
    Returns:
        dict: Dictionary of created users by username
    """
    logger.info("Creating test users...")
    users = {}
    
    # Create admin users
    admin_users = [
        User("admin", "admin@example.com", DEFAULT_ADMIN_PASSWORD),
        User("site1admin", "site1admin@example.com", DEFAULT_ADMIN_PASSWORD),
        User("site2admin", "site2admin@example.com", DEFAULT_ADMIN_PASSWORD),
        User("site3admin", "site3admin@example.com", DEFAULT_ADMIN_PASSWORD)
    ]
    
    # Create regular users with different permission levels
    regular_users = [
        User("user1", "user1@example.com", "User123!"),
        User("user2", "user2@example.com", "User123!"),
        User("user3", "user3@example.com", "User123!"),
        User("editor1", "editor1@example.com", "Editor123!"),
        User("editor2", "editor2@example.com", "Editor123!"),
        User("viewer1", "viewer1@example.com", "Viewer123!"),
        User("viewer2", "viewer2@example.com", "Viewer123!")
    ]
    
    # Combine all users
    all_users = admin_users + regular_users
    
    # Add users to session
    for user in all_users:
        session.add(user)
        users[user.username] = user
    
    # Commit to get IDs
    session.commit()
    
    logger.info(f"Created {len(users)} users")
    return users

def create_sites(session):
    """
    Create organizational sites for multi-tenant demonstration.
    
    Args:
        session: SQLAlchemy session object
        
    Returns:
        dict: Dictionary of created sites by name
    """
    logger.info("Creating organization sites...")
    sites = {}
    
    # Create site objects
    site_data = [
        ("Headquarters", "Main corporate headquarters"),
        ("Northwest Regional Office", "Regional office serving the Northwest"),
        ("Southwest Regional Office", "Regional office serving the Southwest"),
        ("Eastern Division", "Division covering all Eastern operations")
    ]
    
    for name, description in site_data:
        site = Site(name, description)
        session.add(site)
        sites[name] = site
    
    # Commit to get IDs
    session.commit()
    
    logger.info(f"Created {len(sites)} sites")
    return sites

def associate_users_with_sites(session, users, sites):
    """
    Create user-site associations with appropriate roles.
    
    Args:
        session: SQLAlchemy session object
        users: Dictionary of users by username
        sites: Dictionary of sites by name
    """
    logger.info("Creating user-site associations...")
    
    # Main admin has access to all sites as admin
    for site in sites.values():
        stmt = "INSERT INTO user_sites (user_id, site_id, role) VALUES (:user_id, :site_id, :role)"
        session.execute(stmt, {
            "user_id": users["admin"].id,
            "site_id": site.id,
            "role": UserRole.SITE_ADMIN.value
        })
    
    # Site-specific admins
    site_admins = {
        "site1admin": "Headquarters",
        "site2admin": "Northwest Regional Office",
        "site3admin": "Southwest Regional Office"
    }
    
    for username, site_name in site_admins.items():
        stmt = "INSERT INTO user_sites (user_id, site_id, role) VALUES (:user_id, :site_id, :role)"
        session.execute(stmt, {
            "user_id": users[username].id,
            "site_id": sites[site_name].id,
            "role": UserRole.SITE_ADMIN.value
        })
    
    # Regular users with varied permissions
    user_site_roles = [
        # username, site_name, role
        ("user1", "Headquarters", UserRole.EDITOR.value),
        ("user1", "Northwest Regional Office", UserRole.VIEWER.value),
        ("user2", "Southwest Regional Office", UserRole.EDITOR.value),
        ("user2", "Eastern Division", UserRole.VIEWER.value),
        ("user3", "Eastern Division", UserRole.EDITOR.value),
        ("editor1", "Headquarters", UserRole.EDITOR.value),
        ("editor1", "Northwest Regional Office", UserRole.EDITOR.value),
        ("editor2", "Southwest Regional Office", UserRole.EDITOR.value),
        ("editor2", "Eastern Division", UserRole.EDITOR.value),
        ("viewer1", "Headquarters", UserRole.VIEWER.value),
        ("viewer1", "Northwest Regional Office", UserRole.VIEWER.value),
        ("viewer2", "Southwest Regional Office", UserRole.VIEWER.value),
        ("viewer2", "Eastern Division", UserRole.VIEWER.value)
    ]
    
    for username, site_name, role in user_site_roles:
        stmt = "INSERT INTO user_sites (user_id, site_id, role) VALUES (:user_id, :site_id, :role)"
        session.execute(stmt, {
            "user_id": users[username].id,
            "site_id": sites[site_name].id,
            "role": role
        })
    
    # Commit the changes
    session.commit()
    
    logger.info("User-site associations created")

def create_interactions(session, users, sites, count_per_site=10):
    """
    Create sample interaction records for each site.
    
    Args:
        session: SQLAlchemy session object
        users: Dictionary of users by username
        sites: Dictionary of sites by name
        count_per_site: Number of interactions to create per site
    """
    logger.info(f"Creating {count_per_site} interactions per site...")
    
    interaction_types = [
        InteractionType.MEETING.value,
        InteractionType.CALL.value,
        InteractionType.EMAIL.value
    ]
    
    # Get timezone options from our enum
    timezone_options = list(Timezone.COMMON_ZONES.keys())
    
    # For each site, create a set of interactions
    for site_name, site in sites.items():
        logger.info(f"Creating interactions for {site_name}...")
        
        # Find users with access to this site
        site_users = []
        for username, user in users.items():
            # Query to check if user has access to this site
            result = session.execute(
                "SELECT role FROM user_sites WHERE user_id = :user_id AND site_id = :site_id",
                {"user_id": user.id, "site_id": site.id}
            ).fetchone()
            
            if result:
                site_users.append(user)
        
        if not site_users:
            logger.warning(f"No users found for site {site_name}, skipping interaction creation")
            continue
        
        # Create past, current, and future interactions
        past_count = count_per_site // 3
        current_count = count_per_site // 3
        future_count = count_per_site - past_count - current_count
        
        # Create past interactions
        for i in range(past_count):
            created_by = random.choice(site_users)
            interaction_type = random.choice(interaction_types)
            timezone = random.choice(timezone_options)
            start_dt, end_dt = generate_datetime_pairs("past")
            
            interaction = Interaction(
                site_id=site.id,
                title=generate_sample_data("title", site_name),
                type=interaction_type,
                lead=generate_sample_data("lead", site_name),
                start_datetime=start_dt,
                end_datetime=end_dt,
                timezone=timezone,
                location=generate_sample_data("location", site_name),
                description=generate_sample_data("description", site_name),
                notes=generate_sample_data("notes", site_name),
                created_by=created_by.id
            )
            
            # Validate before adding
            is_valid, error = interaction.validate()
            if is_valid:
                session.add(interaction)
            else:
                logger.warning(f"Invalid interaction data: {error}")
                
        # Create current interactions (around current date)
        for i in range(current_count):
            created_by = random.choice(site_users)
            interaction_type = random.choice(interaction_types)
            timezone = random.choice(timezone_options)
            start_dt, end_dt = generate_datetime_pairs("current")
            
            interaction = Interaction(
                site_id=site.id,
                title=generate_sample_data("title", site_name),
                type=interaction_type,
                lead=generate_sample_data("lead", site_name),
                start_datetime=start_dt,
                end_datetime=end_dt,
                timezone=timezone,
                location=generate_sample_data("location", site_name),
                description=generate_sample_data("description", site_name),
                notes=generate_sample_data("notes", site_name),
                created_by=created_by.id
            )
            
            # Validate before adding
            is_valid, error = interaction.validate()
            if is_valid:
                session.add(interaction)
            else:
                logger.warning(f"Invalid interaction data: {error}")
                
        # Create future interactions
        for i in range(future_count):
            created_by = random.choice(site_users)
            interaction_type = random.choice(interaction_types)
            timezone = random.choice(timezone_options)
            start_dt, end_dt = generate_datetime_pairs("future")
            
            interaction = Interaction(
                site_id=site.id,
                title=generate_sample_data("title", site_name),
                type=interaction_type,
                lead=generate_sample_data("lead", site_name),
                start_datetime=start_dt,
                end_datetime=end_dt,
                timezone=timezone,
                location=generate_sample_data("location", site_name),
                description=generate_sample_data("description", site_name),
                notes=generate_sample_data("notes", site_name),
                created_by=created_by.id
            )
            
            # Validate before adding
            is_valid, error = interaction.validate()
            if is_valid:
                session.add(interaction)
            else:
                logger.warning(f"Invalid interaction data: {error}")
    
    # Commit all interactions
    session.commit()
    logger.info(f"Created interactions for {len(sites)} sites")

def generate_sample_data(data_type, site_name):
    """
    Generate random sample text data for interaction fields.
    
    Args:
        data_type: Type of data to generate (title, description, notes, location, lead)
        site_name: Name of the site to reference in the generated data
        
    Returns:
        str: Generated sample text
    """
    if data_type == "title":
        titles = [
            f"{site_name} Team Meeting",
            f"{site_name} Project Review",
            f"{site_name} Client Consultation",
            f"{site_name} Status Update",
            f"{site_name} Planning Session",
            f"{site_name} Training Workshop",
            f"{site_name} Budget Discussion",
            f"{site_name} Strategy Meeting",
            f"{site_name} Performance Review",
            f"{site_name} Onboarding Session"
        ]
        return random.choice(titles)
    
    elif data_type == "description":
        descriptions = [
            f"Detailed discussion of current projects at {site_name} with team members to align priorities and address blockers.",
            f"Review of quarterly objectives for {site_name} and progress against key metrics.",
            f"Meeting with external clients to discuss requirements and expectations for upcoming work with {site_name}.",
            f"Regular status update covering all active initiatives at {site_name}.",
            f"Planning session to establish roadmap for the next quarter at {site_name}.",
            f"Training session for new tools and processes being implemented at {site_name}.",
            f"Budget review and financial planning discussion for {site_name} operations.",
            f"Strategic alignment session to ensure {site_name} activities support organizational goals.",
            f"Individual performance reviews with team members at {site_name}.",
            f"Onboarding new team members to the {site_name} team and processes."
        ]
        return random.choice(descriptions)
    
    elif data_type == "notes":
        # Sometimes return empty notes
        if random.random() < 0.3:
            return ""
        
        notes = [
            f"Key action items identified. Follow-up meeting scheduled for next week.",
            f"Several decisions made regarding resource allocation for {site_name}.",
            f"Client expressed concerns about timeline. Need to adjust schedule.",
            f"New requirements identified that will impact the project scope.",
            f"Team morale is high. No major concerns raised during the meeting.",
            f"Technical challenges discussed. Research needed for potential solutions.",
            f"Budget constraints may affect project delivery. Escalation needed.",
            f"Great progress reported across all workstreams.",
            f"Training needs identified for several team members.",
            f"Compliance issues discussed. Need to follow up with legal team."
        ]
        return random.choice(notes)
    
    elif data_type == "location":
        locations = [
            f"{site_name} Conference Room A",
            f"{site_name} Conference Room B",
            f"{site_name} Training Room",
            f"{site_name} Executive Office",
            f"{site_name} Open Workspace",
            "Virtual",
            "Microsoft Teams",
            "Zoom",
            f"{site_name} Cafeteria",
            f"{site_name} Innovation Lab"
        ]
        return random.choice(locations)
    
    elif data_type == "lead":
        leads = [
            "John Smith",
            "Emily Johnson",
            "Michael Williams",
            "Jessica Brown",
            "David Jones",
            "Sarah Miller",
            "Robert Davis",
            "Jennifer Garcia",
            "James Wilson",
            "Lisa Martinez"
        ]
        return random.choice(leads)
    
    return ""

def generate_datetime_pairs(timeframe):
    """
    Generate start and end datetime pairs for interactions.
    
    Args:
        timeframe: "past", "current", or "future"
        
    Returns:
        tuple: (start_datetime, end_datetime) pair
    """
    now = datetime.now()
    
    if timeframe == "past":
        # Generate a date 1-90 days in the past
        days_ago = random.randint(1, 90)
        base_date = now - timedelta(days=days_ago)
    elif timeframe == "future":
        # Generate a date 1-90 days in the future
        days_ahead = random.randint(1, 90)
        base_date = now + timedelta(days=days_ahead)
    else:  # "current"
        # Generate a date -7 to +7 days from now
        days_delta = random.randint(-7, 7)
        base_date = now + timedelta(days=days_delta)
    
    # Set a random hour between 8 AM and 6 PM
    hour = random.randint(8, 18)
    minute = random.choice([0, 15, 30, 45])
    
    # Create start datetime
    start_dt = datetime(
        base_date.year, base_date.month, base_date.day,
        hour, minute, 0
    )
    
    # Create end datetime 30 min to 2 hours later
    duration_minutes = random.choice([30, 45, 60, 90, 120])
    end_dt = start_dt + timedelta(minutes=duration_minutes)
    
    # Convert to UTC (the model expects aware datetime objects)
    start_dt = get_utc_datetime(start_dt)
    end_dt = get_utc_datetime(end_dt)
    
    return start_dt, end_dt

def parse_args():
    """
    Parse command line arguments for script options.
    
    Returns:
        argparse.Namespace: Parsed argument namespace
    """
    parser = argparse.ArgumentParser(
        description="Seed the database with initial data for development and testing."
    )
    
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Drop all existing data before seeding"
    )
    
    parser.add_argument(
        "--count",
        type=int,
        default=10,
        help="Number of interactions to create per site (default: 10)"
    )
    
    parser.add_argument(
        "--env",
        choices=["development", "staging", "testing", "production"],
        default="development",
        help="Environment to run in (default: development)"
    )
    
    return parser.parse_args()

def clean_database(session):
    """
    Remove all existing data from the database.
    
    Args:
        session: SQLAlchemy session object
    """
    logger.info("Cleaning database...")
    
    # Delete in order to respect foreign key constraints
    session.execute("DELETE FROM interactions")
    session.execute("DELETE FROM user_sites")
    session.execute("DELETE FROM users")
    session.execute("DELETE FROM sites")
    
    session.commit()
    logger.info("Database cleaned")

def main():
    """
    Main function that orchestrates the database seeding process.
    
    Returns:
        int: Exit code (0 for success, 1 for error)
    """
    # Parse command line arguments
    args = parse_args()
    
    # Configure logging based on environment
    log_level = logging.DEBUG if args.env == "development" else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    logger.info(f"Starting database seeding in {args.env} environment")
    
    try:
        # Create connection manager
        conn_manager = ConnectionManager()
        
        # Get session
        session = conn_manager.get_session()
        
        # Use transaction context for atomic operation
        with conn_manager.transaction_context():
            # Clean database if requested
            if args.clean:
                clean_database(session)
            
            # Create users, sites, and associations
            users = create_users(session)
            sites = create_sites(session)
            associate_users_with_sites(session, users, sites)
            
            # Create interactions
            create_interactions(session, users, sites, args.count)
        
        logger.info(f"Database seeding completed successfully. Created {len(users)} users, {len(sites)} sites, and approximately {args.count * len(sites)} interactions")
        return 0
    
    except Exception as e:
        logger.error(f"Error during database seeding: {str(e)}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())