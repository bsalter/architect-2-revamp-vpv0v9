# Monitoring and Observability

## Overview

The Interaction Management System implements a comprehensive monitoring and observability approach to ensure optimal performance, reliability, and security. This document outlines the monitoring infrastructure, metrics collection, logging strategy, alerting mechanisms, and dashboards used throughout the system.

The monitoring strategy addresses several key needs:
- Real-time visibility into system health and performance
- Early detection of issues before they impact users
- Historical data for trend analysis and capacity planning
- Business insights through user behavior and feature adoption metrics
- Compliance with service level agreements (SLAs)

## Monitoring Infrastructure

The system uses AWS CloudWatch as the primary monitoring infrastructure, with additional monitoring components implemented at both application and infrastructure levels.

### Key Components

- **CloudWatch**: Core monitoring service for metrics, logs, and alarms
- **X-Ray**: Distributed tracing for request execution flow
- **Structured Logging**: Consistent JSON-formatted logs with context
- **Custom Metrics**: Application-specific metrics for business and performance tracking
- **Health Checks**: Regular validation of component availability

### Architecture Diagram

The monitoring architecture integrates with all system components to provide comprehensive visibility:

```text
+----------------+      +----------------+      +----------------+
| Client Browser |      | Web Servers    |      | API Servers    |
+-------+--------+      +-------+--------+      +-------+--------+
        |                       |                       |
        v                       v                       v
+-------+-----------------------+-----------------------+--------+
|                           Metrics                              |
|  +----------------+    +----------------+    +----------------+|
|  | User Experience|    | Application    |    | Infrastructure ||
|  | - Page Load    |    | - API Response |    | - CPU/Memory   ||
|  | - Interactions |    | - Error Rates  |    | - Network      ||
|  +----------------+    +----------------+    +----------------+|
+-------------------------------------------------------------------+
|                          CloudWatch                               |
|  +----------------+    +----------------+    +----------------+   |
|  | Metrics        |    | Logs           |    | Alarms         |   |
|  +----------------+    +----------------+    +----------------+   |
|  | Dashboards     |    | X-Ray          |    | Notifications  |   |
|  +----------------+    +----------------+    +----------------+   |
+-------------------------------------------------------------------+
              ^                  ^                   ^
              |                  |                   |
      +-------+------+    +------+-------+    +------+-------+
      | Operations   |    | Development  |    | Management   |
      | Team         |    | Team         |    | Team         |
      +--------------+    +--------------+    +--------------+
```

## Metrics Collection

The system collects metrics at multiple levels to provide comprehensive visibility into its operation.

### Infrastructure Metrics

- **Compute**: 
  - CPU utilization (average, peak)
  - Memory usage
  - Disk I/O and usage
  - Network traffic

- **Database**: 
  - Query performance (execution time, scan rates)
  - Connection count and utilization
  - Latency
  - Read/write operations
  - Replication lag

- **Cache**: 
  - Hit ratio
  - Memory usage
  - Eviction rate
  - Key expiration metrics
  - Connection count

- **Network**: 
  - Traffic volumes
  - Latency
  - Error rates
  - Connection counts
  - SSL handshake time

### Application Metrics

- **Frontend**: 
  - Page load time (total, DOM content loaded, fully loaded)
  - Component render time
  - JavaScript errors
  - API call durations from client perspective
  - Resource loading times (CSS, JS, images)

- **API**: 
  - Request count by endpoint
  - Response time (average, p95, p99)
  - Error rate by status code
  - Request size
  - Response size
  - Authentication/authorization failures

- **Auth Service**: 
  - Authentication attempts (success/failure)
  - Token validation time
  - Token refresh rate
  - JWT verification errors
  - Site access validation

- **Search Service**: 
  - Query time
  - Result count
  - Zero-result rate
  - Query complexity (filters applied)
  - Cache hits/misses for search results

### Business Metrics

- **User Engagement**: 
  - Active users (daily, weekly, monthly)
  - Session duration
  - Feature usage
  - Navigation patterns
  - User retention

- **Interaction Management**: 
  - Creation rate
  - Edit frequency
  - View count
  - Site distribution
  - Type breakdown

- **Search Effectiveness**: 
  - Search frequency
  - Refinement rate (searches modified)
  - Click-through rate on results
  - Advanced filter usage
  - Most common search terms

