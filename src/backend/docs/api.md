# Interaction Management System API Documentation

## Introduction

The Interaction Management System API provides a RESTful interface for managing interaction records across multiple organizational sites. This API allows clients to create, read, update, and delete interaction records, as well as perform various search operations with filtering capabilities.

Key features include:
- JWT-based authentication with site-scoped access control
- Comprehensive CRUD operations for interaction records
- Advanced search functionality with multiple filtering options
- Pagination support for list endpoints
- Versioned API design for backward compatibility

This document serves as the primary reference for developers integrating with or maintaining the API.

## Authentication

The API implements a JWT (JSON Web Token) based authentication system. All API requests (except for authentication endpoints) must include a valid JWT token in the Authorization header.

### Authentication Flow

1. Client submits credentials to `/api/auth/login`
2. Server validates credentials and returns a JWT token with user information
3. Client includes the JWT token in the Authorization header for subsequent requests
4. When the token expires (30 minutes default), client can use the refresh token to obtain a new JWT

### Token Usage

Include the JWT token in all authenticated requests using the following header format:

```
Authorization: Bearer <token>
```

### Site Context

The API implements site-scoping where users can only access interaction data for sites they have permission to view. After authentication, users with access to multiple sites must select a site context before accessing interaction data.

## API Versioning

The API implements version control through the URL path. The current version is v1.

```
https://api.example.com/api/v1/resource
```

All URLs in this documentation assume the `/api/v1` prefix.

### Compatibility Policy

- Major versions (v1, v2) may contain breaking changes
- Within a major version, backward compatibility is maintained
- Deprecated endpoints will be marked in documentation and return warning headers
- Major versions are supported for a minimum of 12 months after deprecation notice

## Error Handling

