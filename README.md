# Interaction Management System

A comprehensive web application for managing and viewing Interaction records through a searchable table interface ("Finder") and a dedicated add/edit form. The system enables organizations to track various interactions across multiple sites with controlled user access.

## Key Features
- **Site-scoped Access Control**: Data isolation between organizational sites
- **Interaction Management**: Complete CRUD operations for interaction records
- **Advanced Search**: High-performance search capabilities across interaction fields
- **Responsive Design**: Mobile-friendly interfaces across all device sizes
- **Authentication**: Secure JWT-based authentication integrated with Auth0

## System Overview

The Interaction Management System consists of three primary components:

- **Finder Interface**: A searchable table view displaying Interaction records with filterable columns
- **Interaction Form**: A detailed add/edit interface for Interaction records
- **Authentication System**: Site-scoped user authentication controlling access to Interaction data

The application utilizes a modern web architecture with responsive design principles to ensure usability across devices.

## Technology Stack
### Frontend
- Angular 16.2.0 (TypeScript 4.9.5)
- TailwindCSS 3.3.3
- AG Grid 30.0.3
- date-fns 2.30.0
- Auth0 SDK

### Backend
- Flask 2.3.2 (Python 3.11)
- SQLAlchemy 2.0.19
- Flask-JWT-Extended 4.5.2
- marshmallow 3.20.1

### Database & Storage
- PostgreSQL 15.3
- Alembic 1.11.1 (migrations)
- Redis 7.0.12 (caching)

### Testing
- Jest and Cypress (frontend)
- pytest (backend)

### DevOps
- Docker / Docker Compose
- GitHub Actions (CI/CD)
- Terraform (Infrastructure as Code)
- AWS (hosting infrastructure)

## Project Structure
```
├── .github/            # GitHub Actions workflows and templates
├── docs/               # Project documentation
├── infrastructure/     # Terraform configurations and monitoring
├── src/
│   ├── backend/        # Flask API backend
│   │   ├── api/        # API controllers, routes, and schemas
│   │   ├── auth/       # Authentication services
│   │   ├── models/     # SQLAlchemy data models
│   │   ├── services/   # Business logic layer
│   │   └── ...        # Additional backend components
│   └── web/           # Angular frontend application
│       ├── src/app/\n│       │   ├── core/   # Core modules and services
│       │   ├── features/ # Feature modules
│       │   └── shared/ # Shared components and utilities
│       └── ...        # Additional frontend files
├── docker-compose.yml # Main Docker Compose configuration
├── docker-compose.dev.yml # Development environment configuration
└── ...               # Additional project files
```

## Getting Started
### Prerequisites

- Docker and Docker Compose (recommended for development)
- Node.js 18+ and npm 9+ (for frontend development)
- Python 3.11+ (for backend development)
- PostgreSQL 15.3+ (for local database)
- Redis 7.0+ (for caching)
- Auth0 account (for authentication)

### Quick Start with Docker

1. Clone the repository
   ```bash
   git clone https://github.com/your-org/interaction-management.git
   cd interaction-management
   ```

2. Create environment files
   ```bash
   cp src/backend/.env.example src/backend/.env
   # Edit .env with your configuration
   ```

3. Start the application with Docker Compose
   ```bash
   docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
   ```

4. Access the application:
   - Frontend: http://localhost:80
   - Backend API: http://localhost:5000
   - API Documentation: http://localhost:5000/api/docs/ui

### Development Setup

For detailed instructions on setting up for development, refer to:
- [Backend Setup](src/backend/README.md#getting-started)
- [Frontend Setup](src/web/README.md#getting-started)

## Authentication

The application uses Auth0 for authentication:

1. Users log in via Auth0 through the frontend
2. JWT tokens are issued containing user identity and site access information
3. Backend validates tokens and enforces site-scoped access control
4. Token refresh is handled via refresh tokens

To configure Auth0:

1. Create an Auth0 account and tenant
2. Configure an API and application
3. Set Auth0 environment variables in `.env` files

Detailed Auth0 configuration steps can be found in the [backend documentation](src/backend/docs/setup.md).

## Development Workflow

We follow a feature branch workflow with pull requests:

1. Create a feature branch from the main branch
2. Make your changes in the feature branch
3. Write or update tests for your changes
4. Run tests locally to verify your changes
5. Lint and format your code
6. Commit your changes with descriptive commit messages
7. Push your branch to your fork
8. Create a pull request to the main repository
9. Address any feedback from code reviews

Detailed contribution guidelines can be found in the [contribution documentation](docs/contribution.md).

## Deployment

The application is designed for deployment using Docker containers on AWS:

1. Build the Docker images with production settings
2. Deploy to the target environment (AWS ECS recommended)
3. Ensure database migrations are applied
4. Configure environment variables for the production environment

CI/CD pipelines using GitHub Actions are configured for automatic deployment.

Detailed deployment instructions can be found in the [deployment documentation](docs/deployment.md).

## Testing

The project includes comprehensive testing at multiple levels:

### Backend
```bash
# Navigate to backend directory
cd src/backend

# Run all tests
pytest

# Run with coverage
pytest --cov=src/backend
```

### Frontend
```bash
# Navigate to web directory
cd src/web

# Run Jest tests
npm run test:jest

# Run Angular tests
npm test

# Run end-to-end tests
npm run cypress:open
```

## Architecture

The system implements a layered architecture with clear separation of concerns:

- **Frontend**: Angular SPA with component-based UI and state management
- **Backend**: Flask API with controller-service-repository pattern
- **Database**: PostgreSQL with site-scoped data access
- **Authentication**: Auth0 integration with JWT validation

For detailed architecture documentation, refer to the [architecture documentation](docs/architecture.md).

## Contributing

We welcome contributions to the Interaction Management System! Please see the [contribution guidelines](docs/contribution.md) for details on our code of conduct and the process for submitting pull requests.

## License

Copyright © 2023 Interaction Management System

All rights reserved. This software and associated documentation are proprietary and confidential.

## Support

For issues, questions, or support, please create an issue in the GitHub repository.