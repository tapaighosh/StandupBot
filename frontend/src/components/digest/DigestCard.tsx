/**
 * StandupBot — DigestCard Component
 *
 * Summary card for digest list items.
 * Shows date, response count, color-coded rate badge, and status.
 */

import { useNavigate } from 'react-router-dom';
import './DigestCard.css';

interface DigestCardProps {
  id: string;
  digestDate: string;
  totalMembers: number;
  respondedCount: number;
  responseRate: number;
  status: string;
  sentAt: string | null;
}

function getRateBadge(rate: number): { class: string; label: string } {
  if (rate >= 80) return { class: 'digest-card__rate--high', label: '🟢' };
  if (rate >= 50) return { class: 'digest-card__rate--mid', label: '🟡' };
  return { class: 'digest-card__rate--low', label: '🔴' };
}

function getStatusBadge(status: string): { class: string; label: string } {
  switch (status) {
    case 'sent':
      return { class: 'digest-card__status--sent', label: 'Sent' };
    case 'failed':
      return { class: 'digest-card__status--failed', label: 'Failed' };
    default:
      return { class: 'digest-card__status--pending', label: 'Pending' };
  }
}

export function DigestCard({
  id,
  digestDate,
  totalMembers,
  respondedCount,
  responseRate,
  status,
}: DigestCardProps) {
  const navigate = useNavigate();
  const rate = getRateBadge(responseRate);
  const statusBadge = getStatusBadge(status);

  const formattedDate = new Date(digestDate + 'T00:00:00').toLocaleDateString('en-US', {
    weekday: 'short',
    month: 'short',
    day: 'numeric',
  });

  const fullDate = new Date(digestDate + 'T00:00:00').toLocaleDateString('en-US', {
    weekday: 'long',
    month: 'long',
    day: 'numeric',
    year: 'numeric',
  });

  return (
    <button
      className="digest-card"
      onClick={() => navigate(`/dashboard/digests/${id}`)}
      title={`View digest for ${fullDate}`}
    >
      {/* Date */}
      <div className="digest-card__date">
        <span className="digest-card__date-text">{formattedDate}</span>
      </div>

      {/* Response rate visual */}
      <div className="digest-card__stats">
        <div className="digest-card__bar-container">
          <div
            className={`digest-card__bar-fill ${rate.class}`}
            style={{ width: `${responseRate}%` }}
          />
        </div>
        <span className="digest-card__rate-text">
          {rate.label} {responseRate}%
        </span>
      </div>

      {/* Count */}
      <div className="digest-card__count">
        <span className="digest-card__count-value">
          {respondedCount}/{totalMembers}
        </span>
        <span className="digest-card__count-label">responded</span>
      </div>

      {/* Status */}
      <span className={`digest-card__status ${statusBadge.class}`}>
        {statusBadge.label}
      </span>

      {/* Arrow */}
      <span className="digest-card__arrow">→</span>
    </button>
  );
}
