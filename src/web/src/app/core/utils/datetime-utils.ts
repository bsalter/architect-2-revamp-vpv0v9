import { 
  format, 
  parse, 
  isValid, 
  parseISO, 
  formatISO, 
  addMinutes, 
  differenceInMinutes, 
  isAfter, 
  isBefore 
} from 'date-fns'; // v2.30.0
import { 
  formatInTimeZone, 
  utcToZonedTime, 
  zonedTimeToUtc 
} from 'date-fns-tz'; // v2.0.0

/**
 * Standard date format patterns used throughout the application
 */
export const DATE_FORMATS = {
  API_ISO: "yyyy-MM-dd'T'HH:mm:ss.SSS'Z'", // ISO format for API communication
  DISPLAY_DATE: 'MMM d, yyyy',             // Formatted date for display (e.g., Jan 1, 2023)
  DISPLAY_TIME: 'h:mm a',                  // Formatted time for display (e.g., 3:30 PM)
  DISPLAY_DATETIME: 'MMM d, yyyy h:mm a',  // Formatted date and time for display
  INPUT_DATE: 'yyyy-MM-dd',                // HTML date input format
  INPUT_TIME: 'HH:mm',                     // HTML time input format
  TIMEZONE_OFFSET: 'XXX'                   // Timezone offset format (e.g., +02:00)
};

/**
 * Formats a date using the specified format pattern
 * 
 * @param date - Date object or string to format
 * @param formatPattern - Format pattern to use (e.g., from DATE_FORMATS)
 * @returns Formatted date string or empty string if date is invalid
 */
export function formatDate(date: Date | string, formatPattern: string): string {
  try {
    if (!date) return '';
    
    let dateObj: Date;
    
    if (typeof date === 'string') {
      // Try to parse the date string
      dateObj = parseISO(date);
      if (!isValid(dateObj)) {
        return '';
      }
    } else if (date instanceof Date) {
      dateObj = date;
      if (!isValid(dateObj)) {
        return '';
      }
    } else {
      return '';
    }
    
    return format(dateObj, formatPattern);
  } catch (error) {
    console.error('Error formatting date:', error);
    return '';
  }
}

/**
 * Formats a date with timezone consideration
 * 
 * @param date - Date object or string to format
 * @param formatPattern - Format pattern to use
 * @param timezone - IANA timezone identifier (e.g., 'America/New_York')
 * @returns Timezone-aware formatted date string or empty string if invalid
 */
export function formatDateTimeWithTimezone(
  date: Date | string,
  formatPattern: string,
  timezone: string
): string {
  try {
    if (!date || !isValidTimezone(timezone)) return '';
    
    let dateObj: Date;
    
    if (typeof date === 'string') {
      // Try to parse the date string
      dateObj = parseISO(date);
      if (!isValid(dateObj)) {
        return '';
      }
    } else if (date instanceof Date) {
      dateObj = date;
      if (!isValid(dateObj)) {
        return '';
      }
    } else {
      return '';
    }
    
    return formatInTimeZone(dateObj, timezone, formatPattern);
  } catch (error) {
    console.error('Error formatting date with timezone:', error);
    return '';
  }
}

/**
 * Parses a string representation of a date to a Date object
 * 
 * @param dateString - String to parse
 * @param formatPattern - Expected format of the string
 * @returns Date object or null if parsing fails
 */
export function parseStringToDate(dateString: string, formatPattern: string): Date | null {
  try {
    if (!dateString) return null;
    
    // Try parsing with the specified format
    const parsedDate = parse(dateString, formatPattern, new Date());
    
    if (isValid(parsedDate)) {
      return parsedDate;
    }
    
    // Try parsing as ISO string as fallback
    const isoDate = parseISO(dateString);
    if (isValid(isoDate)) {
      return isoDate;
    }
    
    return null;
  } catch (error) {
    console.error('Error parsing date string:', error);
    return null;
  }
}

/**
 * Converts a date from one timezone to another
 * 
 * @param date - Date to convert
 * @param fromTimezone - Source IANA timezone identifier
 * @param toTimezone - Target IANA timezone identifier
 * @returns Date converted to the target timezone
 */
export function convertToTimezone(
  date: Date,
  fromTimezone: string,
  toTimezone: string
): Date {
  try {
    if (!isValidTimezone(fromTimezone) || !isValidTimezone(toTimezone)) {
      throw new Error('Invalid timezone identifier');
    }
    
    // Convert to UTC first
    const utcDate = zonedTimeToUtc(date, fromTimezone);
    
    // Then convert from UTC to the target timezone
    return utcToZonedTime(utcDate, toTimezone);
  } catch (error) {
    console.error('Error converting between timezones:', error);
    return date; // Return original date on error
  }
}

/**
 * Gets the offset in minutes for a timezone at a specific date
 * 
 * @param timezone - IANA timezone identifier
 * @param date - Date to get the offset for (defaults to now)
 * @returns Offset in minutes
 */
export function getTimezoneOffset(timezone: string, date: Date = new Date()): number {
  try {
    if (!isValidTimezone(timezone)) {
      throw new Error('Invalid timezone identifier');
    }
    
    // Calculate the difference between the UTC time and the timezone time
    const zonedDate = utcToZonedTime(date, timezone);
    const utcMinutes = date.getUTCHours() * 60 + date.getUTCMinutes();
    const zonedMinutes = zonedDate.getHours() * 60 + zonedDate.getMinutes();
    
    // Calculate the difference, adjusting for date boundary crossing
    let diff = zonedMinutes - utcMinutes;
    if (diff > 720) diff -= 1440; // Adjust if we've crossed the international date line
    if (diff < -720) diff += 1440;
    
    return diff;
  } catch (error) {
    console.error('Error getting timezone offset:', error);
    return 0;
  }
}

