/**
 * Shared parsing utilities for coin data.
 * 
 * These utilities handle the conversion of JSON strings or arrays
 * that come from the backend into properly typed arrays.
 */

/**
 * Parse a value that could be a JSON string array, an actual array, or null.
 * Used for iconography, control marks, and other array fields stored as JSON strings.
 * 
 * @param value - The value to parse (string, array, null, or undefined)
 * @param fallbackSplit - If true, try splitting comma-separated strings as fallback
 * @returns Array of strings or null if no valid data
 * 
 * @example
 * parseJsonArray('["eagle", "altar"]')  // ["eagle", "altar"]
 * parseJsonArray(["eagle", "altar"])     // ["eagle", "altar"]
 * parseJsonArray(null)                   // null
 * parseJsonArray("eagle, altar", true)   // ["eagle", "altar"]
 */
export function parseJsonArray(
  value: string | string[] | null | undefined,
  fallbackSplit = false
): string[] | null {
  if (!value) return null;
  if (Array.isArray(value)) return value.length > 0 ? value : null;
  
  // Try JSON parse first
  try {
    const parsed = JSON.parse(value);
    if (Array.isArray(parsed) && parsed.length > 0) {
      return parsed;
    }
    return null;
  } catch {
    // If JSON parse fails and fallback is enabled, try comma split
    if (fallbackSplit && typeof value === 'string' && value.trim()) {
      const items = value.split(',').map(s => s.trim()).filter(Boolean);
      return items.length > 0 ? items : null;
    }
    return null;
  }
}

/**
 * Parse control marks from backend data.
 * Alias for parseJsonArray with comma fallback enabled.
 * 
 * @param value - Control marks data
 * @returns Array of control mark strings or null
 */
export function parseControlMarks(
  value: string | string[] | null | undefined
): string[] | null {
  return parseJsonArray(value, true);
}

/**
 * Parse iconography elements from backend data.
 * 
 * @param value - Iconography data (JSON string or array)
 * @returns Array of iconography element strings or null
 */
export function parseIconography(
  value: string | string[] | null | undefined
): string[] | null {
  return parseJsonArray(value, false);
}

/**
 * Parse a JSON object string into an object.
 * Used for condition_observations and other JSON object fields.
 * 
 * @param value - JSON string or object
 * @returns Parsed object or null
 */
export function parseJsonObject<T extends object>(
  value: string | T | null | undefined
): T | null {
  if (!value) return null;
  if (typeof value === 'object') return value;
  
  try {
    const parsed = JSON.parse(value);
    return typeof parsed === 'object' && parsed !== null ? parsed : null;
  } catch {
    return null;
  }
}

/**
 * Type for condition observations parsed from JSON.
 */
export interface ConditionObservations {
  wear_observations?: string;
  surface_notes?: string;
  strike_quality?: string;
  notable_features?: string;
}

/**
 * Parse condition observations from backend JSON string.
 * 
 * @param value - Condition observations JSON string or object
 * @returns Parsed condition observations or null
 */
export function parseConditionObservations(
  value: string | ConditionObservations | null | undefined
): ConditionObservations | null {
  return parseJsonObject<ConditionObservations>(value);
}
