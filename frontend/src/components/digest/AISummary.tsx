/**
 * StandupBot — AISummary Component
 *
 * Styled card for the AI-generated digest summary.
 * Gradient border, subtle glow, "AI Generated" badge.
 * Shows fallback message if summary is null.
 */

import './AISummary.css';

interface AISummaryProps {
  summary: string | null;
}

export function AISummary({ summary }: AISummaryProps) {
  return (
    <div className="ai-summary">
      <div className="ai-summary__badge">
        <span className="ai-summary__badge-icon">✨</span>
        <span className="ai-summary__badge-text">AI Generated</span>
      </div>

      {summary ? (
        <p className="ai-summary__text">{summary}</p>
      ) : (
        <div className="ai-summary__fallback">
          <span className="ai-summary__fallback-icon">📝</span>
          <p className="ai-summary__fallback-text">
            AI summary unavailable for this digest. The raw submissions
            are still available below.
          </p>
        </div>
      )}
    </div>
  );
}
