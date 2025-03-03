# Interaction Management System - Backend

The backend component of the Interaction Management System provides a RESTful API for managing and searching interaction records with site-scoped access control. Built with Flask, SQLAlchemy, and PostgreSQL, it implements secure authentication via Auth0 and leverages Redis for caching.

## Features

- **Authentication**: Secure JWT-based authentication integrated with Auth0
- **Site-scoped Access Control**: Data isolation between organizational sites
- **Interaction Management**: Complete CRUD operations for interaction records
- **Advanced Search**: High-performance search capabilities across all interaction fields
- **Multi-environment Support**: Configurations for development, staging, and production
- **Container-ready**: Docker support for consistent deployment across environments
- **API Documentation**: Auto-generated OpenAPI specification and Swagger UI

## Tech Stack

- **Framework**: Flask 2.3.2
- **ORM**: SQLAlchemy 2.0.19
- **Database**: PostgreSQL 15.3
- **Authentication**: Flask-JWT-Extended 4.5.2, Auth0
- **Caching**: Redis 7.0.12
- **Migration**: Alembic 1.11.1
- **API Documentation**: apispec 6.3.0
- **Testing**: pytest 7.4.0
- **Containerization**: Docker

## Project Structure

```
src/backend/
├── api/                # API controllers, routes, and schemas
│   ├── controllers/    # Controller endpoints by domain
│   ├── helpers/        # API utility functions
│   ├── middleware/     # Request processing middleware
│   ├── schemas/        # Request/response schema validation
│   └── routes.py       # Route registration
├── auth/               # Authentication and authorization services
├── cache/              # Caching implementation
├── docs/               # Additional documentation
├── logging/            # Logging configuration
├── migrations/         # Database migration scripts
├── models/             # SQLAlchemy data models
├── repositories/       # Data access layer
├── scripts/            # Utility scripts
├── security/           # Security implementation
├── services/           # Business logic layer
├── tests/              # Test suites and fixtures
├── utils/              # Utility functions and helpers
├── .env.example        # Environment variable template
├── .flaskenv           # Flask configuration
├── app.py              # Application factory
├── config.py           # Configuration settings
├── Dockerfile          # Container definition
├── extensions.py       # Flask extensions initialization
├── gunicorn.conf.py    # Production server config
├── requirements.txt    # Python dependencies
└── wsgi.py             # WSGI entry point
```

## Getting Started

### Prerequisites

- Python 3.11+
- PostgreSQL 15.3+
- Redis 7.0+
- Auth0 account (for authentication)

### Quick Start

1. Clone the repository
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   cd src/backend
   pip install -r requirements.txt
   ```
4. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```
5. Run database migrations:
   ```bash
   python -m scripts.run_migrations
   ```
6. Start the development server:
   ```bash
   flask run
   ```

For detailed setup instructions, see [docs/setup.md](docs/setup.md)

## Docker Setup

To run the backend using Docker:

1. Ensure Docker and Docker Compose are installed
2. Configure environment variables in `.env` file
3. Build and start the containers:
   ```bash
   # From the project root
   docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
   ```
4. Access the API at http://localhost:5000

See [docs/setup.md](docs/setup.md) for additional Docker commands and configurations.

## Database

### Models

The system uses the following core data models:

- **User**: User accounts with authentication information
- **Site**: Organizational sites that contain interactions
- **UserSite**: Junction table for user-site relationships
- **Interaction**: Core interaction records with all communication details
- **InteractionHistory**: Audit trail for interaction changes

### Migrations

Database migrations use Alembic:

```bash
# Create a new migration after model changes
python -m scripts.create_migration "description_of_changes"

# Apply pending migrations
python -m scripts.run_migrations
```

## API Documentation

The API documentation is available at:

- http://localhost:5000/api/docs (JSON specification)
- http://localhost:5000/api/docs/ui (Swagger UI)

The API follows RESTful principles and includes these main endpoints:

- `/api/v1/auth/*`: Authentication operations
- `/api/v1/users/*`: User management
- `/api/v1/sites/*`: Site management and user-site associations
- `/api/v1/interactions/*`: Interaction CRUD operations
- `/api/v1/search/*`: Advanced search functionality

For detailed API specifications, see [docs/api.md](docs/api.md)

## Authentication

This application uses Auth0 for authentication:

1. Users log in via Auth0 through the frontend
2. JWT tokens are issued containing user identity and site access information
3. Backend validates tokens and enforces site-scoped access control
4. Token refresh is handled via refresh tokens

To configure Auth0:

1. Create an Auth0 account and tenant
2. Configure an API and application
3. Set Auth0 environment variables in `.env`

See [docs/setup.md](docs/setup.md) for detailed Auth0 configuration steps.

## Development

### Code Style

This project follows PEP 8 guidelines with these tools:

- `black` for code formatting
- `flake8` for linting

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/backend

# Run specific test file or pattern
pytest tests/unit/test_interaction_service.py
pytest -k "create or update"
```

### Local Development Workflow

1. Create a new branch for your feature/fix
2. Make changes and write tests
3. Run tests and linting
4. Commit with descriptive message
5. Push and create a pull request

See [docs/development.md](docs/development.md) for coding standards and workflow details.

## Environment Configuration

The application uses different configuration sets based on the environment:

- **Development**: Local development with debug features enabled
- **Staging**: Pre-production environment for testing
- **Production**: Live environment with optimized settings
- **Testing**: For automated tests

Configuration is loaded from multiple sources in this order:

1. Default values in `config.py`
2. Environment variables
3. `.env` file values

Key environment variables are documented in `.env.example`.

## Deployment

The application is designed for deployment using Docker containers:

1. Build the Docker image with production settings
2. Deploy to the target environment (AWS ECS recommended)
3. Ensure database migrations are applied
4. Configure environment variables for the production environment

See [docs/deployment.md](docs/deployment.md) for detailed deployment instructions.

## Troubleshooting

### Common Issues

#### Database Connection Errors
- Verify PostgreSQL is running: `pg_isready`
- Check credentials in `.env` file
- Ensure the database exists: `psql -U postgres -l`

#### Auth0 Configuration Issues
- Verify Auth0 credentials in `.env` file
- Ensure the API and Application are properly configured
- Check CORS settings for local development

#### Docker Issues
- Check Docker logs: `docker-compose logs -f`
- Rebuild containers: `docker-compose build --no-cache`
- Verify port availability: `netstat -tuln`

For more troubleshooting information, see [docs/setup.md](docs/setup.md)

## Documentation

Detailed documentation is available in the `docs/` directory:

- [setup.md](docs/setup.md): Environment setup and configuration
- [api.md](docs/api.md): API endpoints and usage
- [development.md](docs/development.md): Development guidelines and practices
- [testing.md](docs/testing.md): Test organization and execution
- [deployment.md](docs/deployment.md): Deployment procedures

## License

Copyright © 2023 Interaction Management System

All rights reserved. This software and associated documentation are proprietary and confidential.