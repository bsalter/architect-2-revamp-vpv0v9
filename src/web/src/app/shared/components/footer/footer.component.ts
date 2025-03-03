import { Component, OnInit } from '@angular/core'; // @angular/core version 16.2.0
import { AppConfigService } from '../../../core/config/app-config.service';

/**
 * Footer component that provides a consistent footer across the Interaction Management System.
 * Displays copyright information, application version, and navigation links.
 * Adapts to different screen sizes and maintains accessibility compliance.
 */
@Component({
  selector: 'app-footer',
  templateUrl: './footer.component.html',
  styleUrls: ['./footer.component.scss']
})
export class FooterComponent implements OnInit {
  /** The current year for copyright display */
  currentYear: number;
  
  /** Application version from configuration */
  version: string;
  
  /** Flag indicating if app is running in production mode */
  isProduction: boolean;
  
  /**
   * Creates an instance of FooterComponent.
   * @param configService Service for accessing application configuration
   */
  constructor(private configService: AppConfigService) {
    // Initialize with default values
    this.currentYear = new Date().getFullYear();
    this.version = 'Development';
    this.isProduction = false;
  }
  
  /**
   * Lifecycle hook that initializes the component.
   * Retrieves application version and checks production status.
   */
  ngOnInit(): void {
    // Check if application is running in production mode
    this.isProduction = this.configService.isProduction();
    
    // Get application configuration to retrieve version info
    const config = this.configService.getConfig();
    
    // Set application version from configuration
    // If version is not explicitly in the interface, we try to access it dynamically
    // or use a default value
    this.version = (config as any).version || (this.isProduction ? '1.0.0' : 'Development');
  }
}