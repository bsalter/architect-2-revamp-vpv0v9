/**
 * Staging environment configuration for the Interaction Management System
 * 
 * This configuration file provides environment-specific settings for the 
 * staging deployment, including API endpoints, authentication settings,
 * caching configuration, logging parameters, and feature flags.
 * 
 * @version 1.0.0
 */

export const environment = {
  // Indicates this is not a production environment
  production: false,
  
  // Base URL for API requests to the staging backend
  apiUrl: 'https://staging-api.interaction-manager.com/api',
  
  // Auth0 authentication configuration for staging environment
  auth: {
    domain: 'staging-interaction-manager.auth0.com',
    clientId: 'staging-client-id',
    audience: 'https://interaction-api/',
    redirectUri: 'https://staging.interaction-manager.com/callback',
    logoutRedirectUri: 'https://staging.interaction-manager.com/login',
    scope: 'openid profile email'
  },
  
  // Caching strategy configuration
  caching: {
    // Master switch to enable/disable caching
    enabled: true,
    // Default TTL for cached items in seconds (5 minutes)
    defaultTtl: 300,
    // User session TTL in seconds (30 minutes)
    userSessionTtl: 1800,
    // Site access data TTL in seconds (30 minutes)
    siteCacheTtl: 1800,
    // Interactions data TTL in seconds (5 minutes)
    interactionsCacheTtl: 300,
    // Search results TTL in seconds (2 minutes)
    searchResultsCacheTtl: 120
  },
  
  // Logging configuration
  logging: {
    // Log level (debug, info, warn, error)
    level: 'info',
    // Enable logging to browser console
    enableConsoleLogging: true,
    // Enable sending logs to remote endpoint
    enableRemoteLogging: true,
    // Remote logging service endpoint
    remoteLoggingEndpoint: 'https://logging.staging.interaction-manager.com/api/logs',
    // Enable performance monitoring
    performanceMonitoring: true,
    // Enable error tracking
    errorTracking: true
  },
  
  // Feature flags to enable/disable specific functionality
  featureFlags: {
    // Enable multi-factor authentication
    enableMfa: true,
    // Enable advanced search functionality
    enableAdvancedSearch: true,
    // Show debug information in UI (staging only)
    showDebugInfo: true
  }
};