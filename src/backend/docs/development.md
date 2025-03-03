# Development Guide for Interaction Management System - Backend

This document provides comprehensive development guidelines for the backend of the Interaction Management System. It covers code organization, style guidelines, workflow processes, and best practices to ensure consistent, high-quality code across the project.

## 1. Development Environment

### Prerequisites

Before starting development, ensure your environment is set up according to the [Setup Guide](setup.md). You'll need:

- Python 3.11+
- PostgreSQL 15.3
- Redis 7.0.12
- Git
- IDE with Python support (VSCode, PyCharm, etc.)

### Local Development Setup

Follow these steps to set up your development environment:

1. Clone the repository
2. Create and activate a virtual environment
3. Install dependencies from `requirements.txt`
4. Configure `.env` file using `.env.example` as a template
5. Run database migrations
6. Seed test data if needed

See the [Setup Guide](setup.md) for detailed instructions on each step.

### Development Tools

- **Linting**: pylint, flake8
- **Formatting**: black, isort
- **Type Checking**: mypy
- **Testing**: pytest
- **API Testing**: Postman/Insomnia
- **Database Tools**: pgAdmin, DBeaver

### VS Code Configuration

Recommended VS Code extensions:

- Python
- Pylance
- Python Test Explorer
- GitLens
- Docker
- REST Client

Sample VS Code settings (`settings.json`):

```json
{
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "python.testing.pytestEnabled": true,
  "python.testing.unittestEnabled": false,
  "python.testing.nosetestsEnabled": false,
  "python.testing.pytestArgs": [
    "tests"
  ]
}
```

## 2. Project Structure

The backend follows a layered architecture with clear separation of concerns:

```
src/backend/
├── api/                 # API Layer - Controllers and Routes
│   ├── controllers/     # Controller classes for each resource
│   ├── middleware/      # Request/response middleware
│   ├── schemas/         # Request/response schema definitions
│   ├── helpers/         # API-specific helper functions
│   └── routes.py        # Route definitions
├── services/            # Service Layer - Business Logic
│   ├── auth_service.py  # Authentication service
│   ├── user_service.py  # User management service
│   ├── site_service.py  # Site management service
│   └── interaction_service.py # Interaction management service
├── repositories/        # Data Access Layer
│   ├── base_repository.py # Base repository with common operations
│   ├── user_repository.py # User data access
│   └── interaction_repository.py # Interaction data access
├── models/              # Data Models (SQLAlchemy ORM)
│   ├── base.py          # Base model class
│   ├── user.py          # User model
│   ├── site.py          # Site model
│   └── interaction.py   # Interaction model
├── auth/                # Authentication Components
│   ├── auth0.py         # Auth0 integration
│   ├── token_service.py # JWT token handling
│   └── permission_service.py # Permission checking
├── utils/               # Utilities and Helpers
│   ├── constants.py     # System constants
│   ├── enums.py         # Enumeration definitions
│   ├── datetime_util.py # Date/time utilities
│   └── validation_util.py # Common validation functions
├── cache/               # Caching Layer
│   ├── cache_service.py # Cache service implementation
│   └── invalidation.py  # Cache invalidation strategies
├── logging/             # Logging Components
│   ├── structured_logger.py # Structured logging implementation
│   └── audit_logger.py  # Audit logging functionality
├── security/            # Security Components
│   ├── input_validation.py # Input sanitization and validation
│   └── rate_limiting.py # Rate limiting implementation
├── migrations/          # Database Migrations
│   └── versions/        # Migration version scripts
├── tests/               # Test Suite
│   ├── unit/            # Unit tests
│   ├── integration/     # Integration tests
│   └── fixtures/        # Test fixtures
├── scripts/             # Utility Scripts
│   ├── db_seed.py       # Database seeding
│   └── run_migrations.py # Migration execution
├── docs/                # Documentation
├── config.py            # Configuration management
└── app.py               # Application factory
```

### Layer Responsibilities

#### API Layer
- Handle HTTP requests and responses
- Validate request data using schemas
- Route requests to appropriate services
- Apply middleware (authentication, logging, etc.)
- Format responses according to API contracts

#### Service Layer
- Implement business logic and rules
- Orchestrate operations across repositories
- Enforce permissions and site-scoping
- Manage transactions and data integrity
- Handle complex validation logic

#### Repository Layer
- Abstract database operations
- Implement data access patterns
- Apply site-scoping to queries
- Optimize database queries
- Handle data transformations

#### Model Layer
- Define database schema using SQLAlchemy ORM
- Implement model relationships
- Define data validation constraints
- Provide entity behavior when appropriate

## 3. Coding Standards

### Python Styling

- Follow PEP 8 for general Python styling
- Maximum line length: 100 characters
- Use 4 spaces for indentation (no tabs)
- Use snake_case for variables, functions, and methods
- Use PascalCase for classes and CamelCase for type variables
- Use UPPER_CASE for constants

### Documentation