/**
 * Formats a timezone offset in minutes to +/-HH:MM format
 * 
 * @param offsetMinutes - Offset in minutes
 * @returns Formatted offset string (e.g., "+05:30")
 */
export function formatTimezoneOffset(offsetMinutes: number): string {
  const sign = offsetMinutes >= 0 ? '+' : '-';
  const absMinutes = Math.abs(offsetMinutes);
  const hours = Math.floor(absMinutes / 60);
  const minutes = absMinutes % 60;
  
  // Pad with zeros to ensure HH:MM format
  const paddedHours = hours.toString().padStart(2, '0');
  const paddedMinutes = minutes.toString().padStart(2, '0');
  
  return `${sign}${paddedHours}:${paddedMinutes}`;
}

/**
 * Checks if a timezone identifier is valid
 * 
 * @param timezone - IANA timezone identifier to check
 * @returns True if timezone is valid, false otherwise
 */
export function isValidTimezone(timezone: string): boolean {
  if (!timezone || typeof timezone !== 'string') return false;
  
  try {
    // Attempt to format a date with this timezone - will throw if invalid
    formatInTimeZone(new Date(), timezone, 'yyyy-MM-dd');
    return true;
  } catch (error) {
    return false;
  }
}

/**
 * Returns a list of common timezone identifiers from the IANA timezone database
 * 
 * @returns Array of timezone identifiers
 */
export function getCommonTimezones(): string[] {
  return [
    'UTC',
    'America/Los_Angeles', // Pacific Time
    'America/Denver',      // Mountain Time
    'America/Chicago',     // Central Time
    'America/New_York',    // Eastern Time
    'America/Anchorage',   // Alaska
    'Pacific/Honolulu',    // Hawaii
    'America/Halifax',     // Atlantic Time
    'America/Sao_Paulo',   // Brazil
    'Europe/London',       // GMT/BST
    'Europe/Paris',        // Central European Time
    'Europe/Athens',       // Eastern European Time
    'Africa/Cairo',        // Egypt
    'Asia/Dubai',          // United Arab Emirates
    'Asia/Kolkata',        // India
    'Asia/Singapore',      // Singapore
    'Asia/Tokyo',          // Japan
    'Asia/Seoul',          // Korea
    'Australia/Sydney',    // Australia Eastern
    'Australia/Perth',     // Australia Western
    'Pacific/Auckland'     // New Zealand
  ];
}

/**
 * Calculates the duration in minutes between two dates
 * 
 * @param startDate - Start date
 * @param endDate - End date
 * @param timezone - Optional timezone to consider both dates in
 * @returns Duration in minutes (absolute value)
 */
export function calculateDuration(
  startDate: Date | string,
  endDate: Date | string,
  timezone?: string
): number {
  try {
    // Convert string dates to Date objects if needed
    let start: Date;
    let end: Date;
    
    if (typeof startDate === 'string') {
      start = parseISO(startDate);
      if (!isValid(start)) throw new Error('Invalid start date');
    } else {
      start = startDate;
    }
    
    if (typeof endDate === 'string') {
      end = parseISO(endDate);
      if (!isValid(end)) throw new Error('Invalid end date');
    } else {
      end = endDate;
    }
    
    // If timezone is provided, ensure both dates are in the same timezone
    if (timezone && isValidTimezone(timezone)) {
      start = utcToZonedTime(start, timezone);
      end = utcToZonedTime(end, timezone);
    }
    
    // Calculate the difference in minutes
    const diffInMinutes = differenceInMinutes(end, start);
    
    // Return absolute value in case end is before start
    return Math.abs(diffInMinutes);
  } catch (error) {
    console.error('Error calculating duration:', error);
    return 0;
  }
}

/**
 * Checks if a date range is valid (start date is before end date)
 * 
 * @param startDate - Start date
 * @param endDate - End date
 * @returns True if the range is valid, false otherwise
 */
export function isValidDateRange(
  startDate: Date | string,
  endDate: Date | string
): boolean {
  try {
    // Convert string dates to Date objects if needed
    let start: Date;
    let end: Date;
    
    if (typeof startDate === 'string') {
      start = parseISO(startDate);
      if (!isValid(start)) return false;
    } else {
      start = startDate;
      if (!isValid(start)) return false;
    }
    
    if (typeof endDate === 'string') {
      end = parseISO(endDate);
      if (!isValid(end)) return false;
    } else {
      end = endDate;
      if (!isValid(end)) return false;
    }
    
    // Check if start date is before end date
    return isBefore(start, end);
  } catch (error) {
    console.error('Error validating date range:', error);
    return false;
  }
}

/**
 * Gets the user's current timezone from the browser
 * 
 * @returns Current timezone identifier or UTC if detection fails
 */
export function getCurrentTimezone(): string {
  try {
    const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
    
    // Validate the detected timezone
    if (isValidTimezone(timezone)) {
      return timezone;
    }
    
    return 'UTC'; // Default to UTC if timezone detection fails
  } catch (error) {
    console.error('Error getting current timezone:', error);
    return 'UTC';
  }
}