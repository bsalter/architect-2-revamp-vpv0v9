// Import Cypress for type checking and auto-completion
import 'cypress';

// Import test fixtures for user and site data
import user from '../../fixtures/auth/user.json';
import sites from '../../fixtures/sites/sites.json';

describe('Site Selection Page', () => {
  beforeEach(() => {
    // Start from login page and authenticate
    cy.visit('/login');
    cy.login(user.username, user.password);
    
    // Intercept the sites API request and respond with multiple sites
    cy.intercept('GET', '/api/users/sites', {
      statusCode: 200,
      body: sites
    }).as('getUserSites');
    
    // Wait for the sites API request to complete
    cy.wait('@getUserSites');
  });

  it('should display the site selection screen after successful login with multiple sites', () => {
    // Verify redirection to site selection page
    cy.url().should('include', '/auth/select-site');
    
    // Verify page title and content
    cy.get('h1').should('contain', 'Select a Site');
    cy.get('.site-selection-component').should('be.visible');
    cy.get('.selection-instructions').should('contain', 'Please select which site you want to access');
    
    // Verify header contains user information
    cy.get('.user-info').should('contain', user.username);
  });

  it('should display all available sites for the user', () => {
    // Verify all sites are displayed with correct information
    sites.forEach(site => {
      cy.get('.site-list').within(() => {
        cy.get(`.site-option[data-site-id="${site.id}"]`).should('exist');
        cy.get(`.site-option[data-site-id="${site.id}"] .site-name`).should('contain', site.name);
        cy.get(`.site-option[data-site-id="${site.id}"] .site-description`).should('contain', site.description);
      });
    });
    
    // Also verify dropdown if it exists as an alternative selection method
    cy.get('body').then($body => {
      if ($body.find('.site-dropdown').length > 0) {
        cy.get('.site-dropdown').click();
        sites.forEach(site => {
          cy.get('.site-dropdown-option').should('contain', site.name);
        });
      }
    });
  });

  it('should allow selecting a site and navigating to the interactions page', () => {
    // Select a site
    const selectedSite = sites[0];
    cy.get(`.site-option[data-site-id="${selectedSite.id}"] input[type="radio"]`).check();
    
    // Intercept the site selection API request
    cy.intercept('POST', '/api/auth/site-selection', {
      statusCode: 200,
      body: { success: true, siteId: selectedSite.id }
    }).as('siteSelection');
    
    // Click continue button
    cy.get('button[type="submit"]').contains('Continue').click();
    
    // Verify the request contains the selected site ID
    cy.wait('@siteSelection').its('request.body').should('deep.include', {
      siteId: selectedSite.id
    });
    
    // Verify redirection to interactions page
    cy.url().should('include', '/interactions');
    
    // Verify site context is set correctly in local storage
    cy.window().then(win => {
      const storedContext = JSON.parse(win.localStorage.getItem('siteContext') || '{}');
      expect(storedContext.siteId).to.equal(selectedSite.id);
      expect(storedContext.siteName).to.equal(selectedSite.name);
    });
    
    // Verify site name is displayed in the header
    cy.get('.current-site').should('contain', selectedSite.name);
  });

  it('should display validation error when trying to continue without selecting a site', () => {
    // Ensure no site is selected (clear any default selection)
    cy.get('.site-option input[type="radio"]').should('not.be.checked');
    
    // Try to continue without selecting a site
    cy.get('button[type="submit"]').contains('Continue').click();
    
    // Verify error message is displayed
    cy.get('.error-message').should('be.visible');
    cy.get('.error-message').should('contain', 'Please select a site to continue');
    
    // Verify user remains on the site selection page
    cy.url().should('include', '/auth/select-site');
  });

  it('should handle API errors during site selection gracefully', () => {
    // Select a site
    const selectedSite = sites[0];
    cy.get(`.site-option[data-site-id="${selectedSite.id}"] input[type="radio"]`).check();
    
    // Intercept with server error
    cy.intercept('POST', '/api/auth/site-selection', {
      statusCode: 500,
      body: { error: 'Internal Server Error' }
    }).as('siteSelectionError');
    
    // Click continue button
    cy.get('button[type="submit"]').contains('Continue').click();
    
    // Wait for the error response
    cy.wait('@siteSelectionError');
    
    // Verify error message is displayed
    cy.get('.alert-error').should('be.visible');
    cy.get('.alert-error').should('contain', 'An error occurred while selecting the site');
    
    // Verify user remains on the site selection page
    cy.url().should('include', '/auth/select-site');
    
    // Verify the form is still usable (can select different site)
    cy.get(`.site-option[data-site-id="${sites[1].id}"] input[type="radio"]`).check().should('be.checked');
  });

  it('should remember the last selected site for future sessions', () => {
    // Select a site using the custom command
    const selectedSite = sites[0];
    cy.selectSite(selectedSite.id);
    
    // Verify redirection to interactions page
    cy.url().should('include', '/interactions');
    
    // Log out
    cy.logout();
    
    // Log back in with same user
    cy.visit('/login');
    cy.login(user.username, user.password);
    
    // Intercept sites API to ensure we still have multiple sites available
    cy.intercept('GET', '/api/users/sites', {
      statusCode: 200,
      body: sites
    }).as('getUserSites');
    
    // Verify direct redirection to interactions page (bypass site selection)
    cy.url().should('include', '/interactions', { timeout: 10000 });
    
    // Verify stored site ID matches previously selected site
    cy.checkCurrentSite(selectedSite.id);
    
    // Verify the site name appears in the header
    cy.get('.current-site').should('contain', selectedSite.name);
  });

  it('should allow canceling site selection and redirecting to logout', () => {
    // Check for and click the cancel button
    cy.get('button').contains('Cancel').click();
    
    // Verify redirection to login page
    cy.url().should('include', '/login');
    
    // Verify authentication tokens are cleared
    cy.window().then(win => {
      expect(win.localStorage.getItem('token')).to.be.null;
      expect(win.localStorage.getItem('siteContext')).to.be.null;
    });
    
    // Verify we're fully logged out by checking login form is visible
    cy.get('form.login-form').should('be.visible');
  });

  it('should handle sites with different user roles appropriately', () => {
    // Find and verify site roles are displayed correctly
    user.sites.forEach(userSite => {
      const matchingSite = sites.find(s => s.id === userSite.id);
      if (matchingSite) {
        cy.get(`.site-option[data-site-id="${userSite.id}"] .site-role`)
          .should('contain', userSite.role.replace('_', ' '));
      }
    });
    
    // Select a site with admin role
    const adminSite = user.sites.find(site => site.role === 'SITE_ADMIN');
    if (adminSite) {
      cy.get(`.site-option[data-site-id="${adminSite.id}"] input[type="radio"]`).check();
      
      // Intercept the site selection API request
      cy.intercept('POST', '/api/auth/site-selection', {
        statusCode: 200,
        body: { success: true, siteId: adminSite.id, role: adminSite.role }
      }).as('siteSelection');
      
      // Click continue button
      cy.get('button[type="submit"]').contains('Continue').click();
      
      // Wait for site selection to complete
      cy.wait('@siteSelection');
      
      // Verify redirection to interactions page
      cy.url().should('include', '/interactions');
      
      // Verify admin-specific UI elements are visible based on role
      cy.get('.admin-controls').should('be.visible');
      cy.get('.site-management').should('be.visible');
    }
  });
});