- Every module should have a docstring explaining its purpose
- All public functions and methods require docstrings
- Use Google-style docstrings format
- Clearly document parameters, return values, and exceptions
- Include examples for complex functions

Example docstring:

```python
def get_interaction_by_id(interaction_id: int, user_id: int) -> Interaction:
    """Retrieves an interaction by ID with site-scoping validation.
    
    Args:
        interaction_id: The ID of the interaction to retrieve
        user_id: The ID of the user requesting the interaction
        
    Returns:
        The Interaction object if found and user has access
        
    Raises:
        NotFoundError: If interaction doesn't exist
        ForbiddenError: If user doesn't have access to the interaction's site
    """
```

### Typing

- Use type hints for all function parameters and return values
- Use typing module for complex types (List, Dict, Optional, etc.)
- Use Union types for parameters that can accept multiple types
- Use TypedDict for dictionary structures with known keys

Example:

```python
from typing import List, Optional, Dict, Any

def search_interactions(
    query: str,
    site_ids: List[int],
    page: int = 1,
    page_size: int = 20,
    filters: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    # Implementation
```

### Error Handling

- Use custom exception classes for domain-specific errors
- Handle exceptions at appropriate levels (usually service layer)
- Provide informative error messages
- Include context in exceptions when helpful
- Don't expose sensitive information in error messages

Example:

```python
try:
    interaction = repo.get_by_id(interaction_id)
    if not interaction:
        raise NotFoundError(f"Interaction with ID {interaction_id} not found")
    if interaction.site_id not in user_site_ids:
        raise ForbiddenError("User does not have access to this interaction's site")
    return interaction
except (DatabaseError, ConnectionError) as e:
    logger.error(f"Database error retrieving interaction {interaction_id}: {str(e)}")
    raise ServiceError("Unable to retrieve interaction data") from e
```

### Logging

- Use the provided structured logger
- Include relevant context in log entries
- Use appropriate log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Don't log sensitive information
- Include request IDs in logs for request tracing

Example:

```python
from logging.structured_logger import get_logger

logger = get_logger(__name__)

def create_interaction(data, user_id):
    logger.info(
        "Creating new interaction", 
        extra={
            "user_id": user_id,
            "site_id": data["site_id"],
            "title": data["title"]
        }
    )
    # Implementation
```

### Security Practices

- Never store sensitive information in code
- Use environment variables for configuration
- Always validate and sanitize user input
- Apply the principle of least privilege
- Always enforce site-scoping on all data access
- Apply proper authorization checks before operations

Example:

```python
# Sanitize and validate user input
data = input_validation.sanitize_interaction_data(request.json)
validation_errors = input_validation.validate_interaction_data(data)
if validation_errors:
    return jsonify({"errors": validation_errors}), 400

# Check authorization
if not permission_service.can_create_interaction(user_id, data["site_id"]):
    return jsonify({"error": "Unauthorized"}), 403

# Proceed with creation
interaction = interaction_service.create_interaction(data, user_id)
```

## 4. Development Workflow

### Git Workflow

We follow a feature branch workflow:

1. Create a feature branch from `develop` branch
   ```bash
   git checkout develop
   git pull
   git checkout -b feature/feature-name
   ```

2. Make your changes, commit frequently with clear messages
   ```bash
   git add .
   git commit -m "feat: Add feature description"
   ```

3. Push your branch to the remote repository
   ```bash
   git push -u origin feature/feature-name
   ```

4. Create a pull request to merge into `develop`
5. After review and approval, merge into `develop`

### Commit Message Format

We follow the Conventional Commits specification:

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

Types:
- `feat`: A new feature
- `fix`: A bug fix
- `docs`: Documentation only changes
- `style`: Changes that don't affect code meaning (formatting, etc.)
- `refactor`: Code change that neither fixes a bug nor adds a feature
- `perf`: Code change that improves performance
- `test`: Adding missing tests or correcting existing tests
- `chore`: Changes to build process or auxiliary tools

Examples:
```
feat(interaction): Add timezone support to interaction dates
fix(auth): Fix token validation for expired tokens
docs(api): Update interaction endpoint documentation
```

### Branching Strategy

- `main`: Production-ready code
- `develop`: Development branch, source for feature branches
- `feature/*`: Feature branches for new development
- `bugfix/*`: Bug fix branches
- `release/*`: Release preparation branches
- `hotfix/*`: Emergency fixes for production

### Code Review Process

1. Code author creates pull request with descriptive title and details
2. CI/CD pipeline runs automated tests and checks
3. At least one team member reviews the code
4. Reviewers provide feedback directly in the PR
5. Author addresses feedback with new commits
6. After approval and passing tests, code is merged

#### Code Review Checklist

- Code follows project style guidelines
- Appropriate test coverage for new code
- Documentation is updated
- No security vulnerabilities
- Site-scoping is properly implemented
- Error handling is comprehensive
- Performance considerations addressed

### Testing Requirements

- Write unit tests for all new functionality
- Ensure tests are independent and repeatable
- Run tests locally before pushing changes
- Maintain minimum 90% code coverage
- Include integration tests for API endpoints

