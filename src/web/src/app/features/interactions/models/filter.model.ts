import { InteractionType } from './interaction.model';

/**
 * Enum representing comparison operators for filters
 * These operators define how a field's value should be compared during filtering
 */
export enum FilterOperator {
  EQUALS = 'eq',
  NOT_EQUALS = 'neq',
  GREATER_THAN = 'gt',
  LESS_THAN = 'lt',
  GREATER_THAN_OR_EQUAL = 'gte',
  LESS_THAN_OR_EQUAL = 'lte',
  CONTAINS = 'contains',
  STARTS_WITH = 'startsWith',
  ENDS_WITH = 'endsWith',
  BETWEEN = 'between'
}

/**
 * Enum representing data types for filter fields
 * The field type determines what kind of input controls are shown in the filter UI
 */
export enum FilterFieldType {
  TEXT = 'text',
  NUMBER = 'number',
  DATE = 'date',
  DATETIME = 'datetime',
  SELECT = 'select',
  MULTI_SELECT = 'multiSelect'
}

/**
 * Enum defining all filterable fields on the Interaction entity
 * These values correspond to properties on the Interaction model
 */
export enum FilterableInteractionFields {
  TITLE = 'title',
  TYPE = 'type',
  LEAD = 'lead',
  START_DATETIME = 'startDatetime',
  END_DATETIME = 'endDatetime',
  TIMEZONE = 'timezone',
  LOCATION = 'location',
  DESCRIPTION = 'description',
  NOTES = 'notes',
  CREATED_AT = 'createdAt'
}

/**
 * Interface representing a single filter criterion with field, operator, and value
 * Used to build filter expressions for interaction searching
 */
export interface Filter {
  /** The field name to filter on */
  field: string;
  /** The comparison operator to apply */
  operator: FilterOperator;
  /** The value to compare against */
  value: any;
  /** Optional second value for operators like BETWEEN */
  toValue?: any;
}

/**
 * Interface defining a filterable field with its metadata
 * Used to build the filter UI and support field-specific filtering options
 */
export interface FilterField {
  /** The actual field name in the data model */
  field: string;
  /** User-friendly display name for the field */
  displayName: string;
  /** The data type of the field */
  type: FilterFieldType;
  /** Array of operators that can be used with this field */
  supportedOperators: FilterOperator[];
  /** Optional array of selectable options for SELECT and MULTI_SELECT fields */
  options?: any[];
}

/**
 * Interface representing a complete search query with filters and global search term
 * Used to send search requests to the API
 */
export interface SearchQuery {
  /** Free-text search term applied across multiple fields */
  globalSearch?: string;
  /** Array of specific filters to apply */
  filters?: Filter[];
  /** Current page for pagination */
  page: number;
  /** Number of items per page */
  pageSize: number;
  /** Field to sort results by */
  sortField?: string;
  /** Sort direction ('asc' or 'desc') */
  sortDirection?: string;
}

/**
 * Predefined filter field configurations for the Interaction entity
 * These configurations are used to build the filter UI in the Finder
 */
export const predefinedFilterFields: FilterField[] = [
  {
    field: FilterableInteractionFields.TITLE,
    displayName: 'Title',
    type: FilterFieldType.TEXT,
    supportedOperators: [
      FilterOperator.CONTAINS,
      FilterOperator.EQUALS,
      FilterOperator.STARTS_WITH,
      FilterOperator.ENDS_WITH,
    ]
  },
  {
    field: FilterableInteractionFields.TYPE,
    displayName: 'Type',
    type: FilterFieldType.SELECT,
    supportedOperators: [
      FilterOperator.EQUALS,
      FilterOperator.NOT_EQUALS
    ],
    options: [
      { value: InteractionType.MEETING, label: InteractionType.MEETING },
      { value: InteractionType.CALL, label: InteractionType.CALL },
      { value: InteractionType.EMAIL, label: InteractionType.EMAIL },
      { value: InteractionType.OTHER, label: InteractionType.OTHER }
    ]
  },
  {
    field: FilterableInteractionFields.LEAD,
    displayName: 'Lead',
    type: FilterFieldType.TEXT,
    supportedOperators: [
      FilterOperator.CONTAINS,
      FilterOperator.EQUALS,
      FilterOperator.STARTS_WITH
    ]
  },
  {
    field: FilterableInteractionFields.START_DATETIME,
    displayName: 'Start Date/Time',
    type: FilterFieldType.DATETIME,
    supportedOperators: [
      FilterOperator.EQUALS,
      FilterOperator.GREATER_THAN,
      FilterOperator.LESS_THAN,
      FilterOperator.BETWEEN
    ]
  },
  {
    field: FilterableInteractionFields.END_DATETIME,
    displayName: 'End Date/Time',
    type: FilterFieldType.DATETIME,
    supportedOperators: [
      FilterOperator.EQUALS,
      FilterOperator.GREATER_THAN,
      FilterOperator.LESS_THAN,
      FilterOperator.BETWEEN
    ]
  },
  {
    field: FilterableInteractionFields.TIMEZONE,
    displayName: 'Timezone',
    type: FilterFieldType.SELECT,
    supportedOperators: [
      FilterOperator.EQUALS,
      FilterOperator.NOT_EQUALS
    ],
    // Note: Actual timezone options would be populated dynamically or from a constants file
    options: []
  },
  {
    field: FilterableInteractionFields.LOCATION,
    displayName: 'Location',
    type: FilterFieldType.TEXT,
    supportedOperators: [
      FilterOperator.CONTAINS,
      FilterOperator.EQUALS
    ]
  },
  {
    field: FilterableInteractionFields.DESCRIPTION,
    displayName: 'Description',
    type: FilterFieldType.TEXT,
    supportedOperators: [
      FilterOperator.CONTAINS
    ]
  },
  {
    field: FilterableInteractionFields.NOTES,
    displayName: 'Notes',
    type: FilterFieldType.TEXT,
    supportedOperators: [
      FilterOperator.CONTAINS
    ]
  },
  {
    field: FilterableInteractionFields.CREATED_AT,
    displayName: 'Created Date',
    type: FilterFieldType.DATE,
    supportedOperators: [
      FilterOperator.EQUALS,
      FilterOperator.GREATER_THAN,
      FilterOperator.LESS_THAN,
      FilterOperator.BETWEEN
    ]
  }
];