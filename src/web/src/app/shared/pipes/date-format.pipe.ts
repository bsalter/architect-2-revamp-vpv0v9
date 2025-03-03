import { Pipe, PipeTransform } from '@angular/core'; // v16.2.0
import { formatDate, formatDateTimeWithTimezone, DATE_FORMATS } from '../../../core/utils/datetime-utils';

/**
 * Angular pipe that transforms date values into consistently formatted strings
 * based on specified format patterns, with optional timezone support.
 * 
 * Usage examples:
 * {{ interactionDate | dateFormat:'DISPLAY_DATE' }}
 * {{ interactionDateTime | dateFormat:'DISPLAY_DATETIME' }}
 * {{ interactionDateTime | dateFormat:'DISPLAY_DATETIME':{ timezone: 'America/New_York' } }}
 * {{ interactionDateTime | dateFormat:'MMM d, yyyy h:mm a' }}
 */
@Pipe({
  name: 'dateFormat',
  pure: true // Pure pipe for better performance
})
export class DateFormatPipe implements PipeTransform {
  /**
   * Transforms a date into a formatted string based on specified format and options.
   * 
   * @param value - The date value to format (Date object or date string)
   * @param format - The format to use (custom format string or key from DATE_FORMATS)
   * @param options - Optional configuration object with timezone
   * @returns Formatted date string or empty string if date is invalid
   */
  transform(value: Date | string, format: string, options?: { timezone?: string }): string {
    // Check if the value is null, undefined, or empty
    if (value === null || value === undefined || value === '') {
      return '';
    }

    try {
      // Determine the format pattern to use (either a predefined format or custom format string)
      const formatPattern = Object.prototype.hasOwnProperty.call(DATE_FORMATS, format) 
        ? DATE_FORMATS[format] 
        : format;
      
      // Get timezone from options if provided
      const timezone = options?.timezone;
      
      // Format with timezone if provided, otherwise use standard formatting
      if (timezone) {
        return formatDateTimeWithTimezone(value, formatPattern, timezone);
      } else {
        return formatDate(value, formatPattern);
      }
    } catch (error) {
      console.error('Error in DateFormatPipe:', error);
      return '';
    }
  }
}