describe('Direct Access Behavior', () => {
  it('should bypass site selection when user has only one site', () => {
    // Visit login page
    cy.visit('/login');
    
    // Login
    cy.login(user.username, user.password);
    
    // Intercept the sites API request with single site
    cy.intercept('GET', '/api/users/sites', {
      statusCode: 200,
      body: [sites[0]]
    }).as('getUserSingleSite');
    
    // Wait for the sites API request to complete
    cy.wait('@getUserSingleSite');
    
    // Verify direct redirection to interactions page (no site selection screen)
    cy.url().should('include', '/interactions', { timeout: 10000 });
    
    // Verify site context is set correctly to the only available site
    cy.window().then(win => {
      const storedContext = JSON.parse(win.localStorage.getItem('siteContext') || '{}');
      expect(storedContext.siteId).to.equal(sites[0].id);
      expect(storedContext.siteName).to.equal(sites[0].name);
    });
    
    // Verify interactions are loaded with site context
    cy.intercept('GET', '/api/interactions*', request => {
      expect(request.url).to.include(`siteId=${sites[0].id}`);
    }).as('getInteractions');
    
    // Wait for interactions to load
    cy.wait('@getInteractions');
  });

  it('should redirect to site selection when accessing protected routes without site selection', () => {
    // Login with user having multiple sites
    cy.visit('/login');
    cy.login(user.username, user.password);
    
    // Intercept the sites API request
    cy.intercept('GET', '/api/users/sites', { 
      statusCode: 200, 
      body: sites 
    }).as('getUserSites');
    cy.wait('@getUserSites');
    
    // Verify redirection to site selection page
    cy.url().should('include', '/auth/select-site');
    
    // Manually clear site selection from storage
    cy.window().then(win => {
      win.localStorage.removeItem('siteContext');
    });
    
    // Attempt to visit a protected route
    cy.visit('/interactions');
    
    // Verify redirection to site selection page
    cy.url().should('include', '/auth/select-site');
    
    // Select a site and continue
    const selectedSite = sites[0];
    cy.selectSite(selectedSite.id);
    
    // Verify redirection back to originally requested route
    cy.url().should('include', '/interactions');
    
    // Verify site context is properly set
    cy.get('.current-site').should('contain', selectedSite.name);
  });

  it('should redirect to login when accessing site selection page while unauthenticated', () => {
    // Ensure user is not authenticated by clearing local storage
    cy.clearLocalStorage();
    
    // Attempt to directly access the site selection page
    cy.visit('/auth/select-site');
    
    // Verify redirection to login page
    cy.url().should('include', '/login');
    
    // Login with valid credentials
    cy.login(user.username, user.password);
    
    // Intercept the sites API request
    cy.intercept('GET', '/api/users/sites', { 
      statusCode: 200, 
      body: sites 
    }).as('getUserSites');
    cy.wait('@getUserSites');
    
    // Verify redirection back to site selection page if multiple sites available
    cy.url().should('include', '/auth/select-site');
  });
});