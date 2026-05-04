/**
 * StandupBot — TeamCard Component
 *
 * Displays a single team's summary info: name, timezone, member count,
 * and a quick link to its settings page.
 */

import { useNavigate } from 'react-router-dom';
import type { TeamListItem } from '../../types/team';
import './TeamCard.css';

interface TeamCardProps {
  team: TeamListItem;
}

export function TeamCard({ team }: TeamCardProps) {
  const navigate = useNavigate();

  const handleClick = () => {
    navigate(`/dashboard/teams/${team.id}`);
  };

  return (
    <div
      className="team-card"
      onClick={handleClick}
      role="button"
      tabIndex={0}
      aria-label={`Open settings for ${team.name}`}
      onKeyDown={(e) => e.key === 'Enter' && handleClick()}
    >
      {/* ── Top accent bar ── */}
      <div className="team-card__accent" />

      {/* ── Icon + Name ── */}
      <div className="team-card__header">
        <div className="team-card__avatar">
          {team.name.charAt(0).toUpperCase()}
        </div>
        <div className="team-card__title-group">
          <h3 className="team-card__name">{team.name}</h3>
          <span className="team-card__timezone">🌍 {team.timezone}</span>
        </div>
      </div>

      {/* ── Stats Row ── */}
      <div className="team-card__stats">
        <div className="team-card__stat">
          <span className="team-card__stat-value">{team.member_count}</span>
          <span className="team-card__stat-label">Members</span>
        </div>
        <div className="team-card__stat-divider" />
        <div className="team-card__stat">
          <span
            className={`team-card__status-dot ${team.is_active ? 'team-card__status-dot--active' : 'team-card__status-dot--inactive'}`}
          />
          <span className="team-card__stat-label">
            {team.is_active ? 'Active' : 'Inactive'}
          </span>
        </div>
      </div>

      {/* ── Footer CTA ── */}
      <div className="team-card__footer">
        <span className="team-card__cta">Manage Team →</span>
      </div>
    </div>
  );
}
