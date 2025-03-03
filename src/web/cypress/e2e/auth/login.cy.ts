// Cypress E2E tests for authentication functionality
// cypress version: 12.17.3

import { username, password, email, sites } from '../../fixtures/auth/user.json';

describe('Login Page', () => {
  it('should display the login form with correct elements', () => {
    cy.visit('/auth/login');
    cy.title().should('include', 'Interaction Management');
    cy.get('[data-testid="username-field"]').should('exist');
    cy.get('[data-testid="password-field"]').should('exist');
    cy.get('[data-testid="remember-me"]').should('exist');
    cy.get('[data-testid="forgot-password"]').should('exist');
    cy.get('[data-testid="sign-in-button"]').should('exist');
  });

  it('should validate input fields', () => {
    cy.visit('/auth/login');
    // Test submission without entering credentials
    cy.get('[data-testid="sign-in-button"]').click();
    cy.get('[data-testid="username-error"]').should('be.visible');
    cy.get('[data-testid="password-error"]').should('be.visible');
    
    // Test invalid email format
    cy.get('[data-testid="username-field"]').type('invalid-email');
    cy.get('[data-testid="username-error"]').should('contain', 'valid email');
    
    // Test short password
    cy.get('[data-testid="password-field"]').type('short');
    cy.get('[data-testid="password-error"]').should('contain', 'minimum length');
  });

  it('should display error message for invalid credentials', () => {
    cy.visit('/auth/login');
    cy.get('[data-testid="username-field"]').type('wrong@example.com');
    cy.get('[data-testid="password-field"]').type('WrongPassword123!');
    
    // Mock failed authentication response
    cy.intercept('POST', '/api/auth/login', {
      statusCode: 401,
      body: {
        error: 'Invalid credentials'
      }
    }).as('loginAttempt');
    
    cy.get('[data-testid="sign-in-button"]').click();
    cy.wait('@loginAttempt');
    cy.get('[data-testid="auth-error"]').should('be.visible');
    cy.get('[data-testid="auth-error"]').should('contain', 'Invalid credentials');
  });

  it('should successfully login with valid credentials', () => {
    cy.visit('/auth/login');
    cy.get('[data-testid="username-field"]').type(username);
    cy.get('[data-testid="password-field"]').type(password);
    
    // Mock successful authentication response
    cy.intercept('POST', '/api/auth/login', {
      statusCode: 200,
      body: {
        access_token: 'eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwiaXNzIjoiaW50ZXJhY3Rpb24tbWFuYWdlciIsImlhdCI6MTY4OTQxMjY1MiwiZXhwIjoxNjg5NDE0NDUyLCJzaXRlcyI6WzEsMiwzLDRdLCJuYW1lIjoiVGVzdCBVc2VyIiwiZW1haWwiOiJ0ZXN0dXNlckBleGFtcGxlLmNvbSJ9.signature',
        token_type: 'Bearer',
        expires_in: 1800,
        refresh_token: 'eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwiaXNzIjoiaW50ZXJhY3Rpb24tbWFuYWdlciIsImlhdCI6MTY4OTQxMjY1MiwiZXhwIjoxNjkwMDE3NDUyLCJ0eXBlIjoicmVmcmVzaCJ9.signature'
      }
    }).as('loginSuccess');
    
    // Mock site access data
    cy.intercept('GET', '/api/users/sites', {
      statusCode: 200,
      body: sites
    }).as('getSites');
    
    cy.get('[data-testid="sign-in-button"]').click();
    cy.wait('@loginSuccess');
    cy.wait('@getSites');
    
    // Check for appropriate redirection after login
    cy.url().should('not.include', '/auth/login');
  });

  it('should redirect to site selection when user has multiple sites', () => {
    // Use custom login command
    cy.login();
    
    // Mock site access data with multiple sites
    cy.intercept('GET', '/api/users/sites', {
      statusCode: 200,
      body: sites // Multiple sites from fixture
    }).as('getSites');
    
    cy.wait('@getSites');
    cy.url().should('include', '/auth/select-site');
  });

  it('should redirect to finder when user has only one site', () => {
    // Create a single-site array from fixture data
    const singleSite = [sites[0]];
    
    // Mock site access data with single site
    cy.intercept('GET', '/api/users/sites', {
      statusCode: 200,
      body: singleSite
    }).as('getSingleSite');
    
    cy.login();
    cy.wait('@getSingleSite');
    cy.url().should('include', '/interactions');
  });

  it("should remember user preferences with 'Remember me' option", () => {
    cy.visit('/auth/login');
    cy.get('[data-testid="username-field"]').type(username);
    cy.get('[data-testid="password-field"]').type(password);
    cy.get('[data-testid="remember-me"]').check();
    
    // Mock successful authentication response
    cy.intercept('POST', '/api/auth/login', {
      statusCode: 200,
      body: {
        access_token: 'eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwiaXNzIjoiaW50ZXJhY3Rpb24tbWFuYWdlciIsImlhdCI6MTY4OTQxMjY1MiwiZXhwIjoxNjg5NDE0NDUyLCJzaXRlcyI6WzEsMiwzLDRdLCJuYW1lIjoiVGVzdCBVc2VyIiwiZW1haWwiOiJ0ZXN0dXNlckBleGFtcGxlLmNvbSJ9.signature',
        token_type: 'Bearer',
        expires_in: 1800,
        refresh_token: 'eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwiaXNzIjoiaW50ZXJhY3Rpb24tbWFuYWdlciIsImlhdCI6MTY4OTQxMjY1MiwiZXhwIjoxNjkwMDE3NDUyLCJ0eXBlIjoicmVmcmVzaCJ9.signature'
      }
    }).as('loginSuccess');
    
    cy.get('[data-testid="sign-in-button"]').click();
    cy.wait('@loginSuccess');
    
    // Check local storage for persistent token
    cy.window().then((window) => {
      const storedToken = window.localStorage.getItem('auth_token');
      expect(storedToken).to.not.be.null;
      
      // Verify token has correct expiration (7 days instead of default 30 minutes)
      const tokenData = JSON.parse(storedToken || '{}');
      expect(tokenData.expires).to.be.greaterThan(Date.now() + (24 * 60 * 60 * 1000)); // Greater than 1 day
    });
    
    // Simulate new session
    cy.clearCookies();
    cy.visit('/auth/login');
    
    // Should still be authenticated
    cy.checkAuthState().should('eq', true);
  });

  it('should handle forgot password functionality', () => {
    cy.visit('/auth/login');
    cy.get('[data-testid="forgot-password"]').click();
    
    // Verify forgot password dialog appears
    cy.get('[data-testid="forgot-password-dialog"]').should('be.visible');
    cy.get('[data-testid="forgot-password-email"]').type(email);
    
    // Mock password reset API call
    cy.intercept('POST', '/api/auth/password/reset', {
      statusCode: 200,
      body: {
        success: true,
        message: 'Password reset email sent'
      }
    }).as('resetPassword');
    
    cy.get('[data-testid="forgot-password-submit"]').click();
    cy.wait('@resetPassword');
    cy.get('[data-testid="success-message"]').should('be.visible');
    cy.get('[data-testid="success-message"]').should('contain', 'Password reset email sent');
  });
});