See [Testing Guide](testing.md) for detailed testing guidance.

## 5. Implementing Key Features

### Authentication and Authorization

All endpoints requiring authentication should:

1. Use the `@require_auth` decorator
2. Pass through the `auth_middleware`
3. Validate user site access for site-specific operations

Example:

```python
@interaction_blueprint.route("/<int:interaction_id>", methods=["GET"])
@require_auth
def get_interaction(interaction_id):
    # Current user and site info extracted from JWT by middleware
    user_id = g.user_id
    site_ids = g.site_ids
    
    try:
        interaction = interaction_service.get_interaction(interaction_id, user_id, site_ids)
        return jsonify(interaction), 200
    except NotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except ForbiddenError as e:
        return jsonify({"error": str(e)}), 403
```

### Site-Scoping Implementation

Site-scoping must be implemented at multiple layers:

1. **Controller Layer**: Extract site context from JWT token
2. **Service Layer**: Pass site IDs to repositories, verify site access
3. **Repository Layer**: Include site filtering in all queries

Example service method:

```python
def get_interaction(self, interaction_id, user_id, site_ids):
    """Get an interaction with site-scoping check."""
    interaction = self.interaction_repo.find_by_id(interaction_id)
    
    if not interaction:
        raise NotFoundError(f"Interaction with ID {interaction_id} not found")
        
    # Site-scoping check
    if interaction.site_id not in site_ids:
        self.audit_logger.log_unauthorized_access(
            user_id=user_id,
            resource="interaction",
            resource_id=interaction_id
        )
        raise ForbiddenError("You do not have access to this interaction")
        
    return interaction
```

Example repository method:

```python
def find_all_by_site_ids(self, site_ids, page=1, page_size=20, **filters):
    """Find all interactions for the specified sites with filtering."""
    query = self.session.query(Interaction).filter(Interaction.site_id.in_(site_ids))
    
    # Apply additional filters
    for key, value in filters.items():
        if hasattr(Interaction, key) and value is not None:
            query = query.filter(getattr(Interaction, key) == value)
    
    # Pagination
    total = query.count()
    offset = (page - 1) * page_size
    interactions = query.order_by(Interaction.created_at.desc()).offset(offset).limit(page_size).all()
    
    return interactions, total
```

### Implementing Search Functionality

Search implementation should support:

1. Text search across multiple fields
2. Field-specific filtering
3. Pagination of results
4. Site-scoped access control

Example search service:

```python
def search_interactions(self, query, site_ids, page=1, page_size=20, **filters):
    """Search interactions with text query and filtering."""
    # Always apply site-scoping
    if not site_ids:
        return [], 0
        
    # Build search expression
    search_fields = [
        Interaction.title,
        Interaction.description,
        Interaction.notes,
        Interaction.lead,
        Interaction.location
    ]
    
    search_conditions = []
    if query:
        for field in search_fields:
            search_conditions.append(field.ilike(f"%{query}%"))
            
    # Combine with OR for any field match
    if search_conditions:
        search_filter = or_(*search_conditions)
        results, total = self.interaction_repo.search(
            site_ids=site_ids,
            search_filter=search_filter,
            page=page,
            page_size=page_size,
            **filters
        )
    else:
        # No search term, just use site and other filters
        results, total = self.interaction_repo.find_all_by_site_ids(
            site_ids=site_ids,
            page=page,
            page_size=page_size,
            **filters
        )
        
    return results, total
```

### Caching Strategy

Use the cache service for:

1. Frequently accessed, relatively static data
2. Expensive computations or database queries
3. Short-term storage of repeated API requests

Example cache usage:

```python
def get_user_sites(self, user_id):
    """Get sites associated with a user, with caching."""
    cache_key = f"user:{user_id}:sites"
    
    # Try to get from cache first
    cached_sites = self.cache_service.get(cache_key)
    if cached_sites is not None:
        return cached_sites
        
    # Not in cache, query database
    sites = self.user_site_repo.get_sites_for_user(user_id)
    
    # Store in cache for future requests (expire after 30 minutes)
    self.cache_service.set(cache_key, sites, expire=1800)
    
    return sites
```

### Implementing Validation

Validation should be implemented at multiple levels:

1. **Schema Validation**: Validate request data structure
2. **Business Rule Validation**: Validate domain rules
3. **Database Constraints**: Enforce data integrity

Example validation in service:

