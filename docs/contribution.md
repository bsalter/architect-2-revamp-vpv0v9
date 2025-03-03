# Contributing to the Interaction Management System

Thank you for your interest in contributing to the Interaction Management System! This document provides guidelines and instructions for contributing to the project. By participating in this project, you agree to abide by its terms and follow the processes outlined below.

## Code of Conduct

We are committed to providing a welcoming and inclusive experience for everyone. By participating in this project, you are expected to:

- Be respectful and considerate of differing viewpoints and experiences
- Give and gracefully accept constructive feedback
- Focus on what is best for the community and the project
- Show empathy towards other community members

Unacceptable behavior includes but is not limited to:
- Harassment of any participants in any form
- Deliberate intimidation, stalking, or following
- Publishing others' private information without explicit permission
- Other conduct which could reasonably be considered inappropriate in a professional setting

If you experience or witness unacceptable behavior, please report it to the project maintainers.

## Getting Started

### Prerequisites

Before you begin, ensure you have the following installed:

- Git
- Docker and Docker Compose (recommended for development)
- Node.js 18+ and npm 9+ (for frontend development)
- Python 3.11+ (for backend development)
- Auth0 account (for authentication development)

The project uses Docker for consistent development environments. To set up your environment:

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/interaction-management.git
   cd interaction-management
   ```

3. Set up the development environment:
   ```bash
   make setup
   ```

4. Start the development environment:
   ```bash
   make dev
   ```

This will start the application with all components (frontend, backend, database, cache) in development mode with hot reloading enabled.

## Development Workflow

We follow a feature branch workflow with pull requests. Here's the recommended process:

1. **Create a feature branch** from the main branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```
   Use a descriptive branch name prefixed with `feature/`, `fix/`, `docs/`, etc.

2. **Make your changes** in the feature branch.

3. **Write or update tests** for your changes. Ensure:
   - Frontend code has at least 85% test coverage
   - Backend code has at least 90% test coverage
   - Critical paths have at least 95% test coverage

4. **Run tests locally** to verify your changes:
   ```bash
   make test
   ```

5. **Lint and format your code**:
   ```bash
   make lint
   make format
   ```

6. **Commit your changes** with clear, descriptive commit messages following the conventional commit format:
   ```
   <type>(<scope>): <short summary>
   ```
   Where `type` is one of: feat, fix, docs, style, refactor, perf, test, build, ci, chore

7. **Push your branch** to your fork:
   ```bash
   git push -u origin feature/your-feature-name
   ```

8. **Create a pull request** from your branch to the main repository's main branch.

9. **Address any feedback** from code reviews and update your pull request as needed.

## Pull Request Process

1. **Create your pull request** against the main branch using the provided PR template.

2. **Fill out the PR template** completely, including:
   - Type of change
   - Description of changes
   - Related issues
   - Component checklist
   - Testing details

3. **Ensure all CI checks pass**:
   - Unit tests
   - Integration tests
   - Linting
   - Code coverage thresholds

4. **Request a review** from at least one maintainer.

5. **Address all feedback** from reviewers. Make necessary changes and push to your feature branch to update the PR.

6. **Once approved**, a maintainer will merge your PR.

7. **Delete your branch** after the PR is merged.

Note: Pull requests must receive approval from at least one maintainer before they can be merged. Maintainers may request changes or improvements before approving.

## Coding Standards

### General Guidelines

- Write clean, readable, and maintainable code
- Include comments for complex logic, but prefer self-documenting code
- Keep functions and methods focused on a single responsibility
- Follow the established patterns and architecture of the project
- Maintain site-scoping security in all data access operations

### Backend (Python) Standards

- Follow PEP 8 style guidelines
- Use Black for code formatting: `make format-backend`
- Use Pylint for linting: `make lint-backend`
- Use type hints where appropriate
- Document functions and classes with docstrings
- Maintain 90% or higher test coverage
- Follow the layered architecture (controllers, services, repositories)
- Ensure all database queries include site-scoping filters

### Frontend (Angular/TypeScript) Standards

- Follow the Angular style guide
- Use ESLint for linting: `make lint-frontend`
- Use Prettier for formatting: `make format-frontend`
- Maintain 85% or higher test coverage
- Use strong typing with TypeScript
- Implement responsive designs following mobile-first approach
- Ensure WCAG 2.1 AA accessibility compliance
- Follow component-based architecture
- Implement proper error handling and user feedback

### Database Considerations

- Create migrations for all schema changes
- Test migrations thoroughly, including rollback procedures
- Consider query performance in high-volume operations
- Enforce site-scoping at the database level where possible
- Implement proper indexes for search operations

## Testing Requirements

All code contributions must include appropriate tests. The project maintains high test coverage standards:

- Frontend: 85% minimum coverage (statements, functions, lines) and 75% branch coverage
- Backend: 90% minimum coverage (statements, functions, lines) and 85% branch coverage
- Critical paths: 95% minimum coverage

### Backend Testing

- Write unit tests for models, services, and repositories
- Write integration tests for API endpoints
- Use pytest fixtures for test data
- Mock external dependencies
- Test both success and error scenarios
- Verify site-scoping in all data access tests

Run backend tests with:
```bash
make test-backend
```

### Frontend Testing

- Write unit tests for services, components, and pipes
- Use TestBed for Angular component testing
- Mock backend API responses
- Test both success and error scenarios
- Write end-to-end tests for critical user flows