describe('Auth Redirects', () => {
  it('should redirect to login page when accessing protected routes while unauthenticated', () => {
    // Clear any existing auth state
    cy.clearLocalStorage();
    
    // Attempt to access protected route
    cy.visit('/interactions');
    
    // Verify redirect to login with return URL parameter
    cy.url().should('include', '/auth/login');
    cy.url().should('include', 'returnUrl=%2Finteractions');
  });

  it('should redirect to last attempted route after successful login', () => {
    // Clear any existing auth state
    cy.clearLocalStorage();
    
    // Attempt to access protected route
    cy.visit('/interactions');
    cy.url().should('include', '/auth/login');
    
    // Login with valid credentials
    cy.get('[data-testid="username-field"]').type(username);
    cy.get('[data-testid="password-field"]').type(password);
    
    // Mock successful authentication
    cy.intercept('POST', '/api/auth/login', {
      statusCode: 200,
      body: {
        access_token: 'eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwiaXNzIjoiaW50ZXJhY3Rpb24tbWFuYWdlciIsImlhdCI6MTY4OTQxMjY1MiwiZXhwIjoxNjg5NDE0NDUyLCJzaXRlcyI6WzEsMiwzLDRdLCJuYW1lIjoiVGVzdCBVc2VyIiwiZW1haWwiOiJ0ZXN0dXNlckBleGFtcGxlLmNvbSJ9.signature',
        token_type: 'Bearer',
        expires_in: 1800,
        refresh_token: 'eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwiaXNzIjoiaW50ZXJhY3Rpb24tbWFuYWdlciIsImlhdCI6MTY4OTQxMjY1MiwiZXhwIjoxNjkwMDE3NDUyLCJ0eXBlIjoicmVmcmVzaCJ9.signature'
      }
    }).as('loginSuccess');
    
    // Mock single site to avoid site selection
    cy.intercept('GET', '/api/users/sites', {
      statusCode: 200,
      body: [sites[0]]
    }).as('getSites');
    
    cy.get('[data-testid="sign-in-button"]').click();
    cy.wait('@loginSuccess');
    cy.wait('@getSites');
    
    // Verify redirect to original route
    cy.url().should('include', '/interactions');
  });

  it('should handle Auth0 callback parameters', () => {
    // Simulate Auth0 redirect callback
    cy.visit('/auth/login?code=xyz&state=123');
    
    // Mock Auth0 callback handling
    cy.intercept('POST', '/api/auth/callback', {
      statusCode: 200,
      body: {
        access_token: 'eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwiaXNzIjoiaW50ZXJhY3Rpb24tbWFuYWdlciIsImlhdCI6MTY4OTQxMjY1MiwiZXhwIjoxNjg5NDE0NDUyLCJzaXRlcyI6WzEsMiwzLDRdLCJuYW1lIjoiVGVzdCBVc2VyIiwiZW1haWwiOiJ0ZXN0dXNlckBleGFtcGxlLmNvbSJ9.signature',
        token_type: 'Bearer',
        expires_in: 1800,
        refresh_token: 'eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwiaXNzIjoiaW50ZXJhY3Rpb24tbWFuYWdlciIsImlhdCI6MTY4OTQxMjY1MiwiZXhwIjoxNjkwMDE3NDUyLCJ0eXBlIjoicmVmcmVzaCJ9.signature'
      }
    }).as('handleCallback');
    
    // Wait for callback processing
    cy.wait('@handleCallback');
    
    // Verify appropriate redirection after callback processing
    cy.url().should('not.include', '/auth/login');
  });
});

describe('Logout Functionality', () => {
  it('should successfully logout the user', () => {
    // Login first
    cy.login();
    
    // Navigate to a page with logout option
    cy.visit('/interactions');
    
    // Click on user profile menu and logout option
    cy.get('[data-testid="user-menu"]').click();
    cy.get('[data-testid="logout-option"]').click();
    
    // Mock logout API call
    cy.intercept('POST', '/api/auth/logout', {
      statusCode: 200,
      body: {
        success: true
      }
    }).as('logout');
    
    cy.wait('@logout');
    
    // Verify redirect to login page
    cy.url().should('include', '/auth/login');
    
    // Verify tokens are removed
    cy.window().then((window) => {
      const storedToken = window.localStorage.getItem('auth_token');
      expect(storedToken).to.be.null;
    });
    
    // Verify protected routes are no longer accessible
    cy.visit('/interactions');
    cy.url().should('include', '/auth/login');
  });
});