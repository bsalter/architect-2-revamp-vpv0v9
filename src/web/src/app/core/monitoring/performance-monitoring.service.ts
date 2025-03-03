import { Injectable, Inject, Optional } from '@angular/core'; // @angular/core version 16.2.0
import { Router, NavigationStart, NavigationEnd } from '@angular/router'; // @angular/router version 16.2.0
import { filter } from 'rxjs/operators'; // rxjs/operators version 7.8.1
import { Observable, of } from 'rxjs'; // rxjs version 7.8.1
import { catchError, tap } from 'rxjs/operators'; // rxjs/operators version 7.8.1
import { AppConfigService } from '../config/app-config.service';
import { formatDate } from '../utils/datetime-utils';
import { environment } from '../../../environments/environment';

/**
 * Global performance threshold constants defining warning and critical levels
 * for various performance metrics. These align with the SLAs defined in the
 * technical specifications (section 5.4.5).
 */
const PERFORMANCE_THRESHOLDS = {
  PAGE_LOAD_WARNING: 3000,      // 3 seconds
  PAGE_LOAD_CRITICAL: 5000,     // 5 seconds
  API_RESPONSE_WARNING: 1000,   // 1 second
  API_RESPONSE_CRITICAL: 2000,  // 2 seconds
  COMPONENT_RENDER_WARNING: 300, // 300ms
  RESOURCE_LOAD_WARNING: 1000   // 1 second
};

/**
 * Enum defining different types of performance metrics that can be tracked
 * by the performance monitoring service.
 */
export enum PerformanceMetricType {
  /** Page load time measurement */
  PAGE_LOAD = 'page_load',
  /** API call response time measurement */
  API_CALL = 'api_call',
  /** Component rendering time measurement */
  COMPONENT_RENDER = 'component_render',
  /** Resource (scripts, styles, images) loading time measurement */
  RESOURCE_LOAD = 'resource_load',
  /** JavaScript error tracking */
  JAVASCRIPT_ERROR = 'javascript_error',
  /** Time to interactive measurement */
  TIME_TO_INTERACTIVE = 'time_to_interactive'
}

/**
 * Interface defining the structure of a performance metric
 * to be collected, analyzed, and reported.
 */
export interface PerformanceMetric {
  /** The type of metric from PerformanceMetricType enum */
  type: string;
  /** Descriptive name of the metric */
  name: string;
  /** The value of the metric (usually time in milliseconds) */
  value: number;
  /** When the metric was recorded */
  timestamp: Date;
  /** URL when the metric was recorded */
  url: string;
  /** Additional metric details specific to the metric type */
  details?: any;
}

/**
 * Service for tracking and reporting frontend performance metrics
 * including page load times, API response times, component rendering times,
 * and resource loading metrics.
 * 
 * This service aligns with the monitoring requirements specified in
 * section 6.5.2 (Observability Patterns) of the technical specifications.
 */
@Injectable({ providedIn: 'root' })
export class PerformanceMonitoringService {
  /** Flag indicating whether performance monitoring is enabled */
  private enabled: boolean = false;
  
  /** Record of navigation timing data keyed by URL */
  private navigationTimings: Record<string, number> = {};
  
  /** Record of API timing data keyed by endpoint and method */
  private apiTimings: Record<string, Record<string, number>> = {};
  
  /** Count of JavaScript errors encountered */
  private errorCount: number = 0;
  
  /** Map of component render times keyed by component name */
  private componentRenderTimes: Map<string, number> = new Map();
  
  /** Current page URL for context in metrics */
  private currentPageUrl: string = '';
  
  /** Buffer of metrics pending submission to backend */
  private metricsBuffer: Array<PerformanceMetric> = [];
  
  /** Interval in milliseconds for flushing metrics to backend */
  private flushInterval: number = 60000; // Default: 1 minute
  
  /** Timer reference for periodic metrics flushing */
  private flushTimer: any;

  /**
   * Creates an instance of PerformanceMonitoringService.
   * Initializes performance monitoring based on application configuration.
   * 
   * @param router Angular Router for tracking navigation events
   * @param configService Service providing application configuration
   * @param metricsReporter Optional service for reporting metrics to backend
   */
  constructor(
    private router: Router,
    private configService: AppConfigService,
    @Optional() private metricsReporter: any
  ) {
    this.initialize();
  }