```python
def create_interaction(self, data, user_id):
    """Create a new interaction with validation."""
    # Validate required fields
    required_fields = ["title", "type", "lead", "start_datetime", "end_datetime", "timezone", "site_id", "description"]
    for field in required_fields:
        if field not in data or not data[field]:
            raise ValidationError(f"Field '{field}' is required")
    
    # Validate field lengths
    if len(data["title"]) < 5 or len(data["title"]) > 100:
        raise ValidationError("Title must be between 5 and 100 characters")
    
    # Validate dates
    start_dt = datetime.fromisoformat(data["start_datetime"])
    end_dt = datetime.fromisoformat(data["end_datetime"])
    if end_dt <= start_dt:
        raise ValidationError("End date must be after start date")
    
    # Check site access permission
    if not self.site_service.user_has_site_access(user_id, data["site_id"]):
        raise ForbiddenError("User does not have access to the specified site")
    
    # Create the interaction
    interaction = self.interaction_repo.create({
        **data,
        "created_by": user_id
    })
    
    # Log audit trail
    self.audit_logger.log_interaction_created(interaction.id, user_id)
    
    return interaction
```

## 6. API Design Principles

### RESTful Endpoint Design

Follow these principles for RESTful API design:

1. Use resource-based URLs (nouns, not verbs)
2. Use HTTP methods appropriately:
   - GET: Retrieve resources
   - POST: Create resources
   - PUT: Update resources
   - DELETE: Remove resources
3. Use HTTP status codes correctly
4. Support pagination for collection endpoints
5. Use snake_case for JSON field names
6. Version the API with /api/v1/... prefix

Example endpoint structure:

```
# Resource collection
GET /api/interactions            # List interactions
POST /api/interactions           # Create interaction

# Specific resource
GET /api/interactions/{id}       # Get interaction
PUT /api/interactions/{id}       # Update interaction
DELETE /api/interactions/{id}    # Delete interaction

# Resource relations
GET /api/sites/{id}/interactions # Get site's interactions

# Search
GET /api/search/interactions?q=term  # Search interactions
```

### API Response Format

Use consistent response formats:

1. For single resources:

```json
{
  "id": 123,
  "title": "Project Kickoff",
  "type": "MEETING",
  ... other fields ...
}
```

2. For collections with pagination:

```json
{
  "interactions": [
    { ... interaction 1 ... },
    { ... interaction 2 ... }
  ],
  "total": 57,
  "page": 1,
  "page_size": 20,
  "total_pages": 3
}
```

3. For errors:

```json
{
  "error": {
    "code": "validation_error",
    "message": "Validation failed",
    "details": {
      "title": "Title is required",
      "start_datetime": "Invalid date format"
    }
  }
}
```

### HTTP Status Codes

Use appropriate status codes:

- 200 OK: Successful request (GET, PUT)
- 201 Created: Resource created (POST)
- 204 No Content: Successful request with no response body (DELETE)
- 400 Bad Request: Invalid input
- 401 Unauthorized: Authentication required
- 403 Forbidden: Insufficient permissions
- 404 Not Found: Resource not found
- 422 Unprocessable Entity: Semantic validation errors
- 429 Too Many Requests: Rate limit exceeded
- 500 Internal Server Error: Server-side error

### Pagination

Implement pagination using query parameters:

```
GET /api/interactions?page=2&page_size=20
```

Default values:
- page: 1
- page_size: 20 (max 100)

Include pagination metadata in responses (as shown in the response format section).

## 7. Database Practices

### SQLAlchemy ORM Usage

Use SQLAlchemy ORM effectively:

1. Define models with clear relationships
2. Use appropriate column types
3. Include constraints and indexes
4. Define cascading behavior for relationships
5. Use hybrid properties for computed fields
6. Implement model methods for entity behavior

Example model definition:

```python
class Interaction(Base):
    __tablename__ = "interactions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    site_id = Column(Integer, ForeignKey("sites.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(100), nullable=False)
    type = Column(String(50), nullable=False)
    lead = Column(String(100), nullable=False)
    start_datetime = Column(DateTime, nullable=False, index=True)
    end_datetime = Column(DateTime, nullable=False)
    timezone = Column(String(50), nullable=False)
    location = Column(String(200))
    description = Column(Text, nullable=False)
    notes = Column(Text)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    site = relationship("Site", back_populates="interactions")
    creator = relationship("User")
    history = relationship("InteractionHistory", back_populates="interaction", cascade="all, delete-orphan")
    
    # Hybrid properties
    @hybrid_property
    def duration_minutes(self):
        """Calculate the interaction duration in minutes."""
        if self.start_datetime and self.end_datetime:
            delta = self.end_datetime - self.start_datetime
            return int(delta.total_seconds() / 60)
        return 0
```

### Query Optimization

Optimize database queries for performance:

1. Use appropriate indexes
2. Limit results and paginate
3. Use eager loading for relationships (joinedload, selectinload)
4. Optimize query conditions
5. Use compiled queries for repeated operations

Example optimized query:

