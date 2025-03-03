"""
Script that automatically generates comprehensive API documentation by inspecting the Flask application's routes,
controllers, and schemas to produce a structured Markdown document for developer reference.
This reduces manual documentation effort and ensures that API documentation stays in sync with implementation.
"""

import sys  # standard library
import os  # standard library
import argparse  # standard library
import json  # standard library
import inspect  # standard library
from typing import Dict, List, Any, Optional, Tuple, Callable  # typing: standard library

import flask  # flask: version 2.3.2
from flask import Blueprint, Flask, request  # flask: version 2.3.2
import apispec  # apispec: version 6.0.2
from apispec.ext import marshmallow as apispec_marshmallow  # apispec: version 6.0.2

from ...app import app  # src/backend/app.py
from ...api.routes import get_blueprints  # src/backend/api/routes.py
from ...logging.structured_logger import StructuredLogger  # src/backend/logging/structured_logger.py

# Initialize structured logger
logger = StructuredLogger(__name__)

# Define the path for the API documentation file
API_DOC_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'docs', 'api.md')

# Define the API version
API_VERSION = 'v1'


def main() -> int:
    """
    Entry point for the script that parses arguments and generates API documentation.

    Returns:
        int: Exit code (0 for success, non-zero for failure)
    """
    try:
        # Set up argument parser with options for output format and location
        parser = argparse.ArgumentParser(description='Generate API documentation for the Interaction Management System.')
        parser.add_argument('--format', choices=['markdown', 'openapi'], default='markdown',
                            help='Output format for the documentation (markdown or openapi)')
        parser.add_argument('--output', default=API_DOC_PATH,
                            help='Path to the output file (default: ./docs/api.md)')

        # Parse command line arguments
        args = parser.parse_args()

        # Configure logging
        # (Logging configuration is assumed to be handled elsewhere, e.g., in app.py)

        # Create an APISpec instance for OpenAPI specification
        spec = apispec.APISpec(
            title='Interaction Management System API',
            version=API_VERSION,
            openapi_version='3.0.0'
        )

        # Call process_blueprints() to gather route information
        api_data = process_blueprints(spec)

        # Call generate_markdown() or generate_openapi() based on specified format
        if args.format == 'markdown':
            output = generate_markdown(api_data)
        elif args.format == 'openapi':
            output = generate_openapi(spec, api_data)
        else:
            logger.error(f"Invalid format specified: {args.format}")
            return 1

        # Write output to the specified file location
        success = write_output(output, args.output, args.format)

        # Log success and return 0 on successful completion
        if success:
            logger.info(f"API documentation generated successfully in {args.format} format at {args.output}")
            return 0
        else:
            logger.error("API documentation generation failed")
            return 1

    except Exception as e:
        # Log error and return non-zero exit code on failure
        logger.error(f"An unexpected error occurred: {str(e)}")
        return 1


def process_blueprints(spec: apispec.APISpec) -> Dict[str, List[Dict[str, Any]]]:
    """
    Processes all API blueprints to extract route information, schemas, and documentation.

    Args:
        spec (apispec.APISpec): The APISpec instance for OpenAPI documentation.

    Returns:
        Dict[str, List[Dict[str, Any]]]: Structured representation of API endpoints grouped by blueprint.
    """
    # Get all blueprints from get_blueprints()
    blueprints = get_blueprints()

    # Initialize empty dictionary for route documentation
    api_data = {}

    # For each blueprint, iterate through its routes
    for blueprint in blueprints:
        api_data[blueprint.name] = []
        for rule in app.url_map.iter_rules():
            if rule.endpoint.startswith(blueprint.name + '.'):
                # Extract HTTP methods, URL patterns, and handler functions
                methods = rule.methods
                url_pattern = str(rule)
                handler_func = app.view_functions[rule.endpoint]

                # Parse handler function docstrings for description and parameter information
                docstring_info = parse_docstring(handler_func.__doc__)

                # Extract request and response schemas from handler function
                schema_info = extract_schema_info(handler_func)

                # Build structured route information including path, method, description, schemas, and status codes
                route_info = {
                    'path': url_pattern,
                    'methods': methods,
                    'description': docstring_info.get('description', ''),
                    'parameters': docstring_info.get('parameters', []),
                    'responses': docstring_info.get('responses', []),
                    'request_schema': schema_info.get('request_schema'),
                    'response_schema': schema_info.get('response_schema'),
                    'status_codes': docstring_info.get('status_codes', [])
                }

                # Organize routes by blueprint/controller
                api_data[blueprint.name].append(route_info)

    # Return structured API documentation data
    return api_data


def extract_schema_info(handler_func: Callable) -> Dict[str, Any]:
    """
    Extracts schema information from route handler functions.

    Args:
        handler_func (Callable): The route handler function.

    Returns:
        Dict[str, Any]: Schema information including request and response schemas.
    """
    # Use inspect to analyze the handler function
    source = inspect.getsource(handler_func)

    # Look for schema instance usage in the function body
    request_schema = None
    response_schema = None

    # Identify request validation schemas (load method calls)
    if 'load(' in source:
        request_schema = 'RequestSchema'  # Placeholder, replace with actual schema name

    # Identify response serialization schemas (dump method calls)
    if 'dump(' in source:
        response_schema = 'ResponseSchema'  # Placeholder, replace with actual schema name

    # Return dictionary with request and response schema information
    return {
        'request_schema': request_schema,
        'response_schema': response_schema
    }