  /**
   * Initialize the performance monitoring service with configuration
   */
  private initialize(): void {
    // Check if performance monitoring is enabled in the configuration
    const loggingConfig = this.configService.getLoggingConfig();
    this.enabled = loggingConfig?.performanceMonitoring ?? environment.logging?.performanceMonitoring ?? false;

    if (this.enabled) {
      console.debug('Performance monitoring initialized');
      
      // Subscribe to router events to track page navigation
      this.router.events
        .pipe(
          filter(event => event instanceof NavigationStart || event instanceof NavigationEnd)
        )
        .subscribe(event => {
          if (event instanceof NavigationStart) {
            this.navigationTimings[event.url] = performance.now();
          } else if (event instanceof NavigationEnd) {
            const startTime = this.navigationTimings[event.url] || 0;
            const duration = performance.now() - startTime;
            this.trackPageLoad(event.url);
          }
        });

      // Set up periodic flushing of metrics
      this.flushInterval = loggingConfig?.metricsFlushInterval || this.flushInterval;
      this.flushTimer = setInterval(() => this.flushMetrics(), this.flushInterval);

      // Set up error monitoring
      if (typeof window !== 'undefined') {
        window.addEventListener('error', (event) => {
          this.trackError(event.error, 'window.error');
        });
      }

      // Initialize Performance API observers if available
      if (typeof window !== 'undefined' && window.performance) {
        // Measure resource loading performance periodically
        setInterval(() => this.measureResourceLoadTime(), 10000);
      }
    }
  }

  /**
   * Track page load timing metrics
   * @param url The page URL being loaded
   */
  trackPageLoad(url: string): void {
    if (!this.enabled) return;

    this.currentPageUrl = url;
    
    let loadTime = 0;
    
    // Get page load time from Navigation Timing API if available
    if (typeof window !== 'undefined' && window.performance && window.performance.timing) {
      const perfData = window.performance.timing;
      
      // If navigation is complete, calculate load time
      if (perfData.loadEventEnd > 0) {
        loadTime = perfData.loadEventEnd - perfData.navigationStart;
      } else {
        // For SPA navigation or incomplete page load
        const startTime = this.navigationTimings[url] || 0;
        loadTime = performance.now() - startTime;
      }
    } else {
      // Fallback for environments without Performance API
      const startTime = this.navigationTimings[url] || 0;
      loadTime = startTime > 0 ? (Date.now() - startTime) : 0;
    }

    // Ensure load time is valid
    if (loadTime < 0) loadTime = 0;

    // Create and store the metric
    const metric: PerformanceMetric = {
      type: PerformanceMetricType.PAGE_LOAD,
      name: 'PageLoad',
      value: loadTime,
      timestamp: new Date(),
      url: url,
      details: {
        timeToInteractive: this.calculateTimeToInteractive()
      }
    };

    this.metricsBuffer.push(metric);

    // Log warnings for slow page loads
    if (loadTime > PERFORMANCE_THRESHOLDS.PAGE_LOAD_CRITICAL) {
      console.warn(`Critical: Page load time (${loadTime}ms) exceeds critical threshold for ${url}`);
    } else if (loadTime > PERFORMANCE_THRESHOLDS.PAGE_LOAD_WARNING) {
      console.warn(`Warning: Page load time (${loadTime}ms) exceeds warning threshold for ${url}`);
    }
  }

  /**
   * Start tracking an API call
   * @param endpoint API endpoint URL
   * @param method HTTP method
   * @returns Start timestamp for the API call
   */
  trackApiCall(endpoint: string, method: string): number {
    if (!this.enabled) return Date.now();

    const timestamp = Date.now();
    return timestamp;
  }

  /**
   * End tracking an API call and record its duration
   * @param endpoint API endpoint URL
   * @param method HTTP method
   * @param startTime Start timestamp from trackApiCall
   */
  endApiCall(endpoint: string, method: string, startTime: number): void {
    if (!this.enabled) return;

    const endTime = Date.now();
    const duration = endTime - startTime;

    // Store API timing information by endpoint
    if (!this.apiTimings[endpoint]) {
      this.apiTimings[endpoint] = {};
    }
    this.apiTimings[endpoint][method] = duration;

    // Create and store the metric
    const metric: PerformanceMetric = {
      type: PerformanceMetricType.API_CALL,
      name: `API:${method}:${endpoint}`,
      value: duration,
      timestamp: new Date(),
      url: this.currentPageUrl,
      details: {
        endpoint,
        method,
        startTime,
        endTime
      }
    };

    this.metricsBuffer.push(metric);

    // Log warnings for slow API calls
    if (duration > PERFORMANCE_THRESHOLDS.API_RESPONSE_CRITICAL) {
      console.warn(`Critical: API response time (${duration}ms) exceeds critical threshold for ${method} ${endpoint}`);
    } else if (duration > PERFORMANCE_THRESHOLDS.API_RESPONSE_WARNING) {
      console.warn(`Warning: API response time (${duration}ms) exceeds warning threshold for ${method} ${endpoint}`);
    }
  }

