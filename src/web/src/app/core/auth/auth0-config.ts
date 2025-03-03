import { environment } from 'src/environments/environment'; // environment.ts version N/A

/**
 * Defines the possible cache locations for Auth0 tokens
 */
export type Auth0CacheLocation = 'memory' | 'localstorage';

/**
 * Interface defining the Auth0 configuration parameters required for authentication.
 * This configuration is used to initialize the Auth0 client in the authentication service.
 * It centralizes all Auth0-related settings for the authentication system.
 */
export interface Auth0Config {
  /** Auth0 domain URL */
  domain: string;
  
  /** Auth0 client ID */
  clientId: string;
  
  /** Auth0 API audience identifier */
  audience: string;
  
  /** URI where Auth0 will redirect after successful authentication */
  redirectUri: string;
  
  /** URI where Auth0 will redirect after logout */
  logoutRedirectUri: string;
  
  /** OAuth scopes to request (e.g., 'openid profile email') */
  scope: string;
  
  /** Location to store authentication data (memory or local storage) */
  cacheLocation: Auth0CacheLocation;
  
  /** Whether to use refresh tokens for seamless token renewal */
  useRefreshTokens: boolean;
}

/**
 * Factory function that creates an Auth0Config object from environment settings.
 * This centralizes all Auth0-related configuration and allows for environment-specific
 * settings to be applied.
 * 
 * @returns {Auth0Config} Configuration object with Auth0 settings
 */
export function createAuth0Config(): Auth0Config {
  if (!environment.auth) {
    console.error('Auth0 configuration not found in environment settings');
  }
  
  // Extract Auth0 settings from environment configuration or use defaults
  const { 
    domain = '',
    clientId = '',
    audience = '',
    redirectUri = window.location.origin,
    logoutRedirectUri = window.location.origin,
    scope = 'openid profile email',
    cacheLocation = 'memory' as Auth0CacheLocation,
    useRefreshTokens = true
  } = environment.auth || {};
  
  // Validate required fields
  if (!domain) {
    console.warn('Auth0 domain is not configured');
  }
  
  if (!clientId) {
    console.warn('Auth0 clientId is not configured');
  }

  // Create and return Auth0Config object with all required properties
  return {
    domain,
    clientId,
    audience,
    // Ensure redirectUri is properly formatted
    redirectUri: redirectUri || window.location.origin,
    // Ensure logoutRedirectUri is properly formatted
    logoutRedirectUri: logoutRedirectUri || window.location.origin,
    scope,
    cacheLocation: (cacheLocation as Auth0CacheLocation) || 'memory',
    useRefreshTokens
  };
}