Run frontend tests with:
```bash
make test-frontend
```

### End-to-End Testing

- Write Cypress tests for critical user journeys
- Test across different screen sizes
- Verify accessibility compliance

Run end-to-end tests with:
```bash
make e2e
```

## Issue Reporting

We use GitHub Issues to track bugs, features, and enhancements. Before creating an issue:

1. Search existing issues to avoid duplicates
2. Use the provided issue templates for bug reports and feature requests
3. Provide as much detail as possible to help us understand and address the issue

### Bug Reports

When reporting a bug, please include:

- A clear and concise description of the bug
- Step-by-step reproduction instructions
- Expected behavior vs. actual behavior
- Screenshots if applicable
- Environment details (browser, OS, application version)
- Error messages or console output

### Feature Requests

When requesting a feature, please include:

- A clear and concise description of the feature
- The problem it solves or need it addresses
- User stories or use cases
- Any implementation ideas you may have

## Documentation

Documentation is a crucial part of the project. When contributing, please:

- Update relevant documentation for your changes
- Document new features, APIs, or significant changes
- Use clear, concise language accessible to various technical levels
- Include examples where appropriate

Documentation sources include:

- Code comments and docstrings
- README files in project directories
- API documentation via OpenAPI/Swagger
- User documentation in the docs directory

For significant documentation changes, consider creating a separate PR focused solely on documentation updates.

## Branch Strategy

The project maintains the following branches:

- `main`: Production-ready code, protected branch
- `develop`: Integration branch for active development (when applicable)
- `feature/*`: Feature branches for new development
- `fix/*`: Bug fix branches
- `docs/*`: Documentation update branches
- `release/*`: Release preparation branches

The general workflow is:

1. Create a feature/fix branch from `main`
2. Develop and test in your branch
3. Submit a PR to merge back into `main`
4. After review and approval, the branch is merged

Periodically, stable releases are tagged from the `main` branch following semantic versioning.

## Release Process

Releases follow semantic versioning (MAJOR.MINOR.PATCH):

- MAJOR: Incompatible API changes
- MINOR: Backwards-compatible functionality additions
- PATCH: Backwards-compatible bug fixes

The release process includes:

1. Creating a release branch from `main`
2. Finalizing and testing the release
3. Updating version numbers in relevant files
4. Updating CHANGELOG.md with significant changes
5. Creating a tagged release in GitHub
6. Deploying to production

Maintainers are responsible for creating and managing releases.

## Performance Considerations

When contributing code, consider these performance aspects:

### Frontend Performance

- Optimize bundle size by avoiding unnecessary dependencies
- Implement lazy loading for non-critical components and routes
- Use virtual scrolling for large data sets in the Finder table
- Implement proper caching strategies
- Optimize Angular change detection

### Backend Performance

- Optimize database queries with proper indexing
- Use caching for frequently accessed data
- Implement pagination for large result sets
- Profile and optimize critical paths
- Consider query execution plans for complex searches

### Database Performance

- Create appropriate indexes for search fields
- Use database query optimization techniques
- Consider partitioning for large tables
- Optimize data access patterns

Include performance testing results in PRs for performance-sensitive changes.

## Security Best Practices

When contributing code, follow these security best practices:

### Authentication and Authorization

- Never bypass authentication checks
- Always implement site-scoping for data access
- Follow the principle of least privilege
- Do not hardcode credentials or secrets

### Data Protection

- Validate all user inputs on both client and server
- Use parameterized queries to prevent SQL injection
- Sanitize data for output to prevent XSS
- Implement proper error handling without exposing sensitive details

### Web Security

- Use CSRF protection for state-changing requests
- Implement proper Content Security Policy
- Apply rate limiting to prevent abuse
- Follow secure cookie practices

### Dependencies

- Regularly update dependencies to address security vulnerabilities
- Minimize use of third-party libraries where possible
- Verify the security posture of new dependencies

Security issues should be reported privately to the maintainers rather than via public issues.

## Troubleshooting and Support

### Common Issues

#### Development Environment

- **Docker containers not starting**: Check Docker logs with `docker-compose logs -f`
- **Database connection issues**: Verify PostgreSQL is running and credentials are correct
- **Auth0 configuration**: Check Auth0 settings in your environment variables

#### Testing

- **Test failures**: Run tests with verbose output for debugging: `pytest -vv`
- **Coverage issues**: Generate and view detailed coverage reports

### Getting Help

If you need assistance with your contribution:

1. Check the documentation in the `docs` directory
2. Review existing issues and discussions on GitHub
3. Ask questions in pull requests or issues
4. Reach out to maintainers for guidance

Maintainers and experienced contributors will try to help with questions related to contributing to the project.

## Project Overview

The Interaction Management System is a web application for managing and viewing Interaction records through a searchable table interface ("Finder") and a dedicated add/edit form.

The system enables organizations to track various interactions across multiple sites with controlled user access. It provides:

- Site-scoped authentication and authorization
- Comprehensive interaction management
- Advanced search and filtering
- Multi-site support

For detailed information about the system architecture, please refer to the [Architecture Documentation](docs/architecture.md).

## Acknowledgements

We appreciate all contributors who help improve the Interaction Management System! All contributors will be acknowledged in the project repository.

By following these contribution guidelines, you help maintain a high-quality, consistent codebase that benefits all users of the system.