```python
def find_interactions_with_filters(self, site_ids, page=1, page_size=20, **filters):
    """Find interactions with optimized queries."""
    # Base query with site filtering
    query = self.session.query(Interaction).filter(Interaction.site_id.in_(site_ids))
    
    # Apply type filter efficiently
    if "type" in filters and filters["type"]:
        query = query.filter(Interaction.type == filters["type"])
    
    # Apply date range filter efficiently
    if "start_date" in filters and filters["start_date"]:
        query = query.filter(Interaction.start_datetime >= filters["start_date"])
    if "end_date" in filters and filters["end_date"]:
        query = query.filter(Interaction.start_datetime <= filters["end_date"])
    
    # Get total count efficiently
    total_query = query.with_entities(func.count())
    total = total_query.scalar()
    
    # Apply sorting and pagination
    query = query.order_by(Interaction.start_datetime.desc())
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    
    # Eager load relationships to avoid N+1 queries
    query = query.options(
        joinedload(Interaction.site),
        joinedload(Interaction.creator)
    )
    
    return query.all(), total
```

### Transaction Management

Use transactions for multi-step operations:

```python
def update_interaction_with_history(self, interaction_id, data, user_id):
    """Update interaction with audit history in a transaction."""
    try:
        # Start transaction
        with self.session.begin():
            # Get existing interaction
            interaction = self.session.query(Interaction).get(interaction_id)
            if not interaction:
                raise NotFoundError(f"Interaction {interaction_id} not found")
            
            # Store original state for history
            original_state = interaction.to_dict()
            
            # Update fields
            for key, value in data.items():
                if hasattr(interaction, key) and key not in ["id", "created_at", "created_by"]:
                    setattr(interaction, key, value)
            
            # Create history record
            history_entry = InteractionHistory(
                interaction_id=interaction_id,
                changed_by=user_id,
                change_type="UPDATE",
                before_state=original_state,
                after_state=interaction.to_dict()
            )
            self.session.add(history_entry)
            
            # Transaction will be committed automatically if no exceptions
            return interaction
            
    except SQLAlchemyError as e:
        # Transaction will be rolled back on exception
        self.logger.error(f"Database error updating interaction {interaction_id}: {str(e)}")
        raise RepositoryError("Failed to update interaction") from e
```

### Migrations

Use Alembic for database migrations:

1. Create migrations for all schema changes
2. Test migrations before applying to production
3. Include both upgrade and downgrade paths
4. Use transaction blocks in migrations
5. Add clear comments explaining changes

Example migration script:

```python
"""Add timezone field to interactions table

Revision ID: a1b2c3d4e5f6
Revises: 9z8y7x6w5v4
Create Date: 2023-06-15 09:12:34.567890
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = 'a1b2c3d4e5f6'
down_revision = '9z8y7x6w5v4'

def upgrade():
    # Transaction block
    with op.batch_alter_table('interactions') as batch_op:
        # Add timezone column with a default value
        batch_op.add_column(sa.Column('timezone', sa.String(50), nullable=False, server_default='UTC'))
        # Remove server default after adding
        batch_op.alter_column('timezone', server_default=None)

def downgrade():
    # Transaction block
    with op.batch_alter_table('interactions') as batch_op:
        # Remove timezone column
        batch_op.drop_column('timezone')
```

## 8. Security Guidelines

### Input Validation and Sanitization

Implement thorough input validation and sanitization:

1. Validate request data against schemas
2. Sanitize user input to prevent injection attacks
3. Use parameterized queries to prevent SQL injection
4. Escape output to prevent XSS attacks
5. Validate file uploads thoroughly

Example input validation:

```python
def sanitize_and_validate_interaction(data):
    """Sanitize and validate interaction data."""
    # Sanitize string inputs
    for field in ["title", "lead", "location", "description", "notes"]:
        if field in data and data[field]:
            data[field] = bleach.clean(data[field], strip=True)
    
    # Validate schema
    schema = InteractionSchema()
    try:
        validated_data = schema.load(data)
    except ValidationError as e:
        raise InputValidationError(str(e.messages))
    
    # Validate business rules
    start_dt = validated_data.get("start_datetime")
    end_dt = validated_data.get("end_datetime")
    if start_dt and end_dt and end_dt <= start_dt:
        raise InputValidationError({"end_datetime": ["End time must be after start time"]})
    
    return validated_data
```

### Authentication and Authorization

Implement secure authentication and authorization:

1. Use Auth0 for authentication
2. Validate JWT tokens on every request
3. Enforce site-scoping on all data access
4. Implement role-based access control where needed
5. Use appropriate HTTP-only cookies for tokens
6. Apply the principle of least privilege

Example token validation:

```python
def validate_token(token):
    """Validate JWT token and extract claims."""
    try:
        # Get Auth0 configuration
        auth0_domain = auth0_config["domain"]
        api_audience = auth0_config["audience"]
        algorithms = auth0_config["algorithms"]
        
        # Get the public key from Auth0
        jwks_url = f'https://{auth0_domain}/.well-known/jwks.json'
        jwks_client = jwt.PyJWKClient(jwks_url)
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        
        # Decode and validate the token
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=algorithms,
            audience=api_audience,
            issuer=f'https://{auth0_domain}/'
        )
        
        return payload
    except jwt.ExpiredSignatureError:
        raise AuthError("Token has expired", 401)
    except jwt.InvalidTokenError as e:
        raise AuthError(f"Invalid token: {str(e)}", 401)
```

