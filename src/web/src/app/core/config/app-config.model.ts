import { Auth0Config } from '../auth/auth0-config';

/**
 * Interface defining caching configuration parameters.
 * Controls caching behavior throughout the application including TTL values for different data types.
 * Based on the caching strategy defined in the system architecture.
 */
export interface CachingConfig {
  /** Whether caching is enabled in the application */
  enabled: boolean;
  
  /** Default time-to-live in seconds for cached items if not specified */
  defaultTtl: number;
  
  /** Time-to-live in seconds for user session data (typically 30 minutes) */
  userSessionTtl: number;
  
  /** Time-to-live in seconds for site access data (typically 30 minutes) */
  siteCacheTtl: number;
  
  /** Time-to-live in seconds for interactions data (typically 5 minutes) */
  interactionsCacheTtl: number;
  
  /** Time-to-live in seconds for search results (typically 2 minutes) */
  searchResultsCacheTtl: number;
}

/**
 * Interface defining logging configuration parameters.
 * Controls logging behavior, levels and destinations throughout the application.
 * Aligned with the monitoring infrastructure defined in the system architecture.
 */
export interface LoggingConfig {
  /** Logging level (e.g., 'ERROR', 'WARN', 'INFO', 'DEBUG') */
  level: string;
  
  /** Whether to log to browser console */
  enableConsoleLogging: boolean;
  
  /** Whether to send logs to a remote endpoint (e.g., CloudWatch) */
  enableRemoteLogging: boolean;
  
  /** URL endpoint for remote logging if enabled */
  remoteLoggingEndpoint: string;
  
  /** Whether to enable performance monitoring */
  performanceMonitoring: boolean;
  
  /** Whether to enable error tracking */
  errorTracking: boolean;
}

/**
 * Interface defining feature flags for the application.
 * Used to enable/disable features across different environments.
 * Supports requirement for gradual feature rollout and environment-specific capabilities.
 */
export interface FeatureFlags {
  /** Whether multi-factor authentication is enabled */
  enableMfa: boolean;
  
  /** Whether advanced search functionality is enabled */
  enableAdvancedSearch: boolean;
  
  /** Whether to show debugging information in the UI */
  showDebugInfo: boolean;
}

/**
 * Main application configuration interface.
 * Centralizes all configuration settings for the application across different environments.
 * This interface provides type safety for environment-specific settings used throughout the application.
 */
export interface AppConfig {
  /** Whether the application is running in production mode */
  production: boolean;
  
  /** Base URL for API requests */
  apiUrl: string;
  
  /** Authentication configuration settings for Auth0 integration */
  auth: Auth0Config;
  
  /** Caching behavior configuration */
  caching: CachingConfig;
  
  /** Logging configuration */
  logging: LoggingConfig;
  
  /** Feature flags for toggling features */
  featureFlags: FeatureFlags;
}