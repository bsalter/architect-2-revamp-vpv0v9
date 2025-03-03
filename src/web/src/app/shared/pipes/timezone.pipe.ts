import { Pipe, PipeTransform } from '@angular/core'; // v16.2.0
import { isValidTimezone, getTimezoneOffset, formatTimezoneOffset } from '../../../core/utils/datetime-utils';

/**
 * Mapping of common timezone abbreviations to their full names
 */
const TIMEZONE_ABBREVIATIONS: { [key: string]: string } = {
  "EST": "Eastern Standard Time",
  "EDT": "Eastern Daylight Time",
  "CST": "Central Standard Time",
  "CDT": "Central Daylight Time",
  "MST": "Mountain Standard Time",
  "MDT": "Mountain Daylight Time",
  "PST": "Pacific Standard Time",
  "PDT": "Pacific Daylight Time",
  "UTC": "Coordinated Universal Time"
};

/**
 * Angular pipe that formats timezone identifiers into user-friendly display formats
 * with optional offset information.
 * 
 * Usage examples:
 * {{ 'America/New_York' | timezone }} -> "ET"
 * {{ 'America/New_York' | timezone: { includeOffset: true } }} -> "ET +05:00"
 * {{ 'UTC' | timezone: { includeFullName: true } }} -> "UTC Coordinated Universal Time"
 */
@Pipe({
  name: 'timezone',
  pure: true
})
export class TimezonePipe implements PipeTransform {
  /**
   * Creates an instance of TimezonePipe.
   */
  constructor() {}

  /**
   * Transforms a timezone identifier into a formatted display string.
   * 
   * @param timezone - Timezone identifier to format
   * @param options - Format options:
   *   - includeOffset: Whether to include the timezone offset (e.g., "+05:00")
   *   - includeAbbreviation: Whether to include the timezone abbreviation (e.g., "ET")
   *   - includeFullName: Whether to include the full timezone name
   * @returns Formatted timezone string or empty string if timezone is invalid
   */
  transform(timezone: string, options: {
    includeOffset?: boolean;
    includeAbbreviation?: boolean;
    includeFullName?: boolean;
  } = {}): string {
    // Check if timezone is null, undefined, or empty
    if (!timezone) {
      return '';
    }

    // Validate timezone
    if (!isValidTimezone(timezone)) {
      return 'Invalid timezone';
    }

    // Extract options with defaults
    const {
      includeOffset = false,
      includeAbbreviation = true,
      includeFullName = false
    } = options;

    // Format components array
    const parts: string[] = [];

    // Add abbreviation if requested
    if (includeAbbreviation) {
      const abbreviation = this.getTimezoneAbbreviation(timezone);
      if (abbreviation) {
        parts.push(abbreviation);
      }
    }

    // Add full name if requested
    if (includeFullName) {
      const fullName = this.getTimezoneFullName(timezone);
      if (fullName && !parts.includes(fullName)) {
        parts.push(fullName);
      }
    }

    // Add timezone offset if requested
    if (includeOffset) {
      const offset = getTimezoneOffset(timezone);
      const formattedOffset = formatTimezoneOffset(offset);
      parts.push(formattedOffset);
    }

    // Join all parts and return
    return parts.join(' ');
  }

  /**
   * Extracts an abbreviation from a timezone identifier.
   * 
   * @param timezone - Timezone identifier
   * @returns Timezone abbreviation (e.g., 'ET' for 'America/New_York')
   */
  getTimezoneAbbreviation(timezone: string): string {
    // Check if the timezone is already an abbreviation
    if (TIMEZONE_ABBREVIATIONS[timezone]) {
      return timezone;
    }

    // Extract region code from the timezone identifier
    if (timezone.includes('/')) {
      const region = timezone.split('/')[0];
      
      // Map common regions to their abbreviations
      switch (region) {
        case 'America':
          // Parse city to determine US timezone abbreviation
          const city = timezone.split('/')[1];
          
          // Eastern Time
          if (['New_York', 'Detroit', 'Toronto', 'Eastern', 'Indianapolis'].includes(city)) {
            return 'ET';
          }
          // Central Time
          else if (['Chicago', 'Central', 'Mexico_City', 'Winnipeg'].includes(city)) {
            return 'CT';
          }
          // Mountain Time
          else if (['Denver', 'Mountain', 'Phoenix', 'Edmonton'].includes(city)) {
            return 'MT';
          }
          // Pacific Time
          else if (['Los_Angeles', 'Pacific', 'Vancouver', 'Tijuana'].includes(city)) {
            return 'PT';
          }
          return 'AT'; // Americas Time (fallback)
          
        case 'Europe':
          return 'ET'; // European Time
          
        case 'Asia':
          return 'AT'; // Asian Time
          
        case 'Africa':
          return 'AFT'; // African Time
          
        case 'Australia':
          return 'AUT'; // Australian Time
          
        case 'Pacific':
          return 'PT'; // Pacific Time
          
        default:
          return region.substring(0, 2).toUpperCase() + 'T';
      }
    }
    
    // Handle special case for UTC/GMT
    if (timezone === 'UTC' || timezone === 'GMT') {
      return timezone;
    }
    
    // For unrecognized formats, return the first 2-3 characters + T
    return timezone.substring(0, Math.min(2, timezone.length)).toUpperCase() + 'T';
  }

  /**
   * Generates a user-friendly name for a timezone.
   * 
   * @param timezone - Timezone identifier
   * @returns User-friendly timezone name
   */
  getTimezoneFullName(timezone: string): string {
    // Check if timezone is an abbreviation in our mapping
    if (TIMEZONE_ABBREVIATIONS[timezone]) {
      return TIMEZONE_ABBREVIATIONS[timezone];
    }
    
    // Otherwise, format the timezone identifier into a readable name
    if (timezone.includes('/')) {
      const parts = timezone.split('/');
      
      // Handle multi-part identifiers (e.g., America/New_York)
      if (parts.length >= 2) {
        // Format the city name for readability
        let location = parts[parts.length - 1].replace(/_/g, ' ');
        
        // Special case for America/Argentina/Buenos_Aires type formats
        if (parts.length > 2) {
          location = `${parts[1]}/${location}`;
        }
        
        return `${location} (${parts[0]})`;
      }
    }
    
    // If we can't parse it in a standard way, just clean it up
    return timezone.replace(/_/g, ' ');
  }
}