  /**
   * Track component rendering time
   * @param componentName Name of the component
   * @param renderTime Time taken to render in milliseconds
   */
  trackComponentRender(componentName: string, renderTime: number): void {
    if (!this.enabled) return;

    // Store component render time
    this.componentRenderTimes.set(componentName, renderTime);

    // Create and store the metric
    const metric: PerformanceMetric = {
      type: PerformanceMetricType.COMPONENT_RENDER,
      name: `Component:${componentName}`,
      value: renderTime,
      timestamp: new Date(),
      url: this.currentPageUrl
    };

    this.metricsBuffer.push(metric);

    // Log warnings for slow component renders
    if (renderTime > PERFORMANCE_THRESHOLDS.COMPONENT_RENDER_WARNING) {
      console.warn(`Warning: Component render time (${renderTime}ms) exceeds threshold for ${componentName}`);
    }
  }

  /**
   * Track JavaScript errors
   * @param error The error object
   * @param context Context in which the error occurred
   */
  trackError(error: Error, context: string): void {
    if (!this.enabled) return;

    this.errorCount++;

    // Create error details object
    const errorDetails = {
      message: error.message,
      stack: error.stack,
      context: context
    };

    // Create and store the metric
    const metric: PerformanceMetric = {
      type: PerformanceMetricType.JAVASCRIPT_ERROR,
      name: `Error:${error.name || 'Unknown'}`,
      value: 1, // Error count as value
      timestamp: new Date(),
      url: this.currentPageUrl,
      details: errorDetails
    };

    this.metricsBuffer.push(metric);

    // Log error in development mode
    if (!this.configService.isProduction()) {
      console.error('Tracked error:', error, 'Context:', context);
    }
  }

