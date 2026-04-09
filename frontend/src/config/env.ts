/**
 * StandupBot — Type-safe Environment Variables
 */

interface EnvConfig {
  API_BASE_URL: string;
  APP_NAME: string;
  GOOGLE_CLIENT_ID: string;
}

export const env: EnvConfig = {
  API_BASE_URL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api',
  APP_NAME: import.meta.env.VITE_APP_NAME || 'StandupBot',
  GOOGLE_CLIENT_ID: import.meta.env.VITE_GOOGLE_CLIENT_ID || '',
};
