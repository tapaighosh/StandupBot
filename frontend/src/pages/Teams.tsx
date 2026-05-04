/**
 * StandupBot — Teams Page
 *
 * Lists all teams owned by the current manager. Shows a responsive
 * grid of TeamCards and opens the TeamCreateModal to create new teams.
 */

import { useState, useEffect } from 'react';
import { teamsApi } from '../api/teams';
import type { TeamListItem } from '../types/team';
import { TeamCard } from '../components/teams/TeamCard';
import { TeamCreateModal } from '../components/teams/TeamCreateModal';
import { Button } from '../components/ui/Button';
import { Spinner } from '../components/ui/Spinner';
import './Teams.css';

export function Teams() {
  const [teams, setTeams] = useState<TeamListItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [modalOpen, setModalOpen] = useState(false);

  useEffect(() => {
    loadTeams();
  }, []);

  const loadTeams = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await teamsApi.list();
      setTeams(res.data);
    } catch (err: unknown) {
      const apiErr = err as { response?: { data?: { detail?: string } } };
      setError(
        apiErr?.response?.data?.detail ?? 'Failed to load teams. Please try again.'
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="teams-page">
      {/* ── Page Header ── */}
      <div className="teams-page__header">
        <div className="teams-page__heading">
          <h1 className="teams-page__title">Your Teams</h1>
          <p className="teams-page__subtitle">
            Manage your standup teams, invite members, and configure questions.
          </p>
        </div>
        <Button
          id="create-team-btn"
          variant="primary"
          size="md"
          icon={<span>＋</span>}
          onClick={() => setModalOpen(true)}
        >
          Create New Team
        </Button>
      </div>

      {/* ── Content ── */}
      {isLoading ? (
        <div className="teams-page__loading" aria-live="polite">
          <Spinner size="lg" />
          <p>Loading your teams…</p>
        </div>
      ) : error ? (
        <div className="teams-page__error" role="alert">
          <div className="teams-page__error-icon">⚠️</div>
          <p>{error}</p>
          <Button variant="ghost" size="sm" onClick={loadTeams}>
            Retry
          </Button>
        </div>
      ) : teams.length === 0 ? (
        <div className="teams-page__empty">
          <div className="teams-page__empty-graphic">🏗️</div>
          <h2 className="teams-page__empty-title">No teams yet</h2>
          <p className="teams-page__empty-text">
            Create your first team to start collecting async standups from your
            remote team members.
          </p>
          <Button
            variant="primary"
            size="lg"
            icon={<span>＋</span>}
            onClick={() => setModalOpen(true)}
          >
            Create Your First Team
          </Button>
        </div>
      ) : (
        <div className="teams-page__grid stagger-children">
          {teams.map((team) => (
            <TeamCard key={team.id} team={team} />
          ))}
        </div>
      )}

      {/* ── Create Modal ── */}
      <TeamCreateModal open={modalOpen} onOpenChange={setModalOpen} />
    </div>
  );
}
