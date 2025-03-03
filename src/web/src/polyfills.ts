/**
 * This file includes polyfills needed by Angular and is loaded before the app.
 * You can add your own extra polyfills to this file.
 * 
 * This file is divided into 2 sections:
 *   1. Browser polyfills. These are applied before loading Zone.js.
 *      These polyfills are required for the application to function correctly in all target browsers.
 *   2. Application imports. Files imported after Zone.js that should be loaded before your main
 *      file.
 *
 * The current setup supports:
 *   - Chrome (latest 2 versions)
 *   - Firefox (latest 2 versions)
 *   - Safari (latest 2 versions)
 *   - Edge (latest 2 versions)
 *   - Mobile browsers: iOS Safari, Android Chrome
 * 
 * See Technical Specifications section 6.6.4 for browser testing requirements.
 */

/***************************************************************************************************
 * BROWSER POLYFILLS
 */

/**
 * By default, zone.js will patch all possible macroTask and DomEvents
 * user can disable parts of macroTask/DomEvents patch by setting following flags
 */
// (window as any).__Zone_disable_requestAnimationFrame = true; // disable patch requestAnimationFrame
// (window as any).__Zone_disable_on_property = true; // disable patch onProperty such as onclick
// (window as any).__Zone_disable_geolocation = true; // disable patch geolocation

/**
 * IE11 requires all of the following polyfills.
 * Note: The Interaction Management System does not target IE11 as a supported browser.
 * These polyfills are included for reference but commented out.
 */
// import 'core-js/es/symbol';
// import 'core-js/es/object';
// import 'core-js/es/function';
// import 'core-js/es/parse-int';
// import 'core-js/es/parse-float';
// import 'core-js/es/number';
// import 'core-js/es/math';
// import 'core-js/es/string';
// import 'core-js/es/date';
// import 'core-js/es/array';
// import 'core-js/es/regexp';
// import 'core-js/es/map';
// import 'core-js/es/weak-map';
// import 'core-js/es/set';

/**
 * Safari and Firefox-specific polyfills
 * Uncomment if browser-specific issues are encountered
 */
// Safari 10 support for Web Animations API
// import 'web-animations-js';  // version 2.3.2

// Firefox support for Intl API if needed
// import '@angular/localize/init';  // version from Angular package

/**
 * Mobile browser support
 * Polyfills for specific mobile browser compatibility issues
 */
// Uncomment for better touch event handling if needed
// import 'hammerjs';  // version 2.0.8

/**
 * Required for Angular - load Zone.js
 * Zone.js is loaded before the application and is required for Angular's change detection mechanism
 */
import 'zone.js';  // version 0.13.1

/***************************************************************************************************
 * APPLICATION IMPORTS
 */

/**
 * Additional polyfills can be added here as application requirements evolve
 * or if new browser compatibility issues are encountered during browser testing.
 * 
 * Examples:
 * - smoothscroll polyfill
 * - IntersectionObserver polyfill
 * - ResizeObserver polyfill
 */
// import 'smoothscroll-polyfill';  // version 0.4.4
// import 'intersection-observer';  // version 0.12.2
// import 'resize-observer-polyfill';  // version 1.5.1

/**
 * Performance improvements
 * Uncomment these imports if specific performance optimizations are needed
 */
// import 'requestidlecallback-polyfill';  // version 1.0.2