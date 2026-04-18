/**
 * StandupBot — StandupSubmit Page
 *
 * The public page members reach via magic link.
 * URL pattern: /standup/{token}
 *
 * STATE MACHINE:
 *   loading → form | error | already_submitted
 *   form → submitting → submitted | error
 *
 * This page handles all states:
 * 1. Loading: fetching form data from API
 * 2. Error: expired/used/invalid token
 * 3. Form: the actual standup form
 * 4. Already submitted: shows "done" message
 * 5. Submitted: success confirmation
 */

import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import apiClient from '../api/client';
import { StandupForm } from '../components/standup/StandupForm';
import { SubmitConfirmation } from '../components/standup/SubmitConfirmation';
import { Spinner } from '../components/ui/Spinner';
import './StandupSubmit.css';

// ── Types matching the backend schema ──

interface Question {
  id: string;
  text: string;
  order_index: number;
}

interface FormData {
  team_name: string;
  member_name: string;
  standup_date: string;
  questions: Question[];
  already_submitted: boolean;
}

interface SubmitResult {
  message: string;
  standup_date: string;
  submitted_at: string;
}

type PageState = 'loading' | 'form' | 'already_submitted' | 'submitted' | 'error';

// ── Error code to user-friendly message mapping ──
function getErrorMessage(code: string, detail: string): { icon: string; title: string; message: string } {
  switch (code) {
    case 'TOKEN_EXPIRED':
      return {
        icon: '⏰',
        title: 'Link Expired',
        message: 'This standup link has expired. Contact your team lead for a new one.',
      };
    case 'TOKEN_ALREADY_USED':
      return {
        icon: '✅',
        title: 'Already Submitted',
        message: "You've already submitted your standup for today. See you tomorrow!",
      };
    case 'SUBMISSION_WINDOW_CLOSED':
      return {
        icon: '🔒',
        title: 'Window Closed',
        message: "The submission window has closed for today. Try again tomorrow!",
      };
    default:
      return {
        icon: '❌',
        title: 'Invalid Link',
        message: detail || 'This standup link is invalid. Please check the link and try again.',
      };
  }
}

export function StandupSubmit() {
  const { token } = useParams<{ token: string }>();
  const [state, setState] = useState<PageState>('loading');
  const [formData, setFormData] = useState<FormData | null>(null);
  const [submitResult, setSubmitResult] = useState<SubmitResult | null>(null);
  const [error, setError] = useState<{ icon: string; title: string; message: string } | null>(null);

  // Load form on mount
  useEffect(() => {
    if (!token) {
      setError({ icon: '❌', title: 'Missing Link', message: 'No token provided.' });
      setState('error');
      return;
    }

    loadForm(token);
  }, [token]);

  async function loadForm(tokenStr: string) {
    try {
      const response = await apiClient.get<FormData>(`/v1/submissions/form/${tokenStr}`);
      const data = response.data;
      setFormData(data);

      if (data.already_submitted) {
        setState('already_submitted');
      } else {
        setState('form');
      }
    } catch (err: any) {
      const code = err?.code || '';
      const detail = err?.detail || 'Something went wrong.';
      setError(getErrorMessage(code, detail));
      setState('error');
    }
  }

  async function handleSubmit(answers: { question_id: string; answer_text: string }[]) {
    if (!token) return;

    const response = await apiClient.post<SubmitResult>(
      `/v1/submissions/form/${token}`,
      { answers }
    );
    setSubmitResult(response.data);
    setState('submitted');
  }

  return (
    <div className="standup-page">
      {/* Background orbs (same as login — consistent brand) */}
      <div className="standup-page__bg" aria-hidden="true">
        <div className="standup-page__orb standup-page__orb--1" />
        <div className="standup-page__orb standup-page__orb--2" />
      </div>

      <div className="standup-page__card">
        {/* ── Loading State ── */}
        {state === 'loading' && (
          <div className="standup-page__center">
            <Spinner size="lg" label="Loading your standup..." />
          </div>
        )}

        {/* ── Error State ── */}
        {state === 'error' && error && (
          <div className="standup-page__status animate-fade-in-up">
            <span className="standup-page__status-icon">{error.icon}</span>
            <h2 className="standup-page__status-title">{error.title}</h2>
            <p className="standup-page__status-message">{error.message}</p>
          </div>
        )}

        {/* ── Already Submitted State ── */}
        {state === 'already_submitted' && formData && (
          <div className="standup-page__status animate-fade-in-up">
            <span className="standup-page__status-icon">✅</span>
            <h2 className="standup-page__status-title">Already Submitted</h2>
            <p className="standup-page__status-message">
              You&apos;ve already submitted your standup for{' '}
              {new Date(formData.standup_date + 'T00:00:00').toLocaleDateString('en-US', {
                weekday: 'long',
                month: 'long',
                day: 'numeric',
              })}
              . See you tomorrow! 👋
            </p>
          </div>
        )}

        {/* ── Form State ── */}
        {state === 'form' && formData && (
          <>
            <div className="standup-page__header">
              <span className="standup-page__emoji">✍️</span>
              <h1 className="standup-page__title">Daily Standup</h1>
              <p className="standup-page__meta">
                <span className="standup-page__team">{formData.team_name}</span>
                {' · '}
                <span>Hi, {formData.member_name.split(' ')[0]}!</span>
                {' · '}
                <span>
                  {new Date(formData.standup_date + 'T00:00:00').toLocaleDateString('en-US', {
                    month: 'short',
                    day: 'numeric',
                  })}
                </span>
              </p>
            </div>

            <StandupForm
              questions={formData.questions}
              token={token!}
              onSubmit={handleSubmit}
            />
          </>
        )}

        {/* ── Submitted State ── */}
        {state === 'submitted' && submitResult && (
          <SubmitConfirmation
            standupDate={submitResult.standup_date}
            submittedAt={submitResult.submitted_at}
          />
        )}
      </div>
    </div>
  );
}
