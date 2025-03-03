/**
 * Development environment configuration file
 * 
 * This file provides environment-specific settings for the Angular application
 * during local development and testing. The configuration in this file is used
 * when running the application with `ng serve` or `npm start`.
 * 
 * For production settings, see environment.prod.ts
 */
export const environment = {
  /**
   * Indicates whether the application is running in production mode
   * Set to false for development environment
   */
  production: false,
  
  /**
   * Base URL for API requests in development environment
   * Points to the local development API server
   */
  apiUrl: 'http://localhost:5000/api',
  
  /**
   * Authentication configuration for Auth0 integration
   * Contains development-specific Auth0 credentials and settings
   */
  auth: {
    /**
     * Auth0 domain for authentication requests
     */
    domain: 'dev-interaction-manager.auth0.com',
    
    /**
     * Client ID for the Auth0 application
     */
    clientId: 'dev-client-id',
    
    /**
     * API identifier for the backend API
     */
    audience: 'https://interaction-api/',
    
    /**
     * URL to redirect after successful authentication
     */
    redirectUri: 'http://localhost:4200/callback',
    
    /**
     * URL to redirect after logout
     */
    logoutRedirectUri: 'http://localhost:4200/login',
    
    /**
     * OAuth scopes to request during authentication
     */
    scope: 'openid profile email'
  },
  
  /**
   * Caching configuration for development environment
   * Defines caching behavior and TTL values for different data types
   * Aligns with section 6.2.2 DATA MANAGEMENT/Caching Policies
   */
  caching: {
    /**
     * Master switch to enable/disable caching
     */
    enabled: true,
    
    /**
     * Default time-to-live for cached items in seconds
     */
    defaultTtl: 300, // 5 minutes
    
    /**
     * Time-to-live for user session cache in seconds
     */
    userSessionTtl: 1800, // 30 minutes
    
    /**
     * Time-to-live for site access data in seconds
     */
    siteCacheTtl: 1800, // 30 minutes
    
    /**
     * Time-to-live for interaction list data in seconds
     */
    interactionsCacheTtl: 300, // 5 minutes
    
    /**
     * Time-to-live for search results in seconds
     */
    searchResultsCacheTtl: 120 // 2 minutes
  },
  
  /**
   * Logging configuration for development environment
   * Controls logging verbosity and destinations
   */
  logging: {
    /**
     * Logging level: 'debug', 'info', 'warn', 'error'
     */
    level: 'debug',
    
    /**
     * Enable logging to browser console
     */
    enableConsoleLogging: true,
    
    /**
     * Enable sending logs to a remote endpoint
     */
    enableRemoteLogging: false,
    
    /**
     * Remote logging service endpoint (when enabled)
     */
    remoteLoggingEndpoint: '',
    
    /**
     * Enable performance monitoring in development
     * Tracks rendering times and other performance metrics
     */
    performanceMonitoring: true,
    
    /**
     * Enable tracking and reporting of client-side errors
     */
    errorTracking: true
  },
  
  /**
   * Feature flags for development environment
   * Enables or disables specific features during development
   */
  featureFlags: {
    /**
     * Enable multi-factor authentication in development
     * When enabled, requires MFA setup for administrative users
     */
    enableMfa: false,
    
    /**
     * Enable advanced search capabilities
     * Provides complex query building and filtering options
     */
    enableAdvancedSearch: true,
    
    /**
     * Show debug information in the UI
     * Displays additional information useful during development
     */
    showDebugInfo: true
  }
};