import { Pipe, PipeTransform } from '@angular/core'; // v16.2.0
import { DomSanitizer, SafeHtml } from '@angular/platform-browser'; // v16.2.0

/**
 * Angular pipe that safely renders HTML content by bypassing Angular's built-in sanitization.
 * This allows trusted HTML content to be displayed in templates, particularly useful for
 * rendering rich text content in interaction descriptions and notes.
 * 
 * SECURITY WARNING: Only use this pipe with content from trusted sources as it bypasses
 * Angular's built-in XSS protection. Never use with user-generated content that hasn't
 * been properly sanitized first.
 */
@Pipe({
  name: 'safeHtml',
  pure: true
})
export class SafeHtmlPipe implements PipeTransform {
  /**
   * Creates an instance of SafeHtmlPipe with DomSanitizer injection.
   * @param sanitizer Angular's DomSanitizer service for handling HTML content safely
   */
  constructor(private sanitizer: DomSanitizer) {}

  /**
   * Transforms a string containing HTML into a SafeHtml value that can be used in templates.
   * @param value The HTML string to be sanitized and trusted
   * @returns A SafeHtml object that Angular will render without sanitization
   */
  transform(value: string): SafeHtml {
    // Check if value is null, undefined, or empty - return empty string if true
    if (!value) {
      return '';
    }
    
    // Use DomSanitizer.bypassSecurityTrustHtml to mark the content as safe
    return this.sanitizer.bypassSecurityTrustHtml(value);
  }
}