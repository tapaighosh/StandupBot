/**
 * StandupBot — Digests API
 */

import apiClient from './client';
import type { Digest, DigestListItem } from '../types/digest';
import type { MessageResponse } from '../types/api';

export const digestsApi = {
  getToday: (teamId: string) =>
    apiClient.get<Digest | null>(`/v1/digests/${teamId}/today`),

  getHistory: (teamId: string, page = 1, pageSize = 20) =>
    apiClient.get<DigestListItem[]>(`/v1/digests/${teamId}/history`, {
      params: { page, page_size: pageSize },
    }),

  getById: (teamId: string, digestId: string) =>
    apiClient.get<Digest>(`/v1/digests/${teamId}/${digestId}`),

  trigger: (teamId: string) =>
    apiClient.post<MessageResponse>(`/v1/digests/${teamId}/trigger`),
};
