/**
 * StandupBot — Submission Types
 */

export interface AnswerSubmit {
  question_id: string;
  answer_text: string;
}

export interface SubmissionCreateRequest {
  answers: AnswerSubmit[];
}

export interface StandupFormData {
  team_name: string;
  member_name: string;
  standup_date: string;
  questions: { id: string; text: string }[];
  already_submitted: boolean;
}

export interface AnswerResponse {
  question_id: string;
  question_text: string;
  answer_text: string;
}

export interface Submission {
  id: string;
  member_id: string;
  member_name: string;
  standup_date: string;
  is_late: boolean;
  submitted_at: string;
  answers: AnswerResponse[];
}

export interface SubmissionConfirmation {
  message: string;
  standup_date: string;
  submitted_at: string;
}
