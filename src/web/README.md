# Interaction Management System - Frontend

Angular-based web application for managing and viewing Interaction records through a searchable table interface (Finder) and a dedicated add/edit form. Part of the Interaction Management System that enables organizations to track various interactions across multiple sites with controlled user access.

## Technologies

* Angular 16.2.0
* TypeScript 4.9.5
* TailwindCSS 3.3.3
* AG Grid 30.0.3 for the Finder interface
* date-fns 2.30.0 for date handling
* Auth0 integration for authentication
* Jest and Cypress for testing

## Prerequisites

* Node.js 18.x or higher
* npm 9.x or higher
* Docker and Docker Compose (for containerized development)
* Auth0 account (for authentication development)

## Getting Started

### Local Development Setup

1. Clone the repository
2. Navigate to the web directory: `cd src/web`
3. Install dependencies: `npm install`
4. Create environment configuration (copy .env.example to .env)
5. Start the development server: `npm start`

The application will be available at http://localhost:4200.

### Using Docker

Alternatively, you can use Docker Compose to run the entire application stack:

```bash
# From the project root
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

This will start the frontend, backend, database, and cache services. The frontend will be available at http://localhost:80.

## Project Structure

```
src/
  app/
    core/                 # Core modules, services, and utilities
      auth/              # Authentication services and guards
      cache/             # Caching implementation
      http/              # HTTP interceptors and API service
      errors/            # Error handling
    features/            # Feature modules
      auth/              # Authentication components and pages
      dashboard/         # Dashboard feature module
      interactions/      # Interaction management components
      sites/             # Site management
    shared/              # Shared components, directives, and pipes
  assets/                # Static assets
  environments/          # Environment configuration
  styles/                # Global styles and design system
```

## Available Scripts

* `npm start` - Start the development server
* `npm run build` - Build the application for development
* `npm run build:prod` - Build the application for production
* `npm run build:staging` - Build the application for staging
* `npm test` - Run Angular tests with Karma
* `npm run test:jest` - Run Jest tests
* `npm run test:coverage` - Generate test coverage report
* `npm run cypress:open` - Open Cypress test runner
* `npm run cypress:run` - Run Cypress tests headlessly
* `npm run lint` - Lint the codebase
* `npm run lint:fix` - Fix linting issues

## Environment Configuration

The application supports multiple environments:

* Development: `environment.ts`
* Staging: `environment.staging.ts`
* Production: `environment.prod.ts`

Key configuration includes:

* API URL
* Auth0 settings
* Caching parameters
* Feature flags

Refer to `src/environments/environment.ts` for the complete configuration structure.

## Testing

The application uses multiple testing frameworks:

### Unit Testing

* Jest for component and service tests: `npm run test:jest`
* Karma for Angular-specific tests: `npm test`

### End-to-End Testing

* Cypress for UI automation tests: `npm run cypress:open`

Tests are run automatically in the CI pipeline. The minimum required coverage is 85% for statements, functions, and lines, and 75% for branches.

## Containerization

The application uses a multi-stage Docker build process:

1. Build stage: Compiles the Angular application
2. Production stage: Serves the built application with NGINX

Customize the Docker build by editing the `Dockerfile` in the web directory.

## Deployment

The application can be deployed through the CI/CD pipeline:

* Development: Triggered by changes to development branch
* Staging: Triggered by creating a release candidate tag
* Production: Triggered by creating a release tag

Refer to the GitHub Workflows in `.github/workflows/` for detailed pipeline configurations.

## Authentication

The application uses Auth0 for authentication. The authentication flow includes:

1. Login through Auth0 Universal Login page
2. JWT token storage and validation
3. Site access control based on user permissions

Authentication configuration is in `src/environments/environment.ts` and handled by the AuthService.

## Key Features

* **Authentication**: Secure login with Auth0 integration
* **Site Selection**: Access control based on user-site associations
* **Interaction Finder**: Searchable, filterable table of interactions
* **Interaction Forms**: Creation and editing of interaction records
* **Responsive Design**: Mobile-friendly interfaces across all device sizes

## Contributing

1. Follow the Angular coding style guidelines
2. Write tests for new features
3. Ensure all existing tests pass before submitting PR
4. Use conventional commit message format
5. Update documentation for significant changes

## Troubleshooting

### Common Issues

* **API connection errors**: Ensure the backend service is running and accessible
* **Auth0 integration issues**: Verify Auth0 configuration in environment files
* **Build errors**: Check Node.js and npm versions match requirements

For more help, refer to the project documentation in `/docs` or contact the development team.