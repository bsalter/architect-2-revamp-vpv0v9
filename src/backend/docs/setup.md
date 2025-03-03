# Setup Guide for Interaction Management System - Backend

This document provides comprehensive instructions for setting up the backend environment for the Interaction Management System. Follow these steps to configure your local development environment, containerized development setup, and prepare for deployment.

## Prerequisites

Before beginning setup, ensure you have the following installed:

- Python 3.11 or higher
- pip (Python package manager)
- PostgreSQL 15.3
- Redis 7.0.12
- Docker and Docker Compose (for containerized development)
- Git

You will also need:
- An Auth0 account for authentication services
- Access to the project repository

## Local Development Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd interaction-management-system
```

### 2. Create a Virtual Environment

```bash
python -m venv venv

# Activate on Windows
venv\Scripts\activate

# Activate on macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies

```bash
cd src/backend
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the `src/backend` directory using the provided template:

```bash
cp .env.example .env
```

Edit the `.env` file to configure your local environment settings. The most critical settings are:

```
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=interaction_db
DB_USER=postgres
DB_PASSWORD=your-database-password

# Redis Cache Configuration
REDIS_HOST=localhost
REDIS_PORT=6379

# Auth0 Configuration
AUTH0_DOMAIN=your-tenant.auth0.com
AUTH0_CLIENT_ID=your-auth0-client-id
AUTH0_CLIENT_SECRET=your-auth0-client-secret
AUTH0_AUDIENCE=your-auth0-api-identifier
```

### 5. Setup PostgreSQL Database

```bash
# Create the database
psql -U postgres -c "CREATE DATABASE interaction_db;"

# Run database migrations
python -m scripts.run_migrations
```

### 6. Seed the Database (Optional)

```bash
python -m scripts.db_seed
```

### 7. Run the Development Server

```bash
FLASK_APP=app.py FLASK_ENV=development flask run
```

The backend API will be available at `http://localhost:5000`.

## Containerized Development Setup

Using Docker and Docker Compose provides a consistent development environment that closely mirrors production.

### 1. Configure Environment Variables

Create a `.env` file in the project root directory with the following settings:

```
FLASK_ENV=development
DEBUG=True
DB_NAME=interaction_db
DB_USER=postgres
DB_PASSWORD=postgres
CORS_ALLOWED_ORIGINS=http://localhost:4200,http://frontend:80
```

### 2. Start the Docker Environment

```bash
# Start the development environment
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

This will start all required services:
- Frontend Angular application on port 4200
- Backend Flask API on port 5000
- PostgreSQL database on port 5432
- Redis cache on port 6379

### 3. View Logs

```bash
# View logs from all services
docker-compose logs -f

# View logs from a specific service
docker-compose logs -f backend
```

### 4. Run Commands Inside Containers

```bash
# Access the backend container shell
docker-compose exec backend bash

# Run database migrations
docker-compose exec backend python -m scripts.run_migrations

# Seed the database
docker-compose exec backend python -m scripts.db_seed
```

### 5. Stop the Environment

```bash
docker-compose down

# To remove volumes as well
docker-compose down -v
```

## Database Management

### Database Migrations

The application uses Alembic for database migrations. The migration scripts are located in `src/backend/migrations/versions/`.

```bash
# Create a new migration (after making model changes)
python -m scripts.create_migration "description_of_changes"

# Run pending migrations
python -m scripts.run_migrations

# Downgrade to a specific version
python -m scripts.run_migrations --downgrade <revision_id>

# Downgrade all migrations
python -m scripts.run_migrations --downgrade base
```

### Database Schema

The database includes the following main tables:

- `users`: User accounts and authentication information
- `sites`: Organizational sites that contain interactions
- `user_sites`: Junction table for user-site relationships
- `interactions`: Core interaction records
- `interaction_history`: Audit trail for interaction changes

See the models directory for detailed schema definitions.

## Auth0 Integration

The system uses Auth0 for authentication. Follow these steps to configure Auth0:

### 1. Create an Auth0 Account and Tenant

Sign up at [Auth0](https://auth0.com/) and create a new tenant.

### 2. Create an API

1. In the Auth0 dashboard, go to "APIs" and create a new API
2. Set a name (e.g., "Interaction Management API")
3. Set an identifier (e.g., `https://api.interaction-management.com`)
4. Select the RS256 signing algorithm
5. Note the API Identifier as `AUTH0_AUDIENCE`

### 3. Configure an Application

1. Go to "Applications" and create a new application
2. Select "Single Page Application" type for the frontend
3. Note the Client ID and Client Secret
4. Configure Allowed Callback URLs, Logout URLs, and Web Origins
5. Update your `.env` file with these values

### 4. Configure Connection

Ensure at least one connection (database, social, etc.) is enabled for your application.

### 5. Optional: Create Test Users

Create test users in the Auth0 dashboard for development.

## Environment Configuration

The application uses different configuration sets based on the environment:

### Environment Types

1. **Development**: Local development with debug features enabled
2. **Staging**: Pre-production environment for testing
3. **Production**: Live environment with optimized settings
4. **Testing**: For automated tests

### Configuration Sources

Configuration is loaded from multiple sources in this order:

1. Default values in `config.py`
2. Environment variables
3. `.env` file values

### Critical Environment Variables

```
# Application Settings
FLASK_APP=app.py
FLASK_ENV=development|staging|production
DEBUG=True|False
SECRET_KEY=<secure-random-string>

# Database Configuration
DB_HOST=<host>
DB_PORT=<port>
DB_NAME=<database-name>
DB_USER=<username>
DB_PASSWORD=<password>

# Redis Cache Configuration
REDIS_HOST=<host>
REDIS_PORT=<port>
REDIS_PASSWORD=<password>

# Auth0 Configuration
AUTH0_DOMAIN=<tenant>.auth0.com
AUTH0_CLIENT_ID=<client-id>
AUTH0_CLIENT_SECRET=<client-secret>
AUTH0_AUDIENCE=<api-identifier>

# CORS Settings
CORS_ALLOWED_ORIGINS=<comma-separated-origins>
```

See `.env.example` for a complete list of configurable options.

## Running Tests

The backend includes a comprehensive test suite using pytest.

### 1. Configure Test Environment

```bash
# Create a test database
psql -U postgres -c "CREATE DATABASE interaction_test;"

# Set test environment variables
export FLASK_ENV=testing
export DB_NAME=interaction_test
```

### 2. Run Tests

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=src/backend

# Run specific test file
pytest tests/unit/test_interaction_service.py

# Run tests matching specific pattern
pytest -k "test_create or test_update"
```

### 3. Test in Docker Environment

```bash
docker-compose -f docker-compose.yml -f docker-compose.test.yml up --build -d
docker-compose exec backend pytest
```

For more detailed testing guidance, see [testing.md](testing.md).

## API Documentation

The API documentation is available at:

- Local development: `http://localhost:5000/api/docs`
- Swagger UI: `http://localhost:5000/api/docs/ui`

You can also generate API documentation using:

```bash
python -m scripts.generate_api_docs
```

For detailed API specifications, see [api.md](api.md).

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

#### Migration Errors

- Reset migrations: `python -m scripts.run_migrations --downgrade base`
- Check for conflicting migrations
- Ensure all models are imported in `models/__init__.py`

## Next Steps

After completing the setup process:

1. Review the [development.md](development.md) guide for coding standards and workflows
2. Explore the [api.md](api.md) documentation to understand available endpoints
3. Set up the frontend application following its setup guide
4. Create your first development branch and start contributing

For deployment instructions, see [deployment.md](deployment.md).