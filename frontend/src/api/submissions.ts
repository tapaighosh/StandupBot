/**
 * StandupBot — Submissions API
 */

import apiClient from './client';
import type { StandupFormData, SubmissionConfirmation, SubmissionCreateRequest } from '../types/submission';

export const submissionsApi = {
  loadForm: (token: string) =>
    apiClient.get<StandupFormData>(`/v1/submissions/form/${token}`),

  submitStandup: (token: string, data: SubmissionCreateRequest) =>
    apiClient.post<SubmissionConfirmation>(`/v1/submissions/form/${token}`, data),
};