- **Site Utilization**: 
  - Activity per site
  - User distribution across sites
  - Cross-site access patterns
  - Peak usage periods

## Logging Strategy

The system implements a structured logging approach that ensures consistency, searchability, and proper context across all components.

### Log Levels

- **DEBUG**: Detailed troubleshooting information
  - Example: Function arguments, intermediate calculation results
  - Usage: Development environments, troubleshooting specific issues

- **INFO**: Normal operational events
  - Example: User login, interaction created, search performed
  - Usage: Track normal system operations and user activities

- **WARN**: Potential issues requiring attention
  - Example: Slow database query, API rate limit approaching
  - Usage: Highlight conditions that might lead to errors

- **ERROR**: Runtime exceptions and system failures
  - Example: Database connection failure, API errors
  - Usage: Record application failures that impact functionality

- **FATAL**: Critical failures requiring immediate action
  - Example: Unable to start application, data corruption
  - Usage: Severe conditions that prevent system operation

### Log Format

All logs are formatted as JSON with standardized fields:

```json
{
  "timestamp": "ISO-8601 datetime",
  "level": "INFO|WARN|ERROR",
  "logger": "component.module",
  "message": "Human-readable message",
  "request_id": "UUID for correlation",
  "user_id": "User identifier if authenticated",
  "site_id": "Site context if available",
  "additional_context": "Operation-specific context"
}
```

Additional context fields vary by operation type but might include:
- `interaction_id`: When operations involve a specific interaction
- `search_params`: For search operations
- `execution_time_ms`: For performance tracking
- `client_ip`: For security-relevant operations (anonymized where appropriate)
- `browser_info`: For frontend errors (browser, version, OS)

### Log Storage

- **Short-term storage (30 days)**: CloudWatch Logs
  - Fast access for recent operational data
  - Query capability via CloudWatch Logs Insights
  - Integrated with alerting system

- **Long-term storage (1 year)**: S3 with lifecycle policies
  - Cost-effective storage for compliance and historical analysis
  - Exported from CloudWatch Logs on a daily basis
  - Immutable for compliance purposes

- **Structured Query**: CloudWatch Logs Insights
  - Complex query capability across multiple log streams
  - Pattern matching and aggregation features
  - Visualization of log-based metrics

### Log Masking and PII Protection

- Sensitive data is masked in logs using pattern recognition:
  - Email addresses: partially masked (user***@domain.com)
  - Personal names: logged in full as required for auditing
  - IP addresses: hashed or partially masked in non-security contexts
  - Authentication tokens: never logged in full

## Distributed Tracing

Distributed tracing provides visibility into the execution path of requests as they travel through the system components.

### Implementation

- AWS X-Ray for tracing request flow across services
- Unique trace ID propagation through all components
- Span collection for timing individual operations
- Annotations for request context

### Instrumentation Points

- **HTTP requests and responses**:
  - Request path, method, status code
  - Request duration
  - Headers (selected non-sensitive headers)

- **Database queries**:
  - Query execution time
  - Query parameters (sanitized)
  - Result count
  - Table accessed

- **Cache operations**:
  - Key accessed (hashed if sensitive)
  - Operation type (get, set, delete)
  - Cache hit/miss
  - Value size

- **External service calls**:
  - Service name
  - Endpoint
  - Response time
  - Status code

- **Background processing**:
  - Job type
  - Execution time
  - Queue time
  - Result status

### Trace Sampling Strategy

To balance observability with performance and cost:
- 100% sampling of error responses
- 100% sampling of slow responses (>2s)
- 5% sampling of normal responses
- Custom sampling rules for critical paths

## Performance Monitoring

The system continuously monitors performance metrics to ensure optimal user experience and resource utilization.

### Frontend Performance

- **PerformanceMonitoringService**: Tracks page load, component rendering, and API call times
  - Implemented in `src/web/src/app/core/monitoring/performance-monitoring.service.ts`
  - Uses Angular interceptors to track HTTP requests
  - Uses Navigation Timing API for page load metrics
  - Sends metrics to backend for aggregation

- **Browser Metrics**: Leverages Performance API for detailed browser metrics
  - First Contentful Paint (FCP)
  - Largest Contentful Paint (LCP)
  - First Input Delay (FID)
  - Cumulative Layout Shift (CLS)
  - Time to Interactive (TTI)