The API uses standard HTTP status codes and returns errors in a consistent JSON format:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {
      "field_name": "Field-specific error message"
    }
  }
}
```

### Common Error Codes

| HTTP Status | Error Code | Description |
|-------------|------------|-------------|
| 400 | BAD_REQUEST | Invalid request format or parameters |
| 401 | UNAUTHORIZED | Missing or invalid authentication |
| 403 | FORBIDDEN | Authenticated but insufficient permissions |
| 404 | NOT_FOUND | Requested resource not found |
| 422 | VALIDATION_ERROR | Request validation failed |
| 429 | RATE_LIMITED | Too many requests |
| 500 | SERVER_ERROR | Internal server error |

## Rate Limiting

To ensure API stability and performance, rate limits are enforced based on the client's identity.

| Client Type | Default Rate | Scope |
|-------------|--------------|-------|
| Anonymous | 30/minute | IP address |
| Authenticated | 300/minute | User ID |
| Search Operations | 60/minute | User ID |
| Auth Operations | 10/minute | IP address |

### Rate Limit Headers

The following headers are included in API responses:

- `X-RateLimit-Limit`: Maximum requests allowed in the current time window
- `X-RateLimit-Remaining`: Requests remaining in the current time window
- `X-RateLimit-Reset`: Time when the current rate limit window resets (Unix timestamp)

When a rate limit is exceeded, a 429 Too Many Requests response is returned.

## Authentication Endpoints

### Login

Authenticate user credentials and receive JWT token.

**Endpoint:** `POST /api/auth/login`

**Request Body:**
```json
{
  "username": "user@example.com",
  "password": "secure_password"
}
```

**Response: (200 OK)**
```json
{
  "token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires": "2023-07-15T15:30:00Z",
  "user": {
    "id": 123,
    "username": "user@example.com",
    "email": "user@example.com",
    "sites": [1, 2, 3]
  }
}
```

**Error Response: (401 Unauthorized)**
```json
{
  "error": {
    "code": "INVALID_CREDENTIALS",
    "message": "Invalid username or password"
  }
}
```

### Refresh Token

Refresh an expired JWT token.

**Endpoint:** `POST /api/auth/refresh`

**Request Body:**
```json
{
  "refresh_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response: (200 OK)**
```json
{
  "token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires": "2023-07-15T16:00:00Z"
}
```

**Error Response: (401 Unauthorized)**
```json
{
  "error": {
    "code": "INVALID_REFRESH_TOKEN",
    "message": "Invalid or expired refresh token"
  }
}
```

### Logout

Invalidate the current JWT token.

**Endpoint:** `POST /api/auth/logout`

**Request Headers:**
```
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response: (200 OK)**
```json
{
  "success": true
}
```

### Get User's Sites

Get all sites available to the current user.

**Endpoint:** `GET /api/auth/sites`

**Request Headers:**
```
Authorization: Bearer <token>
```

**Response: (200 OK)**
```json
{
  "sites": [
    {
      "id": 1,
      "name": "Headquarters",
      "description": "Main corporate headquarters"
    },
    {
      "id": 2,
      "name": "Northwest Regional Office",
      "description": "Regional branch serving the northwest territory"
    }
  ]
}
```

**Error Response: (401 Unauthorized)**
```json
{
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Authentication required"
  }
}
```

### Switch Site Context

Switch the current site context.

**Endpoint:** `POST /api/auth/site`

**Request Headers:**
```
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "site_id": 2
}
```

**Response: (200 OK)**
```json
{
  "success": true
}
```

**Error Responses:**
- 401 Unauthorized: Authentication required
- 403 Forbidden: User does not have access to the specified site

### Get User Profile

Get the current user's profile information.

**Endpoint:** `GET /api/auth/profile`

**Request Headers:**
```
Authorization: Bearer <token>
```

**Response: (200 OK)**
```json
{
  "user": {
    "id": 123,
    "username": "user@example.com",
    "email": "user@example.com",
    "sites": [1, 2, 3]
  }
}
```

**Error Response: (401 Unauthorized)**
```json
{
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Authentication required"
  }
}
```

### Request Password Reset

Request a password reset email.

**Endpoint:** `POST /api/auth/password/reset`

**Request Body:**
```json
{
  "email": "user@example.com"
}
```

**Response: (200 OK)**
```json
{
  "success": true
}
```

**Error Response: (400 Bad Request)**
```json
{
  "error": {
    "code": "INVALID_EMAIL",
    "message": "Invalid email address"
  }
}
```

## Interaction Endpoints

### List Interactions

Get a paginated list of interactions with optional search parameters.

**Endpoint:** `GET /api/interactions`

**Request Headers:**
```
Authorization: Bearer <token>
```

**Query Parameters:**
- `search` (optional): Search term to filter interactions
- `page` (optional): Page number for pagination (default: 1)
- `page_size` (optional): Items per page (default: 20, max: 100)

**Response: (200 OK)**
```json
{
  "interactions": [
    {
      "id": 1,
      "site_id": 2,
      "title": "Team Kickoff Meeting",
      "type": "Meeting",
      "lead": "John Smith",
      "start_datetime": "2023-06-12T10:00:00Z",
      "end_datetime": "2023-06-12T11:00:00Z",
      "timezone": "America/New_York",
      "location": "Conference Room A",
      "description": "Initial project kickoff meeting with team members",
      "notes": "Bring project documentation",
      "created_by": 123,
      "created_at": "2023-06-01T15:30:00Z",
      "updated_at": "2023-06-01T15:30:00Z"
    }
  ],
  "total": 24,
  "page": 1
}
```

**Error Response: (401 Unauthorized)**
```json
{
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Authentication required"
  }
}
```

### Create Interaction

Create a new interaction.

**Endpoint:** `POST /api/interactions`

**Request Headers:**
```
Authorization: Bearer <token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "title": "Project Status Update",
  "type": "Meeting",
  "lead": "Jane Doe",
  "start_datetime": "2023-06-20T14:00:00Z",
  "end_datetime": "2023-06-20T15:00:00Z",
  "timezone": "America/Chicago",
  "location": "Virtual Conference Room",
  "description": "Weekly project status update meeting",
  "notes": "Prepare progress report"
}
```

**Response: (201 Created)**
```json
{
  "interaction": {
    "id": 25,
    "site_id": 2,
    "title": "Project Status Update",
    "type": "Meeting",
    "lead": "Jane Doe",
    "start_datetime": "2023-06-20T14:00:00Z",
    "end_datetime": "2023-06-20T15:00:00Z",
    "timezone": "America/Chicago",
    "location": "Virtual Conference Room",
    "description": "Weekly project status update meeting",
    "notes": "Prepare progress report",
    "created_by": 123,
    "created_at": "2023-06-15T09:30:00Z",
    "updated_at": "2023-06-15T09:30:00Z"
  }
}
```

**Error Responses:**
- 400 Bad Request: Invalid request format or validation error
- 401 Unauthorized: Authentication required
- 403 Forbidden: Insufficient permissions to create interaction

### Get Interaction

Get a specific interaction by ID.

**Endpoint:** `GET /api/interactions/{id}`

**Request Headers:**
```
Authorization: Bearer <token>
```

**Response: (200 OK)**
```json
{
  "interaction": {
    "id": 1,
    "site_id": 2,
    "title": "Team Kickoff Meeting",
    "type": "Meeting",
    "lead": "John Smith",
    "start_datetime": "2023-06-12T10:00:00Z",
    "end_datetime": "2023-06-12T11:00:00Z",
    "timezone": "America/New_York",
    "location": "Conference Room A",
    "description": "Initial project kickoff meeting with team members",
    "notes": "Bring project documentation",
    "created_by": 123,
    "created_at": "2023-06-01T15:30:00Z",
    "updated_at": "2023-06-01T15:30:00Z"
  }
}
```

**Error Responses:**
- 401 Unauthorized: Authentication required
- 403 Forbidden: Insufficient permissions to view this interaction
- 404 Not Found: Interaction not found

### Update Interaction

Update an existing interaction.

**Endpoint:** `PUT /api/interactions/{id}`

**Request Headers:**
```
Authorization: Bearer <token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "title": "Team Kickoff Meeting - Updated",
  "type": "Meeting",
  "lead": "John Smith",
  "start_datetime": "2023-06-12T10:30:00Z",
  "end_datetime": "2023-06-12T11:30:00Z",
  "timezone": "America/New_York",
  "location": "Conference Room B",
  "description": "Initial project kickoff meeting with team members",
  "notes": "Bring project documentation and status reports"
}
```

**Response: (200 OK)**
```json
{
  "interaction": {
    "id": 1,
    "site_id": 2,
    "title": "Team Kickoff Meeting - Updated",
    "type": "Meeting",
    "lead": "John Smith",
    "start_datetime": "2023-06-12T10:30:00Z",
    "end_datetime": "2023-06-12T11:30:00Z",
    "timezone": "America/New_York",
    "location": "Conference Room B",
    "description": "Initial project kickoff meeting with team members",
    "notes": "Bring project documentation and status reports",
    "created_by": 123,
    "created_at": "2023-06-01T15:30:00Z",
    "updated_at": "2023-06-15T10:15:00Z"
  }
}
```

**Error Responses:**
- 400 Bad Request: Invalid request format or validation error
- 401 Unauthorized: Authentication required
- 403 Forbidden: Insufficient permissions to update this interaction
- 404 Not Found: Interaction not found

### Delete Interaction

Delete an interaction.

**Endpoint:** `DELETE /api/interactions/{id}`

**Request Headers:**
```
Authorization: Bearer <token>
```

**Response: (200 OK)**
```json
{
  "success": true
}
```

**Error Responses:**
- 401 Unauthorized: Authentication required
- 403 Forbidden: Insufficient permissions to delete this interaction
- 404 Not Found: Interaction not found

## Search Endpoints

### Basic Search

Basic search with query parameters.

**Endpoint:** `GET /api/search/interactions`

**Request Headers:**
```
Authorization: Bearer <token>
```

**Query Parameters:**
- `query`: Search term
- `page` (optional): Page number for pagination (default: 1)
- `page_size` (optional): Items per page (default: 20, max: 100)

**Response: (200 OK)**
```json
{
  "results": [
    {
      "id": 1,
      "site_id": 2,
      "title": "Team Kickoff Meeting",
      "type": "Meeting",
      "lead": "John Smith",
      "start_datetime": "2023-06-12T10:00:00Z",
      "end_datetime": "2023-06-12T11:00:00Z",
      "timezone": "America/New_York",
      "location": "Conference Room A",
      "description": "Initial project kickoff meeting with team members",
      "notes": "Bring project documentation",
      "created_by": 123,
      "created_at": "2023-06-01T15:30:00Z",
      "updated_at": "2023-06-01T15:30:00Z"
    }
  ],
  "total": 5,
  "page": 1
}
```

**Error Responses:**
- 400 Bad Request: Invalid search parameters
- 401 Unauthorized: Authentication required

### Advanced Search

Advanced search with complex filtering and sorting.

**Endpoint:** `POST /api/search/advanced`

**Request Headers:**
```
Authorization: Bearer <token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "filters": [
    {
      "field": "type",
      "operator": "eq",
      "value": "Meeting"
    },
    {
      "field": "start_datetime",
      "operator": "gte",
      "value": "2023-06-01T00:00:00Z"
    },
    {
      "field": "lead",
      "operator": "contains",
      "value": "Smith"
    }
  ],
  "sort": {
    "field": "start_datetime",
    "direction": "asc"
  },
  "page": 1,
  "size": 20
}
```

**Response: (200 OK)**
```json
{
  "results": [
    {
      "id": 1,
      "site_id": 2,
      "title": "Team Kickoff Meeting",
      "type": "Meeting",
      "lead": "John Smith",
      "start_datetime": "2023-06-12T10:00:00Z",
      "end_datetime": "2023-06-12T11:00:00Z",
      "timezone": "America/New_York",
      "location": "Conference Room A",
      "description": "Initial project kickoff meeting with team members",
      "notes": "Bring project documentation",
      "created_by": 123,
      "created_at": "2023-06-01T15:30:00Z",
      "updated_at": "2023-06-01T15:30:00Z"
    }
  ],
  "total": 3,
  "page": 1
}
```

**Error Responses:**
- 400 Bad Request: Invalid search parameters
- 401 Unauthorized: Authentication required

### Search by Date Range

Search interactions by date range.

**Endpoint:** `GET /api/search/date-range`

**Request Headers:**
```
Authorization: Bearer <token>
```

**Query Parameters:**
- `start_date`: Start date in ISO format (e.g., "2023-06-01")
- `end_date`: End date in ISO format (e.g., "2023-06-30")
- `page` (optional): Page number for pagination (default: 1)
- `page_size` (optional): Items per page (default: 20, max: 100)

**Response: (200 OK)**
```json
{
  "results": [
    {
      "id": 1,
      "site_id": 2,
      "title": "Team Kickoff Meeting",
      "type": "Meeting",
      "lead": "John Smith",
      "start_datetime": "2023-06-12T10:00:00Z",
      "end_datetime": "2023-06-12T11:00:00Z",
      "timezone": "America/New_York",
      "location": "Conference Room A",
      "description": "Initial project kickoff meeting with team members",
      "notes": "Bring project documentation",
      "created_by": 123,
      "created_at": "2023-06-01T15:30:00Z",
      "updated_at": "2023-06-01T15:30:00Z"
    }
  ],
  "total": 15,
  "page": 1
}
```

**Error Responses:**
- 400 Bad Request: Invalid date format
- 401 Unauthorized: Authentication required

### Search by Type

Search interactions by type.

**Endpoint:** `GET /api/search/type/{interaction_type}`

**Request Headers:**
```
Authorization: Bearer <token>
```

**Path Parameters:**
- `interaction_type`: Type of interaction (e.g., "Meeting", "Call", "Email")

**Query Parameters:**
- `page` (optional): Page number for pagination (default: 1)
- `page_size` (optional): Items per page (default: 20, max: 100)

**Response: (200 OK)**
```json
{
  "results": [
    {
      "id": 1,
      "site_id": 2,
      "title": "Team Kickoff Meeting",
      "type": "Meeting",
      "lead": "John Smith",
      "start_datetime": "2023-06-12T10:00:00Z",
      "end_datetime": "2023-06-12T11:00:00Z",
      "timezone": "America/New_York",
      "location": "Conference Room A",
      "description": "Initial project kickoff meeting with team members",
      "notes": "Bring project documentation",
      "created_by": 123,
      "created_at": "2023-06-01T15:30:00Z",
      "updated_at": "2023-06-01T15:30:00Z"
    }
  ],
  "total": 8,
  "page": 1
}
```

**Error Responses:**
- 400 Bad Request: Invalid type
- 401 Unauthorized: Authentication required

### Search by Lead

Search interactions by lead person.

**Endpoint:** `GET /api/search/lead/{lead}`

**Request Headers:**
```
Authorization: Bearer <token>
```

**Path Parameters:**
- `lead`: Lead person's name or identifier

**Query Parameters:**
- `page` (optional): Page number for pagination (default: 1)
- `page_size` (optional): Items per page (default: 20, max: 100)

**Response: (200 OK)**
```json
{
  "results": [
    {
      "id": 1,
      "site_id": 2,
      "title": "Team Kickoff Meeting",
      "type": "Meeting",
      "lead": "John Smith",
      "start_datetime": "2023-06-12T10:00:00Z",
      "end_datetime": "2023-06-12T11:00:00Z",
      "timezone": "America/New_York",
      "location": "Conference Room A",
      "description": "Initial project kickoff meeting with team members",
      "notes": "Bring project documentation",
      "created_by": 123,
      "created_at": "2023-06-01T15:30:00Z",
      "updated_at": "2023-06-01T15:30:00Z"
    }
  ],
  "total": 6,
  "page": 1
}
```

**Error Responses:**
- 400 Bad Request: Invalid lead parameter
- 401 Unauthorized: Authentication required

### Get Upcoming Interactions

Get upcoming interactions.

**Endpoint:** `GET /api/search/upcoming`

**Request Headers:**
```
Authorization: Bearer <token>
```

**Query Parameters:**
- `limit` (optional): Number of interactions to return (default: 10, max: 50)

**Response: (200 OK)**
```json
{
  "interactions": [
    {
      "id": 3,
      "site_id": 2,
      "title": "Project Update Meeting",
      "type": "Meeting",
      "lead": "John Smith",
      "start_datetime": "2023-06-18T09:15:00Z",
      "end_datetime": "2023-06-18T10:15:00Z",
      "timezone": "America/New_York",
      "location": "East Wing Room 305",
      "description": "Weekly project status update",
      "notes": "Bring status reports",
      "created_by": 123,
      "created_at": "2023-06-10T15:30:00Z",
      "updated_at": "2023-06-10T15:30:00Z"
    }
  ]
}
```

**Error Response: (401 Unauthorized)**
```json
{
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Authentication required"
  }
}
```

### Get Recent Interactions

Get recently completed interactions.

**Endpoint:** `GET /api/search/recent`

**Request Headers:**
```
Authorization: Bearer <token>
```

**Query Parameters:**
- `limit` (optional): Number of interactions to return (default: 10, max: 50)

**Response: (200 OK)**
```json
{
  "interactions": [
    {
      "id": 2,
      "site_id": 2,
      "title": "Client Review Call",
      "type": "Call",
      "lead": "Mary Jones",
      "start_datetime": "2023-06-14T14:30:00Z",
      "end_datetime": "2023-06-14T15:30:00Z",
      "timezone": "America/New_York",
      "location": "Virtual",
      "description": "Quarterly review call with client",
      "notes": "Prepare Q2 metrics",
      "created_by": 123,
      "created_at": "2023-06-05T10:30:00Z",
      "updated_at": "2023-06-05T10:30:00Z"
    }
  ]
}
```

**Error Response: (401 Unauthorized)**
```json
{
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Authentication required"
  }
}
```

## Site Endpoints

### List All Sites

Get all sites.

**Endpoint:** `GET /api/sites`

**Request Headers:**
```
Authorization: Bearer <token>
```

**Response: (200 OK)**
```json
{
  "sites": [
    {
      "id": 1,
      "name": "Headquarters",
      "description": "Main corporate headquarters"
    },
    {
      "id": 2,
      "name": "Northwest Regional Office",
      "description": "Regional branch serving the northwest territory"
    }
  ]
}
```

**Error Response: (401 Unauthorized)**
```json
{
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Authentication required"
  }
}
```

### Get Site

Get a specific site by ID.

**Endpoint:** `GET /api/sites/{id}`

**Request Headers:**
```
Authorization: Bearer <token>
```

**Response: (200 OK)**
```json
{
  "site": {
    "id": 1,
    "name": "Headquarters",
    "description": "Main corporate headquarters"
  }
}
```

**Error Responses:**
- 401 Unauthorized: Authentication required
- 403 Forbidden: Insufficient permissions to view this site
- 404 Not Found: Site not found

### Get User's Sites

Get sites associated with the current user.

**Endpoint:** `GET /api/users/sites`

**Request Headers:**
```
Authorization: Bearer <token>
```

**Response: (200 OK)**
```json
{
  "sites": [
    {
      "id": 1,
      "name": "Headquarters",
      "description": "Main corporate headquarters"
    },
    {
      "id": 2,
      "name": "Northwest Regional Office",
      "description": "Regional branch serving the northwest territory"
    }
  ]
}
```

**Error Response: (401 Unauthorized)**
```json
{
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Authentication required"
  }
}
```

## Data Models

### User

Represents a user account in the system.

| Property | Type | Description |
|----------|------|-------------|
| id | number | Unique user identifier |
| username | string | Username for authentication |
| email | string | User email address |
| sites | number[] | IDs of sites the user has access to |

### Site

Represents an organizational site.

| Property | Type | Description |
|----------|------|-------------|
| id | number | Unique site identifier |
| name | string | Site name |
| description | string | Site description |

### Interaction

Represents an interaction record.

| Property | Type | Description |
|----------|------|-------------|
| id | number | Unique interaction identifier |
| site_id | number | Site this interaction belongs to |
| title | string | Interaction title (5-100 characters) |
| type | string | Interaction type (Meeting, Call, Email, etc.) |
| lead | string | Person leading the interaction |
| start_datetime | string | Start date and time (ISO format) |
| end_datetime | string | End date and time (ISO format) |
| timezone | string | Timezone for the interaction |
| location | string | Interaction location |
| description | string | Detailed interaction description |
| notes | string | Additional notes |
| created_by | number | User ID who created the interaction |
| created_at | string | Creation timestamp (ISO format) |
| updated_at | string | Last update timestamp (ISO format) |

### Filter

Represents a search filter specification.

| Property | Type | Description |
|----------|------|-------------|
| field | string | Field name to filter on |
| operator | string | Comparison operator (eq, neq, gt, lt, contains, etc.) |
| value | any | Value to compare against |

### Sort

Represents a sort specification.

| Property | Type | Description |
|----------|------|-------------|
| field | string | Field name to sort by |
| direction | string | Sort direction (asc, desc) |

## Pagination

List endpoints in the API support pagination through the following query parameters:

- `page`: The page number to retrieve (starting from 1)
- `page_size`: The number of items per page (default: 20, max: 100)

### Pagination Response Format

Paginated responses include the following metadata:

```json
{
  "results": [
    // Array of items
  ],
  "total": 42,  // Total number of items
  "page": 2     // Current page number
}
```

### Calculating Total Pages

To calculate the total number of pages, use the formula:

```
total_pages = Math.ceil(total / page_size)
```

## Examples

### Authentication Example (JavaScript)

```javascript
// Login and get token
async function login(username, password) {
  try {
    const response = await fetch('https://api.example.com/api/auth/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ username, password })
    });
    
    if (!response.ok) {
      throw new Error('Authentication failed');
    }
    
    const data = await response.json();
    // Store token for future requests
    localStorage.setItem('auth_token', data.token);
    return data;
  } catch (error) {
    console.error('Login error:', error);
    throw error;
  }
}

