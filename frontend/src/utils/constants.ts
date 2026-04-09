/**
 * StandupBot — App-wide constants
 */

export const APP_NAME = 'StandupBot';

export const DEFAULT_QUESTIONS = [
  'What did you accomplish yesterday?',
  'What are you working on today?',
  'Any blockers or help needed?',
];

export const PLAN_NAMES = {
  free: 'Free',
  starter: 'Starter',
  growth: 'Growth',
} as const;

export const PLAN_PRICES = {
  free: '$0',
  starter: '$12/mo',
  growth: '$29/mo',
} as const;

export const TIMEZONE_OPTIONS = [
  'UTC',
  'America/New_York',
  'America/Chicago',
  'America/Denver',
  'America/Los_Angeles',
  'Europe/London',
  'Europe/Berlin',
  'Europe/Paris',
  'Asia/Tokyo',
  'Asia/Shanghai',
  'Asia/Kolkata',
  'Australia/Sydney',
] as const;
