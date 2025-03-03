import { Pipe, PipeTransform } from '@angular/core'; // @angular/core v16.2.0

/**
 * Angular pipe that filters arrays based on provided criteria.
 * This pipe allows filtering arrays by a specific property or across all string properties
 * when no property is specified.
 * 
 * Usage examples:
 * - Basic filtering: *ngFor="let item of items | filter:'search text'"
 * - Property filtering: *ngFor="let item of items | filter:'search text':'title'"
 */
@Pipe({
  name: 'filter',
  pure: true // Pure pipe for better performance - only runs when input references change
})
export class FilterPipe implements PipeTransform {
  /**
   * Default constructor for the FilterPipe
   */
  constructor() {}

  /**
   * Transforms the input array by filtering it according to provided criteria.
   * 
   * @param items The array of items to filter
   * @param filterText The text to filter by
   * @param filterProperty Optional property name to filter on (if not provided, checks all string properties)
   * @returns Filtered array based on criteria
   */
  transform(items: any[], filterText: string, filterProperty?: string): any[] {
    // Check if items array exists and has elements
    if (!items || items.length === 0) {
      return items;
    }

    // Return original array if no filter text is provided
    if (!filterText || filterText.trim() === '') {
      return items;
    }

    // Convert filterText to lowercase for case-insensitive comparison
    const lowerFilterText = filterText.toLowerCase().trim();

    // If filterProperty is specified, filter items where that property contains filterText
    if (filterProperty) {
      return items.filter(item => {
        // Skip undefined/null items or items without the specified property
        if (!item || item[filterProperty] === undefined || item[filterProperty] === null) {
          return false;
        }
        
        // Convert property value to string and check if it contains the filter text
        const value = String(item[filterProperty]).toLowerCase();
        return value.includes(lowerFilterText);
      });
    } 
    // If no filterProperty is specified, check all string properties of each item
    else {
      return items.filter(item => {
        // Skip undefined/null items
        if (!item) {
          return false;
        }
        
        // Check all object properties
        return Object.keys(item).some(key => {
          // Skip null/undefined properties
          if (item[key] === undefined || item[key] === null) {
            return false;
          }
          
          // Only filter by string-compatible properties
          const value = item[key];
          if (typeof value === 'string' || typeof value === 'number' || value instanceof Date) {
            return String(value).toLowerCase().includes(lowerFilterText);
          }
          return false;
        });
      });
    }
  }
}