- **Resource Timing**: Monitors loading of scripts, styles, and images
  - Resource size
  - Load time
  - Resource type
  - Cache status

### Backend Performance

- **API Response Time**: Tracks execution time of API endpoints
  - Uses middleware to capture request duration
  - Segments time by processing phase (auth, business logic, data access)
  - Records p50, p95, and p99 percentiles

- **Database Performance**: Monitors query execution time and optimization
  - Slow query logging for queries exceeding 200ms
  - Connection pool utilization
  - Transaction duration
  - Index usage statistics

- **Service Methods**: Uses decorators and context managers to track function execution time
  - Method execution time
  - Error rate
  - Call volume
  - Memory usage

### Performance Thresholds

| Operation | Warning Threshold | Critical Threshold |
|-----------|-------------------|---------------------|
| Page Load | 3s | 5s |
| API Response | 500ms | 2s |
| Database Query | 200ms | 1s |
| Cache Response | 50ms | 200ms |
| Search Execution | 1s | 5s |

## User Activity Monitoring

User activity monitoring tracks user interactions with the system for analytics, audit, and usability improvement purposes.

### Tracked Activities

- Page views and navigation paths
- Interaction creation, editing, and deletion
- Search operations and filter usage
- Site switching
- Authentication events
- Feature usage patterns

### Implementation

- **UserActivityService**: Frontend service capturing user actions
  - Implemented in `src/web/src/app/core/monitoring/user-activity.service.ts`
  - Tracks user interactions with UI components
  - Buffers events for batched transmission
  - Ensures non-blocking user experience

- **Audit Logging**: Backend service recording security-relevant actions
  - Implemented in `src/backend/logging/audit_logger.py`
  - Records all data modification operations
  - Captures user, timestamp, action, and affected resources
  - Immutable storage for compliance

- **Activity Buffer**: Batches activities for efficient transmission
  - Buffers events in memory
  - Sends in batches every 30 seconds
  - Immediate transmission for critical events
  - Fallback local storage if network unavailable

- **Privacy Controls**: Excludes sensitive data from activity tracking
  - Configurable PII exclusion rules
  - Data minimization practices
  - Compliance with privacy regulations
  - User consent management

## Alerting and Notifications

The system implements a tiered alerting strategy to notify appropriate personnel of issues based on severity and impact.

### Alert Severity Levels

- **Critical**: System unavailable, data loss risk, severe performance degradation
  - Response SLA: 15 minutes
  - Examples: Service downtime, database failure, security breach

- **Warning**: Performance issues, rising error rates, potential capacity issues
  - Response SLA: 2 hours
  - Examples: Slow API responses, increased error rates, storage nearing capacity

- **Info**: Unusual patterns, capacity thresholds, business metrics
  - Response SLA: Next business day
  - Examples: Unusual traffic patterns, feature usage changes, performance trends

### Notification Channels

- **Critical**: PagerDuty, SMS to on-call personnel
  - 24/7 alerting with acknowledgment tracking
  - Escalation path if no acknowledgment within 15 minutes
  - Conference bridge auto-creation for collaborative troubleshooting

- **Warning**: Email, Slack channel notifications
  - Team channel notifications
  - Email to responsible team
  - Business hours monitoring

- **Info**: Dashboard indicators, daily digest emails
  - Visual indicators on operational dashboards
  - Daily summary emails
  - Weekly trend reports

### Alert Response Procedures

1. Acknowledge alert within SLA timeframe
2. Investigate using monitoring dashboards and logs
3. Follow specific runbook for the alert type
4. Resolve or escalate based on findings
5. Document in incident tracking system

### Alert Tuning Process

To minimize alert fatigue and ensure effectiveness:
- Regular review of alert frequency and actionability
- Adjustment of thresholds based on historical patterns
- Consolidation of related alerts
- Muting of alerts during maintenance windows
- Root cause analysis for recurring alerts

## Dashboards

The system provides specialized dashboards for different stakeholders to visualize relevant metrics and system health.

### Operations Dashboard

Focused on system health and operational metrics:
- System availability and response times
- Error rates and distribution
- Resource utilization (CPU, memory, disk)
- Database and cache performance

