/**
 * StandupBot — Form validation helpers
 */

export function isValidEmail(email: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

export function isNotEmpty(value: string): boolean {
  return value.trim().length > 0;
}

export function isMinLength(value: string, min: number): boolean {
  return value.trim().length >= min;
}

export function isMaxLength(value: string, max: number): boolean {
  return value.trim().length <= max;
}

export interface ValidationResult {
  valid: boolean;
  error?: string;
}

export function validateRequired(value: string, fieldName: string): ValidationResult {
  if (!isNotEmpty(value)) {
    return { valid: false, error: `${fieldName} is required` };
  }
  return { valid: true };
}

export function validateEmail(email: string): ValidationResult {
  if (!isNotEmpty(email)) {
    return { valid: false, error: 'Email is required' };
  }
  if (!isValidEmail(email)) {
    return { valid: false, error: 'Please enter a valid email address' };
  }
  return { valid: true };
}