### Rate Limiting

Implement API rate limiting to prevent abuse:

```python
from flask import request, g
import time
import redis

redis_client = redis.Redis.from_url(config.REDIS_URL)

def rate_limit_middleware():
    """Rate limiting middleware."""
    # Get client identifier (IP or user ID if authenticated)
    client_id = g.user_id if hasattr(g, 'user_id') else request.remote_addr
    
    # Get endpoint-specific rate limit
    endpoint = request.endpoint
    if 'auth' in endpoint:
        # Stricter limits for authentication endpoints
        max_requests = config.RATE_LIMIT_AUTH
    elif 'search' in endpoint:
        # Moderate limits for search endpoints
        max_requests = config.RATE_LIMIT_SEARCH
    else:
        # Default limit for other endpoints
        max_requests = config.RATE_LIMIT_DEFAULT
    
    # Redis key for rate limiting
    key = f"rate_limit:{client_id}:{endpoint}"
    current = redis_client.get(key)
    
    if current and int(current) > max_requests:
        # Rate limit exceeded
        # Set headers as per RFC 6585
        response = jsonify({
            "error": "Too many requests",
            "message": "Rate limit exceeded. Please try again later."
        })
        response.status_code = 429
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(max_requests)
        response.headers["X-RateLimit-Remaining"] = "0"
        response.headers["X-RateLimit-Reset"] = str(int(time.time()) + 60)
        response.headers["Retry-After"] = "60"  # Try again after 1 minute
        
        return response
    
    # Increment request count (expire after 1 minute)
    pipe = redis_client.pipeline()
    pipe.incr(key)
    pipe.expire(key, 60)  # 1 minute window
    pipe.execute()
    
    # Continue request processing
    return None
```

### Data Protection

Protect sensitive data:

1. Use HTTPS for all communications
2. Store sensitive data in encrypted form
3. Apply field-level access control
4. Sanitize logs to remove sensitive data
5. Implement proper data retention policies

Example of sensitive data handling:

```python
# Sanitized logging
def log_user_activity(user_id, action, resource_id=None):
    """Log user activity without sensitive data."""
    log_data = {
        "user_id": user_id,  # Log user ID, not name/email
        "action": action,
        "timestamp": datetime.utcnow().isoformat(),
        "ip_address": _mask_ip_address(request.remote_addr)  # Partially mask IP
    }
    
    if resource_id:
        log_data["resource_id"] = resource_id
    
    logger.info("User activity", extra=log_data)

# Mask IP address for privacy
def _mask_ip_address(ip):
    """Mask the last octet of an IPv4 address or equivalent for IPv6."""
    if not ip or ip == "127.0.0.1":
        return "localhost"
        
    if ":" in ip:  # IPv6
        return ip.rsplit(":", 1)[0] + ":xxxx"
    else:  # IPv4
        return ip.rsplit(".", 1)[0] + ".xxx"
```

## 9. Performance Optimization

### Caching Strategies

Implement effective caching:

1. Use Redis for caching frequently accessed data
2. Apply appropriate TTL for different data types
3. Implement cache invalidation strategies
4. Use cache for expensive computations
5. Consider caching HTTP responses

Example caching implementation:

```python
class CacheService:
    """Service for caching data in Redis."""
    
    def __init__(self, redis_client):
        self.redis_client = redis_client
    
    def get(self, key):
        """Get data from cache."""
        data = self.redis_client.get(f"cache:{key}")
        if data:
            return json.loads(data)
        return None
    
    def set(self, key, value, expire=300):
        """Store data in cache with expiration time."""
        if value is not None:
            self.redis_client.setex(
                f"cache:{key}",
                expire,  # TTL in seconds
                json.dumps(value)
            )
    
    def delete(self, key):
        """Delete data from cache."""
        self.redis_client.delete(f"cache:{key}")
    
    def delete_pattern(self, pattern):
        """Delete multiple keys matching a pattern."""
        keys = self.redis_client.keys(f"cache:{pattern}*")
        if keys:
            self.redis_client.delete(*keys)
```

Example cache usage with invalidation:

```python
def get_interaction(self, interaction_id, user_id, site_ids):
    """Get interaction with caching."""
    cache_key = f"interaction:{interaction_id}"
    
    # Try to get from cache
    cached_data = self.cache_service.get(cache_key)
    if cached_data:
        # Verify site access before returning cached data
        if cached_data["site_id"] in site_ids:
            return cached_data
    
    # Not in cache or site access changed, get from database
    interaction = self.interaction_repo.find_by_id(interaction_id)
    
    if not interaction:
        raise NotFoundError(f"Interaction {interaction_id} not found")
    
    # Verify site access
    if interaction.site_id not in site_ids:
        raise ForbiddenError("You do not have access to this interaction")
    
    # Convert to dict for caching
    interaction_data = interaction.to_dict()
    
    # Cache for 10 minutes
    self.cache_service.set(cache_key, interaction_data, expire=600)
    
    return interaction_data

def update_interaction(self, interaction_id, data, user_id, site_ids):
    """Update interaction with cache invalidation."""
    # Verify site access and update interaction
    interaction = self.interaction_repo.update(interaction_id, data, site_ids)
    
    # Invalidate cache
    self.cache_service.delete(f"interaction:{interaction_id}")
    
    # Invalidate related caches
    self.cache_service.delete_pattern(f"interactions:site:{interaction.site_id}")
    self.cache_service.delete_pattern("search:interactions")
    
    return interaction
```

