/**
 * String utilities module
 * 
 * This module provides utility functions for string manipulation, validation, and sanitization
 * used throughout the Interaction Management System.
 * 
 * @version 1.0.0
 */

/**
 * Checks if a string is empty, null, undefined, or contains only whitespace
 * 
 * @param value - The string value to check
 * @returns True if the string is empty or only whitespace, false otherwise
 */
export function isEmpty(value: string | null | undefined): boolean {
  return value === null || value === undefined || (typeof value === 'string' && value.trim() === '');
}

/**
 * Checks if a string is not empty (has content beyond whitespace)
 * 
 * @param value - The string value to check
 * @returns True if the string has content beyond whitespace, false otherwise
 */
export function isNotEmpty(value: string | null | undefined): boolean {
  return !isEmpty(value);
}

/**
 * Truncates a string to a specified length and adds an ellipsis if truncated
 * 
 * @param value - The string to truncate
 * @param maxLength - The maximum length of the returned string (including suffix)
 * @param suffix - The string to append if truncated (default: '...')
 * @returns Truncated string with suffix if shortened, or original string if short enough
 */
export function truncate(value: string | null | undefined, maxLength: number, suffix?: string): string {
  if (isEmpty(value)) {
    return '';
  }
  
  const ellipsis = suffix || '...';
  
  if ((value as string).length <= maxLength) {
    return value as string;
  }
  
  return `${(value as string).substring(0, maxLength - ellipsis.length)}${ellipsis}`;
}

/**
 * Capitalizes the first letter of a string
 * 
 * @param value - The string to capitalize
 * @returns String with first letter capitalized
 */
export function capitalize(value: string | null | undefined): string {
  if (isEmpty(value)) {
    return '';
  }
  
  const str = value as string;
  return str.charAt(0).toUpperCase() + str.slice(1);
}

/**
 * Converts a camelCase string to Title Case with spaces
 * 
 * @param camelCase - The camelCase string to convert
 * @returns Converted string in Title Case with spaces
 */
export function camelToTitle(camelCase: string | null | undefined): string {
  if (isEmpty(camelCase)) {
    return '';
  }
  
  const result = (camelCase as string).replace(/([A-Z])/g, ' $1');
  return capitalize(result.trim());
}

/**
 * Sanitizes HTML strings to prevent XSS attacks
 * 
 * @param html - The HTML string to sanitize
 * @returns Sanitized HTML string
 */
export function sanitizeHtml(html: string | null | undefined): string {
  if (isEmpty(html)) {
    return '';
  }
  
  return (html as string)
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;')
    .replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '')
    .replace(/on\w+="[^"]*"/g, '')
    .replace(/on\w+='[^']*'/g, '');
}

/**
 * Formats a phone number string into a standardized format
 * 
 * @param phoneNumber - The phone number string to format
 * @returns Formatted phone number in (xxx) xxx-xxxx format
 */
export function formatPhoneNumber(phoneNumber: string | null | undefined): string {
  if (isEmpty(phoneNumber)) {
    return '';
  }
  
  // Remove all non-numeric characters
  const cleaned = (phoneNumber as string).replace(/\D/g, '');
  
  // Format based on length
  if (cleaned.length === 10) {
    return `(${cleaned.substring(0, 3)}) ${cleaned.substring(3, 6)}-${cleaned.substring(6, 10)}`;
  } else if (cleaned.length === 11 && cleaned.charAt(0) === '1') {
    return `(${cleaned.substring(1, 4)}) ${cleaned.substring(4, 7)}-${cleaned.substring(7, 11)}`;
  }
  
  // If not a standard format, return the cleaned number
  return cleaned;
}

/**
 * Gets the initials from a name string (first letter of each word)
 * 
 * @param name - The name to extract initials from
 * @param maxInitials - Maximum number of initials to return (optional)
 * @returns Initials extracted from the name
 */
export function getInitials(name: string | null | undefined, maxInitials?: number): string {
  if (isEmpty(name)) {
    return '';
  }
  
  const words = (name as string).split(' ').filter(word => word.length > 0);
  let initials = words.map(word => word.charAt(0)).join('').toUpperCase();
  
  if (maxInitials && maxInitials > 0 && initials.length > maxInitials) {
    initials = initials.substring(0, maxInitials);
  }
  
  return initials;
}

/**
 * Removes HTML tags from a string
 * 
 * @param html - The HTML string to strip tags from
 * @returns Plain text with HTML tags removed
 */
export function stripHtml(html: string | null | undefined): string {
  if (isEmpty(html)) {
    return '';
  }
  
  return (html as string).replace(/<\/?[^>]+(>|$)/g, '');
}

/**
 * Converts a string to a URL-friendly slug
 * 
 * @param text - The text to convert to a slug
 * @returns URL-friendly slug
 */
export function slugify(text: string | null | undefined): string {
  if (isEmpty(text)) {
    return '';
  }
  
  return (text as string)
    .toLowerCase()
    .replace(/\s+/g, '-')         // Replace spaces with hyphens
    .replace(/[^\w\-]+/g, '')     // Remove all non-word characters
    .replace(/\-\-+/g, '-')       // Replace multiple hyphens with single hyphen
    .replace(/^-+/, '')           // Trim hyphens from start
    .replace(/-+$/, '');          // Trim hyphens from end
}

/**
 * Checks if a string contains another string (case insensitive)
 * 
 * @param text - The text to search within
 * @param searchString - The string to search for
 * @returns True if searchString is found in text (ignoring case)
 */
export function containsIgnoreCase(text: string | null | undefined, searchString: string | null | undefined): boolean {
  if (text === null || text === undefined || searchString === null || searchString === undefined) {
    return false;
  }
  
  return text.toLowerCase().includes(searchString.toLowerCase());
}