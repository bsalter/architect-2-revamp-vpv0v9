import { Site } from '../../sites/models/site.model';
import { format } from 'date-fns'; // date-fns v2.30.0

/**
 * Enumeration of allowed interaction types in the system.
 */
export enum InteractionType {
  MEETING = 'Meeting',
  CALL = 'Call',
  EMAIL = 'Email',
  OTHER = 'Other'
}

/**
 * Represents a complete interaction record in the system.
 * This is the core data structure used throughout the application.
 */
export interface Interaction {
  /** Unique identifier for the interaction */
  id: number;
  /** ID of the site this interaction belongs to */
  siteId: number;
  /** Title/subject of the interaction */
  title: string;
  /** Type of interaction (meeting, call, email, etc.) */
  type: InteractionType;
  /** Primary person leading the interaction */
  lead: string;
  /** Start date and time of the interaction */
  startDatetime: Date;
  /** End date and time of the interaction */
  endDatetime: Date;
  /** Timezone the interaction takes place in */
  timezone: string;
  /** Physical or virtual location of the interaction */
  location: string;
  /** Detailed description of the interaction */
  description: string;
  /** Additional notes about the interaction */
  notes: string;
  /** ID of the user who created the interaction */
  createdBy: number;
  /** When the interaction was created */
  createdAt: Date;
  /** When the interaction was last updated */
  updatedAt: Date;
  /** Associated site information */
  site?: Site;
}

/**
 * Interface for creating a new interaction.
 * Excludes system-generated fields like id, createdBy, and timestamps.
 */
export interface InteractionCreate {
  /** ID of the site this interaction belongs to */
  siteId: number;
  /** Title/subject of the interaction */
  title: string;
  /** Type of interaction (meeting, call, email, etc.) */
  type: InteractionType;
  /** Primary person leading the interaction */
  lead: string;
  /** Start date and time of the interaction */
  startDatetime: Date;
  /** End date and time of the interaction */
  endDatetime: Date;
  /** Timezone the interaction takes place in */
  timezone: string;
  /** Physical or virtual location of the interaction */
  location: string;
  /** Detailed description of the interaction */
  description: string;
  /** Additional notes about the interaction */
  notes: string;
}

/**
 * Interface for updating an existing interaction.
 * Excludes system-generated fields and immutable properties like siteId.
 */
export interface InteractionUpdate {
  /** Title/subject of the interaction */
  title: string;
  /** Type of interaction (meeting, call, email, etc.) */
  type: InteractionType;
  /** Primary person leading the interaction */
  lead: string;
  /** Start date and time of the interaction */
  startDatetime: Date;
  /** End date and time of the interaction */
  endDatetime: Date;
  /** Timezone the interaction takes place in */
  timezone: string;
  /** Physical or virtual location of the interaction */
  location: string;
  /** Detailed description of the interaction */
  description: string;
  /** Additional notes about the interaction */
  notes: string;
}

/**
 * API response format for single interaction operations.
 */
export interface InteractionResponse {
  /** The interaction data */
  interaction: Interaction;
}

/**
 * API response format for interaction list operations.
 * Includes pagination metadata.
 */
export interface InteractionListResponse {
  /** Array of interaction records */
  interactions: Interaction[];
  /** Total number of interactions matching the query */
  total: number;
  /** Current page number */
  page: number;
  /** Number of items per page */
  pageSize: number;
  /** Total number of pages */
  pages: number;
}

/**
 * Interface for representing interaction type options in dropdowns and filters.
 */
export interface InteractionTypeOption {
  /** The interaction type enum value */
  value: InteractionType;
  /** Human-readable label for the interaction type */
  label: string;
}

/**
 * Predefined options for interaction type selection controls.
 */
export const INTERACTION_TYPE_OPTIONS: InteractionTypeOption[] = [
  { value: InteractionType.MEETING, label: 'Meeting' },
  { value: InteractionType.CALL, label: 'Call' },
  { value: InteractionType.EMAIL, label: 'Email' },
  { value: InteractionType.OTHER, label: 'Other' }
];

/**
 * Formats the duration between start and end times as a human-readable string.
 * 
 * @param startDatetime The start date and time
 * @param endDatetime The end date and time
 * @returns A formatted duration string (e.g., "1 hour 30 minutes")
 */
export function getDurationString(startDatetime: Date, endDatetime: Date): string {
  if (!startDatetime || !endDatetime) {
    return '';
  }

  const durationMs = endDatetime.getTime() - startDatetime.getTime();
  if (durationMs <= 0) {
    return '';
  }

  const hours = Math.floor(durationMs / (1000 * 60 * 60));
  const minutes = Math.floor((durationMs % (1000 * 60 * 60)) / (1000 * 60));

  if (hours === 0) {
    return `${minutes} minute${minutes !== 1 ? 's' : ''}`;
  } else if (minutes === 0) {
    return `${hours} hour${hours !== 1 ? 's' : ''}`;
  } else {
    return `${hours} hour${hours !== 1 ? 's' : ''} ${minutes} minute${minutes !== 1 ? 's' : ''}`;
  }
}

/**
 * Formats an interaction date/time consistently across the application.
 * 
 * @param datetime The date and time to format
 * @param includeTime Whether to include the time component
 * @returns A formatted date/time string
 */
export function formatInteractionDatetime(datetime: Date, includeTime = true): string {
  if (!datetime) {
    return '';
  }

  try {
    return includeTime
      ? format(datetime, 'MMM d, yyyy h:mm a') // e.g., "Jun 15, 2023 10:30 AM"
      : format(datetime, 'MMM d, yyyy');       // e.g., "Jun 15, 2023"
  } catch (error) {
    console.error('Error formatting datetime:', error);
    return 'Invalid date';
  }
}