### Database Optimization

Optimize database operations:

1. Use appropriate indexes for frequent queries
2. Implement database connection pooling
3. Optimize query patterns for performance
4. Batch operations where appropriate
5. Implement pagination for large datasets

Example optimized repository:

```python
class InteractionRepository:
    """Repository for interaction data with optimizations."""
    
    def __init__(self, session=None):
        self.session = session or db.session
    
    def find_by_id(self, interaction_id):
        """Find interaction by ID with optimized query."""
        return self.session.query(Interaction).get(interaction_id)
    
    def find_all_by_site_ids(self, site_ids, page=1, page_size=20, **filters):
        """Find interactions with optimized query and pagination."""
        # Start with a query builder
        query = self.session.query(Interaction).filter(Interaction.site_id.in_(site_ids))
        
        # Apply filters
        if filters.get("type"):
            query = query.filter(Interaction.type == filters["type"])
        
        if filters.get("start_date"):
            query = query.filter(Interaction.start_datetime >= filters["start_date"])
        
        if filters.get("end_date"):
            query = query.filter(Interaction.start_datetime <= filters["end_date"])
        
        if filters.get("lead"):
            query = query.filter(Interaction.lead.ilike(f"%{filters['lead']}%"))
        
        # Count total (use optimized count query)
        total = query.with_entities(func.count(Interaction.id)).scalar()
        
        # Apply sorting and pagination
        offset = (page - 1) * page_size
        query = query.order_by(Interaction.start_datetime.desc())
        query = query.offset(offset).limit(page_size)
        
        # Execute query and return results
        interactions = query.all()
        
        return interactions, total
    
    def bulk_create(self, interactions_data):
        """Bulk create interactions for performance."""
        interactions = [Interaction(**data) for data in interactions_data]
        self.session.bulk_save_objects(interactions)
        self.session.commit()
        return True
```

### Async Task Processing

Use asynchronous processing for long-running tasks:

```python
from redis import Redis
from rq import Queue

# Configure Redis Queue
redis_conn = Redis.from_url(config.REDIS_URL)
background_queue = Queue('background_tasks', connection=redis_conn)

def generate_interactions_report(self, site_id, filters, user_id):
    """Generate report asynchronously."""
    # Enqueue background task
    job = background_queue.enqueue(
        'tasks.reports.generate_interactions_report',
        site_id=site_id,
        filters=filters,
        user_id=user_id,
        job_timeout=300  # 5 minutes
    )
    
    # Return job ID for status checking
    return {
        "job_id": job.id,
        "status": "queued",
        "estimated_completion": "Your report will be ready in approximately 1-2 minutes"
    }
```

## 10. Documentation

### Code Documentation

Write comprehensive code documentation:

1. Use docstrings for modules, classes, and functions
2. Follow Google-style docstring format
3. Include type hints for all function parameters
4. Document raised exceptions
5. Add examples for complex functionality

Example docstring:

```python
def search_interactions(
    query: str,
    site_ids: List[int],
    page: int = 1,
    page_size: int = 20,
    **filters: Dict[str, Any]
) -> Tuple[List[Interaction], int]:
    """Search for interactions matching criteria within authorized sites.
    
    This function searches across interaction fields including title,
    description, lead, and location. Results are filtered by the user's
    authorized sites and any additional filters provided.
    
    Args:
        query: Search text to match against interaction fields
        site_ids: List of site IDs the user has access to
        page: Page number for pagination (1-based)
        page_size: Number of results per page
        **filters: Additional filters to apply (type, start_date, etc.)
    
    Returns:
        Tuple containing:
            - List of Interaction objects matching the criteria
            - Total count of matching interactions (before pagination)
    
    Raises:
        ValidationError: If search parameters are invalid
        RepositoryError: If a database error occurs
        
    Example:
        >>> search_interactions("Project", [1, 2], type="MEETING")
        ([<Interaction 1>, <Interaction 2>], 2)
    """
```

### API Documentation

Maintain comprehensive API documentation:

1. Document all API endpoints
2. Include request and response formats
3. List possible status codes
4. Provide examples
5. Document authentication requirements

Use OpenAPI/Swagger for interactive documentation:

```python
from flask_swagger_ui import get_swaggerui_blueprint

# Configure Swagger UI
SWAGGER_URL = '/api/docs'
API_URL = '/static/swagger.json'

swagger_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        'app_name': "Interaction Management API"
    }
)
app.register_blueprint(swagger_blueprint, url_prefix=SWAGGER_URL)

# Generate OpenAPI spec
with app.test_request_context():
    spec = generate_api_spec(app, title="Interaction Management API", version="1.0.0")
    with open('static/swagger.json', 'w') as f:
        json.dump(spec, f)
```

