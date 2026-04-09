/**
 * StandupBot — Member Types
 */

export interface Member {
  id: string;
  email: string;
  name: string;
  is_active: boolean;
  created_at: string;
}

export interface MemberInviteRequest {
  email: string;
  name: string;
}