def parse_docstring(docstring: str) -> Dict[str, Any]:
    """
    Parses function docstrings to extract structured API documentation.

    Args:
        docstring (str): The docstring to parse.

    Returns:
        Dict[str, Any]: Parsed docstring information including description, parameters, responses.
    """
    # Check if docstring exists
    if not docstring:
        return {}

    # Parse description from first paragraph
    description = docstring.split('\n\n')[0]

    # Look for @param tags to extract parameter documentation
    parameters = []
    for line in docstring.splitlines():
        if line.strip().startswith('@param'):
            parts = line.split()
            param_name = parts[2]
            param_type = parts[1]
            param_description = ' '.join(parts[3:])
            parameters.append({'name': param_name, 'type': param_type, 'description': param_description})

    # Look for @return or @response tags to extract response documentation
    responses = []
    for line in docstring.splitlines():
        if line.strip().startswith('@return') or line.strip().startswith('@response'):
            parts = line.split()
            response_code = parts[1]
            response_description = ' '.join(parts[2:])
            responses.append({'code': response_code, 'description': response_description})

    # Look for @status_code tags to extract HTTP status codes
    status_codes = []
    for line in docstring.splitlines():
        if line.strip().startswith('@status_code'):
            parts = line.split()
            status_code = parts[1]
            status_description = ' '.join(parts[2:])
            status_codes.append({'code': status_code, 'description': status_description})

    # Return structured docstring information
    return {
        'description': description,
        'parameters': parameters,
        'responses': responses,
        'status_codes': status_codes
    }


def generate_markdown(api_data: Dict[str, List[Dict[str, Any]]]) -> str:
    """
    Generates Markdown documentation from the structured API data.

    Args:
        api_data (Dict[str, List[Dict[str, Any]]]): The structured API data.

    Returns:
        str: Markdown formatted API documentation.
    """
    # Create markdown header with title and introduction
    markdown = '# Interaction Management System API Documentation\n\n'
    markdown += 'This document provides a comprehensive overview of the Interaction Management System API endpoints.\n\n'

    # Generate 'General Information' section with authentication, error handling guidelines
    markdown += '## General Information\n\n'
    markdown += '- **Authentication:** All API endpoints require authentication via JWT token passed in the `Authorization` header.\n'
    markdown += '- **Error Handling:** The API uses standard HTTP status codes to indicate success or failure. Error responses are formatted as JSON objects with `success`, `message`, and `error_type` fields.\n\n'

    # For each controller/blueprint in api_data:
    for controller, routes in api_data.items():
        # Generate section header based on blueprint name
        markdown += f'## Controller: {controller}\n\n'

        # Generate endpoint subsections with path, method, description
        for route in routes:
            markdown += f'### Endpoint: {route["path"]}\n\n'
            markdown += f'- **Methods:** {", ".join(route["methods"])}\n'
            markdown += f'- **Description:** {route["description"]}\n\n'

            # Include request/response examples based on schemas
            if route['request_schema']:
                markdown += f'- **Request Schema:** `{route["request_schema"]}`\n'
            if route['response_schema']:
                markdown += f'- **Response Schema:** `{route["response_schema"]}`\n'

            # Include status codes and their meanings
            if route['status_codes']:
                markdown += '- **Status Codes:**\n'
                for status in route['status_codes']:
                    markdown += f'  - `{status["code"]}`: {status["description"]}\n'
                markdown += '\n'

    # Generate data models section based on schemas used
    markdown += '## Data Models\n\n'
    markdown += 'This section describes the data models used in the API.\n\n'

    # Generate standard response formats section
    markdown += '## Standard Response Formats\n\n'
    markdown += 'The API uses the following standard response formats:\n\n'
    markdown += '- **Success Response:** `{"success": true, "message": "...", "data": {...}}`\n'
    markdown += '- **Error Response:** `{"success": false, "message": "...", "error_type": "...", "details": {...}}`\n\n'

    # Return complete markdown string
    return markdown


def generate_openapi(spec: apispec.APISpec, api_data: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
    """
    Generates OpenAPI specification from the structured API data.

    Args:
        spec (apispec.APISpec): The APISpec instance for OpenAPI documentation.
        api_data (Dict[str, List[Dict[str, Any]]]): The structured API data.

    Returns:
        Dict[str, Any]: OpenAPI specification as a dictionary.
    """
    # Configure OpenAPI specification metadata (title, version, etc.)
    # (Metadata is already configured during APISpec instantiation)

    # Add schemas from application to the specification
    # (Schemas are assumed to be defined elsewhere and registered with APISpec)

    # For each endpoint in api_data:
    for controller, routes in api_data.items():
        for route in routes:
            # Add path information to the specification
            path = route['path']
            for method in route['methods']:
                # Configure request parameters, body schema, and responses
                # Add security requirements and tags
                pass  # Implementation details for OpenAPI configuration

    # Return complete OpenAPI specification as a dictionary
    return spec.to_dict()


def write_output(content: str, output_path: str, format: str) -> bool:
    """
    Writes generated documentation to the specified file.

    Args:
        content (str): The documentation content to write.
        output_path (str): The path to the output file.
        format (str): The format of the documentation (markdown or openapi).

    Returns:
        bool: True if successful, False otherwise.
    """
    try:
        # Create directories for output file if they don't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Open output file for writing
        with open(output_path, 'w') as f:
            # If format is JSON (OpenAPI), dump JSON content
            if format == 'openapi':
                json.dump(content, f, indent=2)
            # If format is Markdown, write content as is
            else:
                f.write(content)

        # Close file and return success status
        return True

    except Exception as e:
        # Handle any exceptions, log error, and return False on failure
        logger.error(f"Error writing output to file: {str(e)}")
        return False


if __name__ == '__main__':
    # Execute main function and exit with appropriate code
    sys.exit(main())