![Operations Dashboard Layout](https://placeholder-image-url/operations-dashboard.png)

Key components:
- Real-time service status indicators
- Error rate trends over time
- Resource utilization gauges
- Active alerts panel
- Performance metrics by component

### Development Dashboard

Detailed technical metrics for troubleshooting:
- API performance by endpoint
- Database query analysis
- Error distribution by component
- Deployment status and version tracking

Key components:
- Endpoint performance comparison
- Slow query analysis
- Error stack trace frequency
- Recent deployments timeline
- Log search interface

### Business Dashboard

Usage patterns and adoption metrics:
- Active users and session metrics
- Interaction volume by type and site
- Search patterns and effectiveness
- Feature adoption rates

Key components:
- User activity trends
- Interaction creation/modification rates
- Popular search terms
- Feature usage heat map
- Site activity comparison

### Executive Dashboard

High-level system performance and business impact:
- System availability and SLA compliance
- User adoption trends
- Interaction growth metrics
- Incident summary and resolution times

Key components:
- SLA compliance scorecard
- User growth trends
- System reliability metrics
- Key business metrics
- Incident resolution performance

## SLA Monitoring

The system tracks performance against defined Service Level Agreements (SLAs) to ensure it meets business requirements.

### Key SLAs

| Service Level | Metric | Target | Measurement Window |
|---------------|--------|--------|-------------------|
| Availability | System uptime | 99.9% | Monthly |
| Performance | API response time | 95% <1s | Daily |
| Reliability | Successful request rate | 99.5% | Daily |
| Data Integrity | No data loss | 100% | Continuous |

### SLA Reporting

- Daily metrics in operational dashboards
- Weekly team reviews of SLA trends
- Monthly executive reporting
- Quarterly trend analysis

### SLA Breach Handling

1. Automatic alert on SLA breach
2. Incident investigation and root cause analysis
3. Corrective action implementation
4. Post-mortem documentation
5. Preventive measures for future compliance

### SLA Calculation Methodology

- **Availability**: (Total minutes - Downtime minutes) / Total minutes × 100%
- **Performance**: Percentage of requests completing within target time
- **Reliability**: (Total requests - Failed requests) / Total requests × 100%
- **Data Integrity**: Validation of data consistency through automated checks

## Health Checks

Health checks continuously validate the operational status of all system components.

### Component Health Checks

| Component | Check Method | Frequency | Failure Action |
|-----------|--------------|-----------|----------------|
| Web/API Server | HTTP endpoint | 30 seconds | Route traffic away |
| Database | Connection test | 1 minute | Failover to replica |
| Cache | Connection test | 1 minute | Flush and restart |
| Auth Service | API verification | 2 minutes | Alert only |

### Health Check Implementation

- **Simple checks**: Basic "ping" to verify process is running
  - HTTP 200 response from /health endpoint
  - Database connection validation
  - Redis connection test

- **Deep checks**: Validation including dependency status
  - Database query execution
  - Cache get/set operation
  - Cross-service communication
  - Resource availability verification

- **Synthetic checks**: Simulated user flows
  - Login flow
  - Interaction creation
  - Search execution
  - Full page rendering

- **Results exposure**: Health metrics in CloudWatch
  - Status (0 = healthy, 1 = degraded, 2 = unhealthy)
  - Response time
  - Last check timestamp
  - Failure count

## Capacity Monitoring

The system proactively monitors resource usage to anticipate capacity needs and prevent performance issues.

### Monitored Resources

| Resource | Metrics | Warning | Action Trigger |
|----------|---------|---------|----------------|
| Database | Size, query time, connections | 70% | 85% |
| Application Servers | CPU, memory, request rate | 60% | 80% |
| Cache | Memory usage, hit ratio | 70% | 85% |
| Storage | Disk usage, growth rate | 70% | 85% |

### Capacity Planning

- Trend analysis of resource utilization
  - Daily peak usage
  - Weekly patterns
  - Monthly growth rates
  - Correlation with user activity

- Growth projection based on user adoption
  - Linear regression models
  - Seasonal adjustment
  - Event-driven spikes
  - Business forecast integration

- Seasonal usage pattern identification
  - Time-of-day patterns
  - Day-of-week patterns
  - Monthly patterns
  - Annual cycles

- Automated scaling configurations
  - Scale-out policies
  - Scale-in policies
  - Pre-warming for predicted high load
  - Resource reservation adjustments

- Regular capacity review meetings
  - Monthly capacity review
  - Quarterly planning
  - Annual infrastructure sizing

## Incident Response

The incident response process defines how to handle issues detected through monitoring.

### Response Workflow

1. Alert triggered based on monitoring thresholds
2. Alert routed to appropriate personnel based on severity
3. Initial triage and acknowledgment
4. Investigation using monitoring tools and logs
5. Resolution or escalation
6. Documentation and post-mortem

### Escalation Tiers

- **Level 1**: Primary on-call engineer
  - Initial triage and response
  - Basic recovery procedures
  - Document initial findings

- **Level 2**: Specialist technical team
  - Deep technical analysis
  - Complex recovery operations
  - Root cause identification

- **Level 3**: Engineering management
  - Resource coordination
  - Business impact assessment
  - Stakeholder communication

- **Level 4**: Executive involvement
  - Major incident coordination
  - External communication
  - Business continuity decisions

### Runbooks

Predefined procedures exist for common scenarios:

- **API performance degradation**:
  1. Verify increased response time in metrics
  2. Check database query performance
  3. Examine resource utilization
  4. Review recent deployments
  5. Scale resources if needed
  6. Optimize slow queries
  7. Implement caching if appropriate

- **Database failover**:
  1. Verify database health metrics
  2. Check replication lag
  3. Execute failover procedure
  4. Verify application connectivity
  5. Monitor performance post-failover
  6. Restore original primary when possible

- **Authentication service disruption**:
  1. Check Auth0 status
  2. Verify local token validation
  3. Implement emergency access if needed
  4. Monitor authentication success rate
  5. Communicate status to users

- **Cache failure**:
  1. Verify cache connectivity
  2. Implement fallback to database
  3. Restart cache service if needed
  4. Monitor application performance
  5. Gradually warm cache after recovery

- **Network connectivity issues**:
  1. Check AWS network status
  2. Verify security group configurations
  3. Test connectivity between components
  4. Review recent network changes
  5. Implement routing changes if needed

## Implementation Reference

### Frontend Monitoring Components

- `src/web/src/app/core/monitoring/performance-monitoring.service.ts`: Tracks frontend performance metrics
  - Page load timing
  - Component rendering time
  - API call performance
  - Error tracking

- `src/web/src/app/core/monitoring/user-activity.service.ts`: Tracks user interactions and activities
  - Feature usage
  - Navigation paths
  - Session information
  - Error encounters

- `src/web/src/app/core/monitoring/error-handler.service.ts`: Global error handling and reporting
  - JavaScript error capture
  - Contextual information collection
  - Error grouping and categorization
  - Automatic reporting

### Backend Monitoring Components

- `src/backend/logging/structured_logger.py`: Provides context-rich structured logging
  - JSON formatting
  - Request context injection
  - Log level management
  - Output configuration

- `src/backend/logging/performance_monitor.py`: Tracks backend performance metrics
  - Method timing decorators
  - Database query timing
  - External service call monitoring
  - Background job performance

- `src/backend/logging/audit_logger.py`: Records security-relevant actions
  - Authentication events
  - Data modification
  - Permission checks
  - Administrative actions

- `src/backend/monitoring/health_check.py`: Implements component health checks
  - Status endpoints
  - Dependency checking
  - Readiness probes
  - Liveness probes

### Infrastructure Configuration

- `infrastructure/monitoring/cloudwatch-dashboard.json`: Dashboard definitions
  - Operational dashboard
  - Development dashboard
  - Business metrics dashboard
  - Executive dashboard

- `infrastructure/monitoring/alerts.yml`: Alert configurations
  - Threshold definitions
  - Notification routes
  - Severity classifications
  - Evaluation periods

- `infrastructure/monitoring/log-config.yml`: Logging infrastructure setup
  - Log groups
  - Retention policies
  - Subscription filters
  - Insights queries

### Tools and Services

- AWS CloudWatch: Primary metrics and logging platform
  - Metric collection and storage
  - Log aggregation
  - Dashboard visualization
  - Alerting engine

- AWS X-Ray: Distributed tracing implementation
  - Request flow tracking
  - Service map visualization
  - Latency analysis
  - Error localization

- CloudWatch Logs: Log aggregation and analysis
  - Structured log storage
  - Log insights queries
  - Pattern-based metrics
  - Export for long-term storage

- CloudWatch Alarms: Alert generation mechanism
  - Threshold-based alerting
  - Composite alarms
  - Notification routing
  - Alert history