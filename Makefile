# Interaction Management System
# Standardized commands for development, testing, building, and deployment

# Set shell to bash
SHELL := /bin/bash

# Directory variables
FRONTEND_DIR := src/web
BACKEND_DIR := src/backend

# Docker compose commands
DOCKER_COMPOSE := docker-compose
DOCKER_COMPOSE_DEV := docker-compose -f docker-compose.yml -f docker-compose.dev.yml
DOCKER_COMPOSE_TEST := docker-compose -f docker-compose.yml -f docker-compose.test.yml

# Phony targets (targets that aren't files)
.PHONY: help setup start stop db-migrate test lint build docker-build clean tf-plan logs \
	frontend-install backend-install frontend-test backend-test e2e-test \
	frontend-lint backend-lint frontend-build backend-build seed-data

# Default target
.DEFAULT_GOAL := help

# Display help information
help:
	@echo "Interaction Management System - Make Commands"
	@echo "============================================="
	@echo "help           - Display this help information"
	@echo "setup          - Set up the full development environment"
	@echo "start          - Start all application services in development mode"
	@echo "stop           - Stop all application services"
	@echo "db-migrate     - Run database migrations" 
	@echo "test           - Run all tests (frontend, backend, e2e)"
	@echo "lint           - Run linting on frontend and backend code"
	@echo "build          - Build all application components"
	@echo "docker-build   - Build all Docker images"
	@echo "clean          - Clean all build artifacts and temporary files"
	@echo "tf-plan        - Run Terraform plan for infrastructure (usage: make tf-plan env=dev)"
	@echo "logs           - View application logs"

# Set up the development environment
setup: frontend-install backend-install
	@echo "Setting up Docker environment..."
	$(DOCKER_COMPOSE_DEV) up -d --build
	@echo "Running database migrations..."
	$(MAKE) db-migrate
	@echo "Seeding initial data..."
	$(MAKE) seed-data
	@echo "Development environment is ready!"

# Install frontend dependencies
frontend-install:
	@echo "Installing frontend dependencies..."
	cd $(FRONTEND_DIR) && npm install

# Install backend dependencies
backend-install:
	@echo "Installing backend dependencies..."
	cd $(BACKEND_DIR) && pip install -r requirements.txt
	cd $(BACKEND_DIR) && pip install -r requirements-dev.txt

# Seed initial data
seed-data:
	@echo "Seeding initial data..."
	docker exec -it backend python manage.py seed_data

# Start all application services
start:
	@echo "Starting application services..."
	$(DOCKER_COMPOSE_DEV) up -d
	@echo "Application is running. Access the frontend at http://localhost:4200"

# Stop all application services
stop:
	@echo "Stopping application services..."
	$(DOCKER_COMPOSE) down
	@echo "Application services stopped"

# Run database migrations
db-migrate:
	@echo "Running database migrations..."
	docker exec -it backend python run_migrations.py
	@echo "Database migrations completed"

# Run all tests
test: frontend-test backend-test e2e-test
	@echo "All tests completed"

# Run frontend tests
frontend-test:
	@echo "Running frontend tests..."
	cd $(FRONTEND_DIR) && npm run test

# Run backend tests
backend-test:
	@echo "Running backend tests..."
	cd $(BACKEND_DIR) && pytest

# Run end-to-end tests
e2e-test:
	@echo "Running end-to-end tests..."
	$(DOCKER_COMPOSE_TEST) up -d
	cd $(FRONTEND_DIR) && npm run e2e
	$(DOCKER_COMPOSE_TEST) down

# Run linting
lint: frontend-lint backend-lint
	@echo "Linting completed"

# Run frontend linting
frontend-lint:
	@echo "Running frontend linting..."
	cd $(FRONTEND_DIR) && npm run lint

# Run backend linting
backend-lint:
	@echo "Running backend linting..."
	cd $(BACKEND_DIR) && flake8

# Build all application components
build: frontend-build backend-build
	@echo "Build completed"

# Build frontend
frontend-build:
	@echo "Building frontend..."
	cd $(FRONTEND_DIR) && npm run build

# Build backend
backend-build:
	@echo "Building backend..."
	cd $(BACKEND_DIR) && python setup.py build

# Build Docker images
docker-build:
	@echo "Building Docker images..."
	$(DOCKER_COMPOSE) build
	@echo "Docker images built"

# Clean build artifacts and temporary files
clean:
	@echo "Cleaning frontend build artifacts..."
	cd $(FRONTEND_DIR) && npm run clean
	@echo "Cleaning backend build artifacts..."
	cd $(BACKEND_DIR) && rm -rf build/ dist/ *.egg-info/ __pycache__/ .pytest_cache/
	@echo "Removing Docker containers and volumes..."
	$(DOCKER_COMPOSE) down -v
	@echo "Clean completed"

# Run Terraform plan
tf-plan:
	@if [ -z "$(env)" ]; then echo "Error: env parameter is required. Usage: make tf-plan env=dev"; exit 1; fi
	@echo "Running Terraform plan for environment: $(env)"
	cd infrastructure/terraform && \
	terraform init && \
	terraform plan -var-file="environments/$(env).tfvars" -out="$(env).tfplan"

# View application logs
logs:
	@echo "Viewing application logs..."
	$(DOCKER_COMPOSE) logs -f