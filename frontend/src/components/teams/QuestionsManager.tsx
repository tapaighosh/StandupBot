/**
 * StandupBot — QuestionsManager Component
 *
 * Allows managers to view, add, edit, reorder, and delete standup questions.
 * Saves via teamsApi.updateQuestions() (replaces the full question set).
 */

import { useState, useEffect } from 'react';
import { teamsApi } from '../../api/teams';
import type { Question } from '../../types/team';
import { Button } from '../ui/Button';
import './QuestionsManager.css';

interface QuestionsManagerProps {
  teamId: string;
  initialQuestions: Question[];
}

interface DraftQuestion {
  id?: string;       // undefined for newly added questions
  text: string;
  order_index: number;
}

export function QuestionsManager({
  teamId,
  initialQuestions,
}: QuestionsManagerProps) {
  const [questions, setQuestions] = useState<DraftQuestion[]>([]);
  const [isSaving, setIsSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [saveSuccess, setSaveSuccess] = useState(false);

  // Sync from parent when initialQuestions change
  useEffect(() => {
    setQuestions(
      initialQuestions
        .filter((q) => q.is_active)
        .sort((a, b) => a.order_index - b.order_index)
        .map((q) => ({ id: q.id, text: q.text, order_index: q.order_index }))
    );
  }, [initialQuestions]);

  // ── Helpers ──────────────────────────────────────────────────────
  const updateText = (index: number, text: string) => {
    setQuestions((prev) =>
      prev.map((q, i) => (i === index ? { ...q, text } : q))
    );
  };

  const addQuestion = () => {
    setQuestions((prev) => [
      ...prev,
      { text: '', order_index: prev.length },
    ]);
  };

  const removeQuestion = (index: number) => {
    setQuestions((prev) =>
      prev
        .filter((_, i) => i !== index)
        .map((q, i) => ({ ...q, order_index: i }))
    );
  };

  const moveUp = (index: number) => {
    if (index === 0) return;
    setQuestions((prev) => {
      const next = [...prev];
      [next[index - 1], next[index]] = [next[index], next[index - 1]];
      return next.map((q, i) => ({ ...q, order_index: i }));
    });
  };

  const moveDown = (index: number) => {
    if (index === questions.length - 1) return;
    setQuestions((prev) => {
      const next = [...prev];
      [next[index], next[index + 1]] = [next[index + 1], next[index]];
      return next.map((q, i) => ({ ...q, order_index: i }));
    });
  };

  // ── Save ─────────────────────────────────────────────────────────
  const handleSave = async () => {
    const nonEmpty = questions.filter((q) => q.text.trim());
    if (nonEmpty.length === 0) {
      setSaveError('At least one question is required.');
      return;
    }

    setIsSaving(true);
    setSaveError(null);
    setSaveSuccess(false);

    try {
      await teamsApi.updateQuestions(
        teamId,
        nonEmpty.map((q, i) => ({ text: q.text.trim(), order_index: i }))
      );
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (err: unknown) {
      const apiErr = err as { detail?: string };
      setSaveError(apiErr?.detail ?? 'Failed to save questions.');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="questions-manager">
      <div className="questions-manager__header">
        <div>
          <h4 className="questions-manager__title">Standup Questions</h4>
          <p className="questions-manager__subtitle">
            These questions are sent to every team member daily. Updating them
            replaces the full set.
          </p>
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={addQuestion}
          icon={<span>＋</span>}
        >
          Add Question
        </Button>
      </div>

      {/* ── Question List ── */}
      <ol className="questions-manager__list">
        {questions.map((q, index) => (
          <li key={q.id ?? `new-${index}`} className="questions-manager__item">
            {/* Drag handle / reorder arrows */}
            <div className="questions-manager__arrows">
              <button
                className="questions-manager__arrow-btn"
                onClick={() => moveUp(index)}
                disabled={index === 0}
                aria-label="Move question up"
                title="Move up"
              >
                ↑
              </button>
              <span className="questions-manager__number">{index + 1}</span>
              <button
                className="questions-manager__arrow-btn"
                onClick={() => moveDown(index)}
                disabled={index === questions.length - 1}
                aria-label="Move question down"
                title="Move down"
              >
                ↓
              </button>
            </div>

            {/* Text area */}
            <textarea
              id={`question-${index}`}
              className="questions-manager__textarea"
              value={q.text}
              onChange={(e) => updateText(index, e.target.value)}
              placeholder="Enter your standup question…"
              rows={2}
              maxLength={500}
              aria-label={`Question ${index + 1}`}
            />

            {/* Remove */}
            <button
              className="questions-manager__remove-btn"
              onClick={() => removeQuestion(index)}
              aria-label={`Remove question ${index + 1}`}
              title="Remove"
            >
              ✕
            </button>
          </li>
        ))}
      </ol>

      {questions.length === 0 && (
        <div className="questions-manager__empty">
          <div className="questions-manager__empty-icon">📋</div>
          <p>No questions yet. Add one to get started.</p>
        </div>
      )}

      {/* ── Feedback ── */}
      {saveError && (
        <div className="questions-manager__alert questions-manager__alert--error" role="alert">
          ⚠️ {saveError}
        </div>
      )}
      {saveSuccess && (
        <div className="questions-manager__alert questions-manager__alert--success" role="status">
          ✓ Questions saved successfully!
        </div>
      )}

      {/* ── Save button ── */}
      <div className="questions-manager__actions">
        <Button
          variant="primary"
          onClick={handleSave}
          loading={isSaving}
          disabled={questions.length === 0}
        >
          Save Questions
        </Button>
      </div>
    </div>
  );
}