  /**
   * Measure loading time for various resources (scripts, styles, images)
   */
  measureResourceLoadTime(): void {
    if (!this.enabled || typeof window === 'undefined' || !window.performance || !window.performance.getEntriesByType) {
      return;
    }

    try {
      // Get resource timing entries
      const resources = window.performance.getEntriesByType('resource') as PerformanceResourceTiming[];

      // Group resources by type
      const entriesByType: Record<string, PerformanceResourceTiming[]> = {};
      resources.forEach(entry => {
        const url = entry.name;
        let type = 'other';

        if (url.match(/\.js(\?|$)/)) type = 'script';
        else if (url.match(/\.css(\?|$)/)) type = 'style';
        else if (url.match(/\.(png|jpg|jpeg|gif|svg|webp)(\?|$)/)) type = 'image';
        else if (url.match(/\.(woff|woff2|ttf|eot)(\?|$)/)) type = 'font';
        else if (url.match(/api\//)) type = 'api';

        if (!entriesByType[type]) {
          entriesByType[type] = [];
        }
        entriesByType[type].push(entry);
      });

      // Check for slow-loading resources
      Object.keys(entriesByType).forEach(type => {
        entriesByType[type].forEach(entry => {
          const loadTime = entry.responseEnd - entry.startTime;
          
          if (loadTime > PERFORMANCE_THRESHOLDS.RESOURCE_LOAD_WARNING) {
            // Create and store the metric for slow resources
            const metric: PerformanceMetric = {
              type: PerformanceMetricType.RESOURCE_LOAD,
              name: `Resource:${type}`,
              value: loadTime,
              timestamp: new Date(),
              url: this.currentPageUrl,
              details: {
                resourceUrl: entry.name,
                resourceType: type,
                size: entry.transferSize,
                duration: loadTime
              }
            };

            this.metricsBuffer.push(metric);

            // Log warning for slow resource
            console.warn(`Warning: Slow resource load (${loadTime}ms) for ${entry.name}`);
          }
        });
      });

      // Clear resource timing buffer to avoid growing endlessly
      if (window.performance.clearResourceTimings) {
        window.performance.clearResourceTimings();
      }
    } catch (error) {
      console.error('Error measuring resource load time:', error);
    }
  }

  /**
   * Calculate time to interactive for the current page
   * @returns Time to interactive in milliseconds
   */
  calculateTimeToInteractive(): number {
    if (typeof window === 'undefined' || !window.performance || !window.performance.timing) {
      return 0;
    }

    try {
      const timing = window.performance.timing;
      
      // First Input Delay & Time to Interactive are modern metrics,
      // but not always available in all browsers
      // This is a simplified estimation based on DOMContentLoaded
      const domContentLoadedTime = timing.domContentLoadedEventEnd - timing.navigationStart;
      
      // Estimate TTI as DOMContentLoaded + a constant for script execution
      // A more accurate measure would require the First Input Delay polyfill
      const estimatedTTI = domContentLoadedTime + 500;
      
      return estimatedTTI > 0 ? estimatedTTI : 0;
    } catch (error) {
      console.error('Error calculating time to interactive:', error);
      return 0;
    }
  }

  /**
   * Send collected metrics to backend for storage and analysis
   * @returns Observable with response from metrics API
   */
  flushMetrics(): Observable<any> {
    if (!this.enabled || this.metricsBuffer.length === 0) {
      return of(null);
    }

    if (!this.metricsReporter) {
      console.warn('No metrics reporter provided to PerformanceMonitoringService, metrics will not be sent to backend');
      return of(null);
    }

    // Create a copy of the buffer and clear it
    const metrics = [...this.metricsBuffer];
    this.metricsBuffer = [];

    // Format the payload
    const payload = {
      metrics,
      timestamp: new Date(),
      userAgent: typeof navigator !== 'undefined' ? navigator.userAgent : 'unknown',
      url: typeof window !== 'undefined' ? window.location.href : 'unknown'
    };

    // Send metrics to backend
    return this.metricsReporter.sendMetrics(payload).pipe(
      tap(() => {
        console.debug(`Sent ${metrics.length} performance metrics to backend`);
      }),
      catchError(error => {
        console.error('Error sending performance metrics:', error);
        // Put metrics back in buffer for retry on next flush
        this.metricsBuffer = [...this.metricsBuffer, ...metrics];
        return of(null);
      })
    );
  }

  /**
   * Get the current performance metrics summary
   * @returns Object containing performance metrics
   */
  getPerformanceMetrics(): object {
    const pageLoadTiming: Record<string, any> = {};
    const apiTiming: Record<string, any> = {};
    const componentTiming: Record<string, any> = {};

    // Extract page load timings
    Object.keys(this.navigationTimings).forEach(url => {
      pageLoadTiming[url] = this.navigationTimings[url];
    });

    // Extract API call timings
    Object.keys(this.apiTimings).forEach(endpoint => {
      apiTiming[endpoint] = this.apiTimings[endpoint];
    });

    // Extract component render timings
    this.componentRenderTimes.forEach((value, key) => {
      componentTiming[key] = value;
    });

    return {
      pageLoad: pageLoadTiming,
      api: apiTiming,
      component: componentTiming,
      errors: this.errorCount,
      metricsCollected: this.metricsBuffer.length,
      enabled: this.enabled,
      timestamp: formatDate(new Date(), 'yyyy-MM-dd HH:mm:ss')
    };
  }

  /**
   * Check if performance monitoring is enabled
   * @returns True if monitoring is enabled
   */
  isEnabled(): boolean {
    return this.enabled;
  }

  /**
   * Enable or disable performance monitoring
   * @param state True to enable, false to disable
   */
  setEnabled(state: boolean): void {
    this.enabled = state;
    
    if (state && !this.flushTimer) {
      // Re-initialize monitoring if enabling
      this.flushTimer = setInterval(() => this.flushMetrics(), this.flushInterval);
    } else if (!state && this.flushTimer) {
      // Clear timer if disabling
      clearInterval(this.flushTimer);
      this.flushTimer = undefined;
    }

    console.log(`Performance monitoring ${state ? 'enabled' : 'disabled'}`);
  }

  /**
   * Reset all performance metrics
   */
  reset(): void {
    this.navigationTimings = {};
    this.apiTimings = {};
    this.errorCount = 0;
    this.componentRenderTimes.clear();
    this.metricsBuffer = [];
    
    if (!this.configService.isProduction()) {
      console.debug('Performance metrics reset');
    }
  }
}