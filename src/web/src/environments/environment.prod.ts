/**
 * Production environment configuration for the Interaction Management System
 * This file contains settings that are specific to the production environment.
 * 
 * NOTE: Sensitive values like API keys and Auth0 credentials should be managed securely
 * through environment variables or a secure configuration service in a real deployment.
 */

export const environment = {
  // Flag indicating this is the production environment
  production: true,
  
  // Base URL for API requests in production
  apiUrl: 'https://api.interaction-manager.com/api',
  
  // Auth0 configuration for production authentication
  auth: {
    domain: 'interaction-manager.auth0.com',
    clientId: 'prod-client-id', // This should be injected during build process in real deployment
    audience: 'https://interaction-api/',
    redirectUri: 'https://interaction-manager.com/callback',
    logoutRedirectUri: 'https://interaction-manager.com/login',
    scope: 'openid profile email'
  },
  
  // Caching configuration for performance optimization
  // TTL values are in seconds
  caching: {
    enabled: true,
    defaultTtl: 300, // 5 minutes default TTL
    userSessionTtl: 1800, // 30 minutes for user session data
    siteCacheTtl: 1800, // 30 minutes for site access data
    interactionsCacheTtl: 300, // 5 minutes for interaction records
    searchResultsCacheTtl: 120 // 2 minutes for search results
  },
  
  // Logging configuration for production environment
  logging: {
    level: 'error', // Only log errors in production
    enableConsoleLogging: false, // Disable console logging in production
    enableRemoteLogging: true, // Enable remote logging for production monitoring
    remoteLoggingEndpoint: 'https://logging.interaction-manager.com/api/logs',
    performanceMonitoring: true, // Enable performance tracking
    errorTracking: true // Enable error tracking for quick resolution
  },
  
  // Feature flags for enabling/disabling features in production
  featureFlags: {
    enableMfa: true, // Multi-factor authentication enabled in production
    enableAdvancedSearch: true, // Advanced search functionality enabled
    showDebugInfo: false // Debug information hidden in production
  }
};