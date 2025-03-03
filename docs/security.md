# Security Documentation

## Introduction

This document provides comprehensive information about the security architecture, features, and best practices implemented in the Interaction Management System. It serves as a reference for developers, administrators, and security auditors.

## Table of Contents

1. [Authentication Framework](#authentication-framework)
2. [Authorization System](#authorization-system)
3. [Data Protection](#data-protection)
4. [Security Zones and Boundaries](#security-zones-and-boundaries)
5. [Threat Mitigation](#threat-mitigation)
6. [Audit and Monitoring](#audit-and-monitoring)
7. [Security Configuration](#security-configuration)
8. [Security Best Practices](#security-best-practices)
9. [References](#references)

## Authentication Framework

The system implements a robust, multi-layered authentication framework using Auth0 as the primary identity provider.

### Auth0 Integration

Integration with Auth0 provides secure authentication with support for various login methods and session management. 

**Implementation:**
- The Auth0Client class in `src/backend/auth/auth0.py` handles server-side authentication
- The AuthService in `src/web/src/app/core/auth/auth.service.ts` manages client-side authentication flows

### JWT Tokens

JSON Web Tokens (JWT) are used for maintaining authentication state with a stateless architecture.

**Implementation:**
- Tokens contain user identity and site access claims
- Verified on each API request
- Stored securely on the client side

**Token Structure:**
```json
{
  "header": {
    "alg": "RS256",
    "typ": "JWT"
  },
  "payload": {
    "sub": "<user_id>",
    "iss": "interaction-manager",
    "iat": "<timestamp>",
    "exp": "<timestamp+30min>",
    "sites": [1, 2, 3],
    "name": "User Full Name",
    "email": "user@example.com"
  },
  "signature": "..."
}
```

### Multi-factor Authentication

MFA is supported through Auth0 with various methods:

- **Time-based OTP**: Required for administrators, optional for standard users
- **SMS verification**: Optional for all users
- **Email verification**: Required for initial login

### Session Management

The system implements secure session management with appropriate timeouts and refresh mechanisms.

| Property | Value | Purpose |
|----------|-------|---------|
| Token Lifetime | 30 minutes | Limited validity period for security |
| Refresh Token | 7 days | Allow reasonable period for return users |
| Idle Timeout | 15 minutes | Security for inactive sessions |
| Concurrent Sessions | Allowed | Support for multiple devices |

### Password Policies

Enforced through Auth0 settings to ensure strong password security:

- **Minimum Length**: 10 characters
- **Complexity**: Upper, lower, number, and special characters required
- **History**: No reuse of last 5 passwords
- **Expiration**: 90 days
- **Failed Attempts**: 5 maximum before temporary lockout

## Authorization System

A multi-layered authorization model centered around site-scoping and role-based permissions.

### Role-Based Access Control

Defines roles with different permission levels for controlling access to resources.

| Role | Description |
|------|-------------|
| Site Admin | Full access to site data and user management |
| Editor | Create, read, and update interactions |
| Viewer | Read-only access to interactions |
| System Admin | Cross-site access and system settings management |

The role hierarchy follows the principle of least privilege:
- Each role inherits permissions from lower roles
- Site-specific roles apply only within site boundaries
- System-wide roles have defined scope limitations

### Site-Scoping

Core authorization mechanism that restricts users to accessing only data from their authorized sites.

**Implementation:**
The SiteContextMiddleware (`src/backend/api/middleware/site_context_middleware.py`) establishes and validates site context for every request. Site context is extracted from request parameters, headers, or JSON body and validated against user's site access permissions.

### Permission Management

Hierarchical permission system with multiple levels of access control:

1. **System Level** - Global permissions
2. **Site Level** - Site-specific permissions
3. **Resource Level** - Permissions for specific resources
4. **Field Level** - Control access to specific fields within resources

### Resource Authorization

Resource-level authorization enforced through multiple mechanisms:

- **Site-scoping**: All resources belong to a site
- **Ownership concept**: Resources have creators/owners with elevated permissions
- **Action-based checks**: Different permissions for view/edit/delete operations
- **Context-aware rules**: Time-based or status-based permission adjustments

### Policy Enforcement Points

Authorization checks occur at multiple layers for defense-in-depth:

1. **API Gateway**: Token validation, basic authorization
2. **Controllers**: Resource-specific permission checks
3. **Services**: Business rule validation
4. **Data Layer**: Automatic site-scoping of queries
5. **Frontend**: UI element visibility based on permissions

## Data Protection

Comprehensive data protection measures are implemented to ensure confidentiality, integrity, and privacy.

### Encryption Standards

Multiple encryption layers protect data in different states:

| Data State | Encryption Method | Key Strength |
|------------|-------------------|--------------|
| Data in Transit | TLS 1.2+ | 256-bit |
| Data at Rest (Database) | AES-256 | 256-bit |
| Data at Rest (Backups) | AES-256 | 256-bit |
| Sensitive Fields | Column-level encryption | 256-bit |

### Input Validation and Sanitization

Protection against injection attacks and malicious input.

**Implementation:**
Comprehensive input validation is implemented in `src/backend/security/input_validation.py` to sanitize all user inputs before processing, including:

- HTML content sanitization using bleach library
- SQL injection detection patterns
- Search query sanitization
- File path sanitization to prevent path traversal
- JSON payload validation
- Security header validation

### CSRF Protection

Cross-Site Request Forgery protection for state-changing requests.

**Implementation:**
Implemented in `src/backend/security/csrf.py` with token generation, validation, and middleware components:

- Token-based protection with cryptographically secure tokens
- Automatic token injection in responses
- Validation middleware for state-changing requests
- Both header and form field support for token submission
- Exemption mechanism for specific endpoints

### Secure Communication

All communication channels are secured with appropriate protocols:

| Communication Path | Protocol | Security Controls |
|-------------------|----------|-------------------|
| Client to Web | HTTPS | TLS 1.2+, HSTS, Proper cipher suite |
| Web to API | HTTPS | Mutual TLS, API tokens |
| API to Database | TLS | Encrypted connection, certificate validation |
| API to Auth0 | HTTPS | Secure API tokens, certificate validation |
| API to Email Service | HTTPS | API keys, certificate validation |

## Security Zones and Boundaries

The application architecture implements distinct security zones with controlled boundaries.

| Security Zone | Purpose | Access Controls | Security Measures |
|---------------|---------|-----------------|-------------------|
| Public Zone | External-facing entry point | IP filtering, rate limiting | WAF, DDoS protection |
| Web Zone | Frontend application delivery | Authentication required | TLS, CSP headers |
| Application Zone | Business logic processing | Authenticated API requests | Token validation, RBAC |
| Data Zone | Data storage and processing | Service account access only | Encryption, network isolation |
| Management Zone | Administrative access | MFA, privileged access | Bastion hosts, audit logging |

### Network Security Architecture

The system implements a layered network security approach:

1. **Edge protection**: Web Application Firewall for filtering malicious traffic
2. **Network segmentation**: VPC with public and private subnets
3. **Access control lists**: Network-level traffic control
4. **Security groups**: Instance-level traffic filtering
5. **Database isolation**: Data tier in private subnets with no direct external access

## Threat Mitigation

Specific controls implemented to address common security threats.

| Threat Category | Mitigation Strategy | Implementation |
|-----------------|---------------------|----------------|
| Authentication Attacks | Brute force prevention | Rate limiting, account lockout after 5 failed attempts |
| Injection Attacks | Input validation | Parameterized queries, comprehensive input sanitization |
| Cross-site Scripting (XSS) | Output encoding | Content Security Policy headers, HTML sanitization of user input |
| Cross-site Request Forgery (CSRF) | Anti-forgery tokens | CSRF tokens required for all state-changing requests |
| Privilege Escalation | Permission enforcement | Strict RBAC, boundary validations, site context checks |
| Data Exposure | Data minimization | Field-level security, encryption, site-scoped queries |
| API Abuse | Rate limiting | Request throttling based on user and IP address |

### Defense-in-Depth Approach

The system implements multiple layers of security controls:

1. **Preventive controls**: Input validation, authentication, encryption
2. **Detective controls**: Logging, monitoring, intrusion detection
3. **Responsive controls**: Alerting, incident response procedures
4. **Recovery controls**: Backups, disaster recovery plans

## Audit and Monitoring

Comprehensive logging, monitoring, and auditing capabilities to detect and respond to security events.

### Audit Logging

Specialized audit logging system for security-relevant events.

**Implementation:**
Implemented in `src/backend/logging/audit_logger.py` to record security events with user context, timestamps, and detailed information.

| Event Category | Events Logged | Retention Period |
|----------------|---------------|------------------|
| Authentication | Login, logout, MFA, failures | 90 days |
| Authorization | Permission checks, access denials | 90 days |
| Resource Access | View, create, update, delete | 1 year |
| Admin Actions | User management, site changes | 3 years |

Each audit log entry includes:
- Timestamp with timezone
- User identifier
- Action attempted
- Resource affected
- Result of action
- IP address and user agent
- Site context identifier

### Security Monitoring

Real-time monitoring of security events for prompt detection and response.

| Security Aspect | Monitoring Method | Alert Criteria |
|-----------------|-------------------|----------------|
| Authentication | Auth0 logs, failed attempts | >5 failures in 5 minutes |
| Authorization | Access logs, permission denials | Unusual access patterns |
| Network | VPC Flow Logs, Security Groups | Unexpected traffic patterns |
| API Usage | Rate limiting metrics | Threshold breaches |

### Data Changes Tracking

Historical record of all changes to interactions for audit purposes.

**Implementation:**
Interaction history is tracked using the InteractionHistory entity, capturing all changes with the user who made them, timestamp, change type, and before/after states.

## Security Configuration

Guidelines for secure configuration of the application and its components.

### Auth0 Configuration

Settings for the Auth0 tenant used for authentication:

- Enable MFA for all administrative accounts
- Set appropriate token lifetimes (access token: 30 min, refresh token: 7 days)
- Configure secure password policies
- Enable Account Linking to prevent duplicate accounts
- Configure appropriate connections based on organizational requirements

### API Security Settings

Configuration for securing API endpoints:

- Enable rate limiting appropriate to expected traffic patterns
- Configure CORS with appropriate origins
- Enable CSRF protection for state-changing operations
- Configure security-related HTTP headers:
  - Content-Security-Policy
  - X-Content-Type-Options
  - X-Frame-Options
  - X-XSS-Protection
  - Strict-Transport-Security
- Set appropriate caching policies

### Database Security

Security settings for the PostgreSQL database:

- Enable SSL/TLS for database connections
- Implement database-level encryption
- Configure appropriate user roles and permissions
- Enable row-level security for site-scoping enforcement
- Set up audit logging for sensitive operations

## Security Best Practices

Guidelines for developers and administrators to maintain security.

### Development Practices

- Always sanitize and validate user inputs
- Use parameterized queries for database operations
- Verify authorization before accessing or modifying data
- Handle errors securely without exposing sensitive information
- Implement proper exception handling
- Keep dependencies updated to address security vulnerabilities

### Administration Practices

- Regularly review audit logs for suspicious activity
- Conduct periodic access reviews to ensure proper permissions
- Monitor security alerts and respond promptly
- Apply security patches in a timely manner
- Maintain secure backup procedures
- Implement the principle of least privilege for all accounts

### User Management

- Enforce strong password policies
- Require MFA for administrative accounts
- Promptly revoke access for departing users
- Regularly review user site access permissions
- Implement secure account recovery procedures
- Provide security awareness training for all users

## References

- [OWASP Top Ten Project](https://owasp.org/Top10/) - Industry standard awareness document for web application security
- [Auth0 Security Documentation](https://auth0.com/docs/security) - Security documentation for the Auth0 identity platform
- [PostgreSQL Security Documentation](https://www.postgresql.org/docs/current/security.html) - Security best practices for PostgreSQL databases
- [AWS Security Best Practices](https://aws.amazon.com/architecture/security-identity-compliance/) - Security guidance for AWS infrastructure