// Making authenticated requests
async function getInteractions(page = 1, pageSize = 20) {
  const token = localStorage.getItem('auth_token');
  
  if (!token) {
    throw new Error('Not authenticated');
  }
  
  try {
    const response = await fetch(
      `https://api.example.com/api/interactions?page=${page}&page_size=${pageSize}`, 
      {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      }
    );
    
    if (!response.ok) {
      throw new Error('Failed to fetch interactions');
    }
    
    return await response.json();
  } catch (error) {
    console.error('Request error:', error);
    throw error;
  }
}
```

### Creating an Interaction (Python)

```python
import requests
import json

API_BASE_URL = 'https://api.example.com/api'

def create_interaction(token, interaction_data):
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    response = requests.post(
        f'{API_BASE_URL}/interactions',
        headers=headers,
        data=json.dumps(interaction_data)
    )
    
    if response.status_code == 201:
        return response.json()
    else:
        raise Exception(f"Failed to create interaction: {response.text}")

# Example usage
token = "your_jwt_token_here"
new_interaction = {
    "title": "Client Meeting",
    "type": "Meeting",
    "lead": "Jane Smith",
    "start_datetime": "2023-07-20T13:00:00Z",
    "end_datetime": "2023-07-20T14:00:00Z",
    "timezone": "America/New_York",
    "location": "Conference Room C",
    "description": "Discuss project requirements with client",
    "notes": "Prepare presentation slides"
}

result = create_interaction(token, new_interaction)
print(f"Created interaction with ID: {result['interaction']['id']}")
```

### Advanced Search (cURL)

```bash
curl -X POST \
  https://api.example.com/api/search/advanced \
  -H 'Authorization: Bearer your_jwt_token_here' \
  -H 'Content-Type: application/json' \
  -d '{
    "filters": [
      {
        "field": "type",
        "operator": "eq",
        "value": "Meeting"
      },
      {
        "field": "start_datetime", 
        "operator": "gte",
        "value": "2023-06-01T00:00:00Z"
      }
    ],
    "sort": {
      "field": "start_datetime",
      "direction": "asc"
    },
    "page": 1,
    "size": 20
  }'
```

## Changelog

### Version 1.0.0 (2023-06-01)

- Initial API release with authentication, interaction, and search endpoints

### Version 1.1.0 (2023-07-15)

- Added upcoming and recent interactions endpoints
- Improved search performance
- Added rate limiting headers
- Fixed bug in date range search

### Version 1.2.0 (2023-08-30)

- Added advanced search endpoint
- Enhanced error messages
- Improved pagination response format
- Optimized database queries for better performance