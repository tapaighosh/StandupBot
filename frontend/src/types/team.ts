/**
 * StandupBot — Team Types
 */

export interface Question {
  id: string;
  text: string;
  order_index: number;
  is_active: boolean;
}

export interface QuestionCreate {
  text: string;
  order_index: number;
}

export interface TeamCreateRequest {
  name: string;
  timezone: string;
  reminder_time: string;
  digest_time: string;
  submission_window_start: string;
  submission_window_end: string;
  allow_late_submissions: boolean;
  questions: QuestionCreate[];
}

export interface TeamUpdateRequest {
  name?: string;
  timezone?: string;
  reminder_time?: string;
  digest_time?: string;
  submission_window_start?: string;
  submission_window_end?: string;
  allow_late_submissions?: boolean;
}

export interface Team {
  id: string;
  name: string;
  timezone: string;
  reminder_time: string;
  digest_time: string;
  submission_window_start: string;
  submission_window_end: string;
  allow_late_submissions: boolean;
  is_active: boolean;
  member_count: number;
  questions: Question[];
  created_at: string;
}

export interface TeamListItem {
  id: string;
  name: string;
  timezone: string;
  member_count: number;
  is_active: boolean;
  created_at: string;
}
