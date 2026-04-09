/**
 * StandupBot — Teams API
 */

import apiClient from './client';
import type { Team, TeamCreateRequest, TeamListItem, TeamUpdateRequest, Question } from '../types/team';
import type { Member, MemberInviteRequest } from '../types/member';
import type { MessageResponse } from '../types/api';

export const teamsApi = {
  create: (data: TeamCreateRequest) =>
    apiClient.post<Team>('/v1/teams/', data),

  list: () =>
    apiClient.get<TeamListItem[]>('/v1/teams/'),

  get: (teamId: string) =>
    apiClient.get<Team>(`/v1/teams/${teamId}`),

  update: (teamId: string, data: TeamUpdateRequest) =>
    apiClient.put<Team>(`/v1/teams/${teamId}`, data),

  delete: (teamId: string) =>
    apiClient.delete<MessageResponse>(`/v1/teams/${teamId}`),

  // Members
  inviteMember: (teamId: string, data: MemberInviteRequest) =>
    apiClient.post<Member>(`/v1/teams/${teamId}/members`, data),

  listMembers: (teamId: string) =>
    apiClient.get<Member[]>(`/v1/teams/${teamId}/members`),

  removeMember: (teamId: string, memberId: string) =>
    apiClient.delete<MessageResponse>(`/v1/teams/${teamId}/members/${memberId}`),

  // Questions
  getQuestions: (teamId: string) =>
    apiClient.get<Question[]>(`/v1/teams/${teamId}/questions`),

  updateQuestions: (teamId: string, questions: { text: string; order_index: number }[]) =>
    apiClient.put<Question[]>(`/v1/teams/${teamId}/questions`, questions),
};
