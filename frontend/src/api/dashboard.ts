/**
 * StandupBot — Dashboard API
 */

import apiClient from './client';
import type { TeamStats, BlockerTrend } from '../types/digest';

export const dashboardApi = {
  getStats: (teamId: string, periodDays = 30) =>
    apiClient.get<TeamStats>(`/v1/dashboard/${teamId}/stats`, {
      params: { period_days: periodDays },
    }),

  getBlockerTrends: (teamId: string, periodDays = 30) =>
    apiClient.get<BlockerTrend>(`/v1/dashboard/${teamId}/blockers`, {
      params: { period_days: periodDays },
    }),

  exportData: (teamId: string, format: 'csv' | 'pdf' = 'csv') =>
    apiClient.get(`/v1/dashboard/${teamId}/export`, {
      params: { format },
      responseType: 'blob',
    }),
};