### Repository Documentation

Maintain up-to-date repository documentation:

1. README with project overview and setup instructions
2. Development guide (this document)
3. API documentation
4. Testing guide
5. Deployment guide

Ensure documentation is:
- Current and accurate
- Easy to understand
- Complete with examples
- Organized logically
- Accessible to all team members

## 11. Troubleshooting

### Debugging Strategies

Use effective debugging strategies:

1. Enable Flask debug mode during development
2. Use proper logging at appropriate levels
3. Add debug logging for complex operations
4. Use Python debugger (pdb) for deep issues
5. Trace request context through the system

Example debug configuration:

```python
# Configure detailed logging for development
if app.config['DEBUG']:
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        handlers=[
            logging.StreamHandler()
        ]
    )
    # Enable SQLAlchemy query logging
    logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
```

Example debugging with pdb:

```python
def debug_interaction_issue(interaction_id):
    """Debug function for interaction issues."""
    # Get interaction with all relationships loaded
    interaction = db.session.query(Interaction).options(
        joinedload(Interaction.site),
        joinedload(Interaction.creator)
    ).get(interaction_id)
    
    if not interaction:
        print(f"Interaction {interaction_id} not found")
        return
    
    # Start interactive debugger
    import pdb; pdb.set_trace()
    
    # Inspect interaction details
    print(f"Interaction: {interaction.title}")
    print(f"Site: {interaction.site.name if interaction.site else 'None'}")
    print(f"Creator: {interaction.creator.username if interaction.creator else 'None'}")
    
    # Diagnostic SQL query
    raw_sql = f"""
    SELECT i.id, i.title, i.site_id, s.name as site_name, u.username as creator
    FROM interactions i
    LEFT JOIN sites s ON i.site_id = s.id
    LEFT JOIN users u ON i.created_by = u.id
    WHERE i.id = {interaction_id}
    """
    
    result = db.engine.execute(raw_sql).fetchone()
    print(f"Raw SQL result: {dict(result) if result else 'None'}")
```

### Common Issues and Solutions

Address common development issues:

#### Database Connection Issues

**Issue**: Unable to connect to the database

**Solutions**:
- Verify PostgreSQL is running: `pg_isready`
- Check database connection string in `.env`
- Ensure database exists and permissions are correct
- Verify network connectivity to database

#### Migration Problems

**Issue**: Migration errors or conflicts

**Solutions**:
- Check migration version history: `alembic history`
- Identify current version: `alembic current`
- Reset to a specific version: `alembic downgrade <revision>`
- Create a clean migration for current models

#### Authentication Problems

**Issue**: Auth0 authentication failures

**Solutions**:
- Verify Auth0 configuration in `.env`
- Check Auth0 tenant status and logs
- Validate client ID and client secret
- Ensure correct Auth0 API Audience is set
- Check CORS settings for local development

#### Site-Scoping Issues

**Issue**: Users can't access or update interactions

**Solutions**:
- Verify user-site associations in the database
- Check site ID is included in JWT token claims
- Confirm repository queries include site filtering
- Review authorization middleware implementation
- Enable debug logging for site context service

#### Performance Problems

**Issue**: Slow API responses

**Solutions**:
- Enable query logging to identify slow queries
- Check for missing database indexes
- Implement caching for frequent operations
- Review N+1 query patterns and optimize with eager loading
- Use database query profiling tools

## 12. Resources

### Internal Documentation

- [Setup Guide](setup.md): Environment setup instructions
- [API Documentation](api.md): Comprehensive API reference
- [Testing Guide](testing.md): Testing strategies and practices
- [Deployment Guide](deployment.md): Deployment processes and environments

### Style Guides

- [PEP 8](https://pep8.org/): Python style guide
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- [Flask Best Practices](https://flask.palletsprojects.com/en/2.3.x/patterns/)

### Technical Documentation

- [Flask Documentation](https://flask.palletsprojects.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Auth0 Documentation](https://auth0.com/docs/)
- [Redis Documentation](https://redis.io/documentation)
- [JWT Documentation](https://pyjwt.readthedocs.io/)

### Learning Resources

- [Flask Mega-Tutorial](https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-i-hello-world)
- [SQLAlchemy ORM Tutorial](https://docs.sqlalchemy.org/en/20/orm/tutorial.html)
- [Effective Python](https://effectivepython.com/): Book on Python best practices
- [RESTful API Design](https://restfulapi.net/): Guide to RESTful API design

### Tools and Utilities

- [Postman](https://www.postman.com/): API testing tool
- [PgAdmin](https://www.pgadmin.org/): PostgreSQL administration tool
- [Redis Commander](https://github.com/joeferner/redis-commander): Redis management UI
- [JWT.io](https://jwt.io/): JWT inspection and debugging tool