/**
 * StandupBot — DigestView Component
 *
 * Full digest detail view, structured like a clean email digest.
 *
 * LAYOUT:
 *   - AI Summary (gradient card)
 *   - Response Rate bar
 *   - Blockers section (red-highlighted)
 *   - Non-responders section (grey)
 *   - Member responses (collapsible cards)
 */

import { AISummary } from './AISummary';
import './DigestView.css';

interface BlockerEntry {
  member_name: string;
  answer_text: string;
  detection: string;
}

interface DigestData {
  id: string;
  team_id: string;
  digest_date: string;
  ai_summary: string | null;
  total_members: number;
  responded_count: number;
  response_rate: number;
  non_responders: string[];
  blockers: BlockerEntry[];
  status: string;
  created_at: string;
}

interface DigestViewProps {
  digest: DigestData;
  onBack?: () => void;
}

export function DigestView({ digest, onBack }: DigestViewProps) {
  const formattedDate = new Date(digest.digest_date + 'T00:00:00').toLocaleDateString('en-US', {
    weekday: 'long',
    month: 'long',
    day: 'numeric',
    year: 'numeric',
  });

  const rateColor =
    digest.response_rate >= 80 ? 'var(--color-success)' :
    digest.response_rate >= 50 ? 'var(--color-warning)' :
    'var(--color-danger)';

  return (
    <div className="digest-view">
      {/* ── Header ── */}
      <div className="digest-view__header">
        {onBack && (
          <button className="digest-view__back" onClick={onBack}>
            ← Back to Digests
          </button>
        )}
        <h1 className="digest-view__title">📋 Daily Digest</h1>
        <p className="digest-view__date">{formattedDate}</p>
      </div>

      {/* ── Response Rate Bar ── */}
      <div className="digest-view__rate-section">
        <div className="digest-view__rate-header">
          <span className="digest-view__rate-label">Response Rate</span>
          <span className="digest-view__rate-value" style={{ color: rateColor }}>
            {digest.response_rate}%
          </span>
        </div>
        <div className="digest-view__rate-bar">
          <div
            className="digest-view__rate-fill"
            style={{
              width: `${digest.response_rate}%`,
              background: `linear-gradient(90deg, ${rateColor}, ${rateColor}88)`,
            }}
          />
        </div>
        <span className="digest-view__rate-count">
          {digest.responded_count} of {digest.total_members} members responded
        </span>
      </div>

      {/* ── AI Summary ── */}
      <AISummary summary={digest.ai_summary} />

      {/* ── Blockers Section ── */}
      {digest.blockers.length > 0 && (
        <div className="digest-view__section digest-view__blockers">
          <h2 className="digest-view__section-title">
            <span>🚧</span> Blockers ({digest.blockers.length})
          </h2>
          <div className="digest-view__blocker-list stagger-children">
            {digest.blockers.map((blocker, i) => (
              <div key={i} className="digest-view__blocker-item">
                <span className="digest-view__blocker-name">{blocker.member_name}</span>
                <p className="digest-view__blocker-text">{blocker.answer_text}</p>
                <span className="digest-view__blocker-badge">
                  {blocker.detection === 'llm' ? '🤖 AI detected' : '🔍 Keyword match'}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── Non-Responders ── */}
      {digest.non_responders.length > 0 && (
        <div className="digest-view__section digest-view__non-responders">
          <h2 className="digest-view__section-title">
            <span>😶</span> Did Not Respond ({digest.non_responders.length})
          </h2>
          <div className="digest-view__nr-list">
            {digest.non_responders.map((name, i) => (
              <div key={i} className="digest-view__nr-item">
                <span className="digest-view__nr-dot" />
                <span className="digest-view__nr-name">{name}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── No Blockers Positive State ── */}
      {digest.blockers.length === 0 && digest.responded_count > 0 && (
        <div className="digest-view__section digest-view__no-blockers">
          <span className="digest-view__no-blockers-icon">✨</span>
          <p className="digest-view__no-blockers-text">
            No blockers reported today — the team is moving smoothly!
          </p>
        </div>
      )}
    </div>
  );
}
