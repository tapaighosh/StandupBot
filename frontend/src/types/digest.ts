/**
 * StandupBot — Digest Types
 */

export interface DigestMemberEntry {
  member_id: string;
  member_name: string;
  submitted: boolean;
  has_blocker: boolean;
  answers: { question: string; answer: string }[];
}

export interface Digest {
  id: string;
  team_id: string;
  digest_date: string;
  ai_summary: string | null;
  total_members: number;
  responded_count: number;
  response_rate: number;
  non_responders: string[];
  blockers: { member: string; text: string }[];
  entries: DigestMemberEntry[];
  status: string;
  sent_at: string | null;
  created_at: string;
}

export interface DigestListItem {
  id: string;
  digest_date: string;
  total_members: number;
  responded_count: number;
  response_rate: number;
  status: string;
  sent_at: string | null;
}

export interface TeamStats {
  team_id: string;
  period_days: number;
  average_response_rate: number;
  total_standups: number;
  total_blockers: number;
  member_stats: { member_id: string; name: string; response_rate: number }[];
}

export interface BlockerTrend {
  team_id: string;
  period_days: number;
  total_blockers: number;
  trend_data: { date: string; count: number }[];
  common_themes: string[];
}
