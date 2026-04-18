/**
 * StandupBot — StandupForm Component
 *
 * The core form where team members answer their standup questions.
 *
 * KEY UX DECISIONS:
 * 1. Auto-save drafts to localStorage on every keystroke
 *    → If the member accidentally closes the tab, their answers are preserved
 * 2. All questions on one page (no wizard/stepper)
 *    → Fewer taps on mobile, completes faster
 * 3. Textareas auto-grow to fit content
 *    → No scrolling inside tiny boxes
 * 4. Submit button disabled until all answers are non-empty
 *    → Clear visual feedback on what's missing
 */

import { useState, useEffect, useCallback } from 'react';
import './StandupForm.css';

interface Question {
  id: string;
  text: string;
  order_index: number;
}

interface StandupFormProps {
  questions: Question[];
  token: string;
  onSubmit: (answers: { question_id: string; answer_text: string }[]) => Promise<void>;
}

export function StandupForm({ questions, token, onSubmit }: StandupFormProps) {
  // Draft key is unique per token so different days don't conflict
  const draftKey = `standup-draft-${token.slice(-12)}`;

  // Initialize answers from localStorage draft or empty
  const [answers, setAnswers] = useState<Record<string, string>>(() => {
    try {
      const saved = localStorage.getItem(draftKey);
      if (saved) return JSON.parse(saved);
    } catch {
      // Corrupted draft — start fresh
    }
    // Initialize with empty strings for each question
    const initial: Record<string, string> = {};
    questions.forEach((q) => {
      initial[q.id] = '';
    });
    return initial;
  });

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Auto-save drafts to localStorage on every change
  useEffect(() => {
    localStorage.setItem(draftKey, JSON.stringify(answers));
  }, [answers, draftKey]);

  const handleChange = useCallback((questionId: string, value: string) => {
    setAnswers((prev) => ({ ...prev, [questionId]: value }));
  }, []);

  // Check if all questions have non-empty answers
  const allAnswered = questions.every(
    (q) => (answers[q.id] || '').trim().length > 0
  );

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!allAnswered || isSubmitting) return;

    setIsSubmitting(true);
    setError(null);

    try {
      const formattedAnswers = questions.map((q) => ({
        question_id: q.id,
        answer_text: answers[q.id].trim(),
      }));

      await onSubmit(formattedAnswers);

      // Clear draft after successful submission
      localStorage.removeItem(draftKey);
    } catch (err: any) {
      setError(err?.detail || 'Failed to submit. Please try again.');
      setIsSubmitting(false);
    }
  };

  // Count answered questions for progress indicator
  const answeredCount = questions.filter(
    (q) => (answers[q.id] || '').trim().length > 0
  ).length;

  return (
    <form className="standup-form" onSubmit={handleSubmit}>
      {/* Progress indicator */}
      <div className="standup-form__progress">
        <div className="standup-form__progress-bar">
          <div
            className="standup-form__progress-fill"
            style={{ width: `${(answeredCount / questions.length) * 100}%` }}
          />
        </div>
        <span className="standup-form__progress-text">
          {answeredCount} of {questions.length} answered
        </span>
      </div>

      {/* Questions */}
      <div className="standup-form__questions">
        {questions.map((question, index) => (
          <div key={question.id} className="standup-form__question">
            <label
              className="standup-form__label"
              htmlFor={`q-${question.id}`}
            >
              <span className="standup-form__question-number">{index + 1}</span>
              {question.text}
            </label>
            <textarea
              id={`q-${question.id}`}
              className="standup-form__textarea"
              value={answers[question.id] || ''}
              onChange={(e) => handleChange(question.id, e.target.value)}
              placeholder="Type your answer..."
              rows={3}
              autoFocus={index === 0}
            />
          </div>
        ))}
      </div>

      {/* Error message */}
      {error && (
        <div className="standup-form__error">
          <span>⚠️</span> {error}
        </div>
      )}

      {/* Submit button */}
      <button
        type="submit"
        className={`standup-form__submit ${allAnswered ? 'standup-form__submit--ready' : ''}`}
        disabled={!allAnswered || isSubmitting}
      >
        {isSubmitting ? (
          <>
            <span className="standup-form__spinner" />
            Submitting...
          </>
        ) : allAnswered ? (
          'Submit Standup ✓'
        ) : (
          `Answer all ${questions.length} questions to submit`
        )}
      </button>
    </form>
  );
}
