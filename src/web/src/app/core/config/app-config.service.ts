import { Injectable } from '@angular/core'; // @angular/core version 16.2.0
import { environment } from 'src/environments/environment'; // environment.ts version N/A
import { AppConfig } from './app-config.model';

/**
 * Service that provides centralized access to application configuration settings.
 * Loads environment-specific configuration and exposes methods to retrieve
 * various application settings such as API URLs, authentication parameters,
 * feature flags, and caching configurations.
 */
@Injectable({
  providedIn: 'root'
})
export class AppConfigService {
  /**
   * The application configuration object
   * @private
   */
  private config: AppConfig;

  /**
   * Flag indicating whether the service has been initialized
   * @private
   */
  private initialized: boolean = false;

  /**
   * Creates an instance of AppConfigService.
   * Initializes the configuration service with environment settings.
   */
  constructor() {
    // Load configuration from environment
    this.config = environment as unknown as AppConfig;
    this.initialized = true;

    // Log configuration in development mode
    if (!this.config.production) {
      console.log('App configuration loaded:', this.config);
    }
  }

  /**
   * Returns the complete application configuration
   * @returns The complete application configuration
   */
  getConfig(): AppConfig {
    return this.config;
  }

  /**
   * Returns the base API URL for the application
   * @returns The base API URL
   */
  getApiUrl(): string {
    return this.config.apiUrl;
  }

  /**
   * Returns the Auth0 authentication configuration
   * @returns The Auth0 configuration
   */
  getAuthConfig(): AppConfig['auth'] {
    return this.config.auth;
  }

  /**
   * Returns the caching configuration
   * @returns The caching configuration
   */
  getCachingConfig(): AppConfig['caching'] {
    return this.config.caching;
  }

  /**
   * Returns the feature flag configuration
   * @returns The feature flags configuration
   */
  getFeatureFlags(): AppConfig['featureFlags'] {
    return this.config.featureFlags;
  }

  /**
   * Checks if a specific feature is enabled
   * @param featureName The name of the feature to check
   * @returns True if the feature is enabled, false otherwise
   */
  isFeatureEnabled(featureName: string): boolean {
    const featureFlags = this.config.featureFlags;
    return featureFlags && featureFlags[featureName] === true;
  }

  /**
   * Returns the logging configuration
   * @returns The logging configuration
   */
  getLoggingConfig(): AppConfig['logging'] {
    return this.config.logging;
  }

  /**
   * Checks if the application is running in production mode
   * @returns True if in production mode, false otherwise
   */
  isProduction(): boolean {
    return this.config.production;
  }
}