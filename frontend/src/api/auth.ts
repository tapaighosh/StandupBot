/**
 * StandupBot — Auth API
 */

import apiClient from './client';

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface UserProfile {
  id: string;
  email: string;
  name: string;
  avatar_url: string | null;
  is_active: boolean;
  created_at: string;
}

export const authApi = {
  loginWithGoogle: (credential: string) =>
    apiClient.post<TokenResponse>('/v1/auth/login/google', { credential }),

  refreshToken: (refreshToken: string) =>
    apiClient.post<TokenResponse>('/v1/auth/refresh', { refresh_token: refreshToken }),

  logout: () =>
    apiClient.post('/v1/auth/logout'),

  getMe: () =>
    apiClient.get<UserProfile>('/v1/auth/me'),
};
