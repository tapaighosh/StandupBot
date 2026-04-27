/**
 * StandupBot — TeamSettings Page
 *
 * Route: /dashboard/teams/:id
 *
 * Full team management hub with three Radix Tabs:
 *   - General: edit name, timezone, schedule windows
 *   - Members: invite / list / remove
 *   - Questions: add / edit / reorder standup questions
 */

import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import * as Tabs from '@radix-ui/react-tabs';
import { teamsApi } from '../api/teams';
import type { Team } from '../types/team';
import type { Member } from '../types/member';
import { MembersManager } from '../components/teams/MembersManager';
import { QuestionsManager } from '../components/teams/QuestionsManager';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Spinner } from '../components/ui/Spinner';
import './TeamSettings.css';

const TIMEZONES = [
  'UTC',
  'America/New_York',
  'America/Chicago',
  'America/Denver',
  'America/Los_Angeles',
  'America/Sao_Paulo',
  'Europe/London',
  'Europe/Paris',
  'Europe/Berlin',
  'Europe/Moscow',
  'Asia/Dubai',
  'Asia/Kolkata',
  'Asia/Singapore',
  'Asia/Tokyo',
  'Asia/Shanghai',
  'Australia/Sydney',
  'Pacific/Auckland',
];

export function TeamSettings() {
  const { id: teamId } = useParams<{ id: string }>();
  const navigate = useNavigate();

  // ── Team data ────────────────────────────────────────────────────
  const [team, setTeam] = useState<Team | null>(null);
  const [members, setMembers] = useState<Member[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  // ── General form state ───────────────────────────────────────────
  const [generalForm, setGeneralForm] = useState({
    name: '',
    timezone: 'UTC',
    reminder_time: '08:00:00',
    digest_time: '10:00:00',
    submission_window_start: '08:00:00',
    submission_window_end: '10:00:00',
    allow_late_submissions: false,
  });
  const [isSavingGeneral, setIsSavingGeneral] = useState(false);
  const [generalError, setGeneralError] = useState<string | null>(null);
  const [generalSuccess, setGeneralSuccess] = useState(false);

  // ── Load team data ───────────────────────────────────────────────
  useEffect(() => {
    if (!teamId) return;
    loadTeam();
  }, [teamId]);

  const loadTeam = async () => {
    if (!teamId) return;
    setIsLoading(true);
    setLoadError(null);
    try {
      const [teamRes, membersRes] = await Promise.all([
        teamsApi.get(teamId),
        teamsApi.listMembers(teamId),
      ]);
      const teamData = teamRes.data;
      const membersData = membersRes.data;
      setTeam(teamData);
      setMembers(membersData);
      setGeneralForm({
        name: teamData.name,
        timezone: teamData.timezone,
        reminder_time: teamData.reminder_time,
        digest_time: teamData.digest_time,
        submission_window_start: teamData.submission_window_start,
        submission_window_end: teamData.submission_window_end,
        allow_late_submissions: teamData.allow_late_submissions,
      });
    } catch (err: unknown) {
      const apiErr = err as { response?: { status?: number; data?: { detail?: string } } };
      if (apiErr?.response?.status === 404) {
        setLoadError('Team not found.');
      } else if (apiErr?.response?.status === 403) {
        setLoadError('You do not have permission to view this team.');
      } else {
        setLoadError(
          apiErr?.response?.data?.detail ?? 'Failed to load team settings.'
        );
      }
    } finally {
      setIsLoading(false);
    }
  };

  // ── Save General ─────────────────────────────────────────────────
  const handleSaveGeneral = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!teamId || !generalForm.name.trim()) return;

    setIsSavingGeneral(true);
    setGeneralError(null);
    setGeneralSuccess(false);

    try {
      const res = await teamsApi.update(teamId, {
        name: generalForm.name.trim(),
        timezone: generalForm.timezone,
        reminder_time: generalForm.reminder_time,
        digest_time: generalForm.digest_time,
        submission_window_start: generalForm.submission_window_start,
        submission_window_end: generalForm.submission_window_end,
        allow_late_submissions: generalForm.allow_late_submissions,
      });
      setTeam(res.data);
      setGeneralSuccess(true);
      setTimeout(() => setGeneralSuccess(false), 3000);
    } catch (err: unknown) {
      const apiErr = err as { response?: { data?: { detail?: string } } };
      setGeneralError(
        apiErr?.response?.data?.detail ?? 'Failed to save changes.'
      );
    } finally {
      setIsSavingGeneral(false);
    }
  };

  // ── Loading / Error states ────────────────────────────────────────
  if (isLoading) {
    return (
      <div className="team-settings__loading">
        <Spinner size="lg" />
        <p>Loading team settings…</p>
      </div>
    );
  }

  if (loadError || !team) {
    return (
      <div className="team-settings__error">
        <div className="team-settings__error-icon">⚠️</div>
        <h2>Something went wrong</h2>
        <p>{loadError ?? 'Unknown error'}</p>
        <div className="team-settings__error-actions">
          <Button variant="ghost" onClick={loadTeam} size="sm">
            Retry
          </Button>
          <Button variant="primary" onClick={() => navigate('/dashboard/teams')} size="sm">
            Back to Teams
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="team-settings">
      {/* ── Breadcrumb ── */}
      <nav className="team-settings__breadcrumb" aria-label="Breadcrumb">
        <Link to="/dashboard/teams" className="team-settings__breadcrumb-link">
          Teams
        </Link>
        <span className="team-settings__breadcrumb-sep">›</span>
        <span className="team-settings__breadcrumb-current">{team.name}</span>
      </nav>

      {/* ── Page Header ── */}
      <div className="team-settings__header">
        <div className="team-settings__header-avatar">
          {team.name.charAt(0).toUpperCase()}
        </div>
        <div className="team-settings__header-info">
          <h1 className="team-settings__title">{team.name}</h1>
          <p className="team-settings__meta">
            🌍 {team.timezone} · 👥 {team.member_count} member
            {team.member_count !== 1 ? 's' : ''}
          </p>
        </div>
      </div>

      {/* ── Tabbed Content ── */}
      <Tabs.Root defaultValue="general" className="team-settings__tabs">
        <Tabs.List className="team-settings__tabs-list" aria-label="Team settings sections">
          <Tabs.Trigger
            value="general"
            className="team-settings__tab"
            id="tab-general"
          >
            ⚙️ General
          </Tabs.Trigger>
          <Tabs.Trigger
            value="members"
            className="team-settings__tab"
            id="tab-members"
          >
            👥 Members
            <span className="team-settings__tab-badge">
              {members.filter((m) => m.is_active).length}
            </span>
          </Tabs.Trigger>
          <Tabs.Trigger
            value="questions"
            className="team-settings__tab"
            id="tab-questions"
          >
            📋 Questions
            <span className="team-settings__tab-badge">
              {team.questions.filter((q) => q.is_active).length}
            </span>
          </Tabs.Trigger>
        </Tabs.List>

        {/* ════════════════════════════════════
            Tab: General
        ════════════════════════════════════ */}
        <Tabs.Content
          value="general"
          className="team-settings__panel"
          aria-labelledby="tab-general"
        >
          <form
            onSubmit={handleSaveGeneral}
            className="team-settings__general-form"
          >
            <div className="team-settings__form-section">
              <h3 className="team-settings__section-heading">Team Identity</h3>
              <Input
                id="general-name"
                label="Team Name"
                value={generalForm.name}
                onChange={(e) =>
                  setGeneralForm((f) => ({ ...f, name: e.target.value }))
                }
                required
                maxLength={100}
              />
              <div className="team-settings__field">
                <label htmlFor="general-timezone" className="input-label">
                  Timezone
                </label>
                <select
                  id="general-timezone"
                  className="team-settings__select"
                  value={generalForm.timezone}
                  onChange={(e) =>
                    setGeneralForm((f) => ({ ...f, timezone: e.target.value }))
                  }
                >
                  {TIMEZONES.map((tz) => (
                    <option key={tz} value={tz}>
                      {tz.replace(/_/g, ' ')}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="team-settings__form-section">
              <h3 className="team-settings__section-heading">Schedule</h3>
              <div className="team-settings__time-grid">
                <div className="team-settings__field">
                  <label htmlFor="general-reminder" className="input-label">
                    Reminder Time
                  </label>
                  <input
                    id="general-reminder"
                    type="time"
                    className="team-settings__time-input"
                    value={generalForm.reminder_time.slice(0, 5)}
                    onChange={(e) =>
                      setGeneralForm((f) => ({
                        ...f,
                        reminder_time: `${e.target.value}:00`,
                      }))
                    }
                  />
                  <span className="input-hint">When reminders are sent</span>
                </div>
                <div className="team-settings__field">
                  <label htmlFor="general-digest" className="input-label">
                    Digest Time
                  </label>
                  <input
                    id="general-digest"
                    type="time"
                    className="team-settings__time-input"
                    value={generalForm.digest_time.slice(0, 5)}
                    onChange={(e) =>
                      setGeneralForm((f) => ({
                        ...f,
                        digest_time: `${e.target.value}:00`,
                      }))
                    }
                  />
                  <span className="input-hint">When digest is generated</span>
                </div>
                <div className="team-settings__field">
                  <label htmlFor="general-window-start" className="input-label">
                    Submission Window Start
                  </label>
                  <input
                    id="general-window-start"
                    type="time"
                    className="team-settings__time-input"
                    value={generalForm.submission_window_start.slice(0, 5)}
                    onChange={(e) =>
                      setGeneralForm((f) => ({
                        ...f,
                        submission_window_start: `${e.target.value}:00`,
                      }))
                    }
                  />
                </div>
                <div className="team-settings__field">
                  <label htmlFor="general-window-end" className="input-label">
                    Submission Window End
                  </label>
                  <input
                    id="general-window-end"
                    type="time"
                    className="team-settings__time-input"
                    value={generalForm.submission_window_end.slice(0, 5)}
                    onChange={(e) =>
                      setGeneralForm((f) => ({
                        ...f,
                        submission_window_end: `${e.target.value}:00`,
                      }))
                    }
                  />
                </div>
              </div>

              <label className="team-settings__checkbox-label">
                <input
                  id="general-late"
                  type="checkbox"
                  className="team-settings__checkbox"
                  checked={generalForm.allow_late_submissions}
                  onChange={(e) =>
                    setGeneralForm((f) => ({
                      ...f,
                      allow_late_submissions: e.target.checked,
                    }))
                  }
                />
                <span className="team-settings__checkbox-text">
                  Allow late submissions after window closes
                </span>
              </label>
            </div>

            {generalError && (
              <div
                className="team-settings__alert team-settings__alert--error"
                role="alert"
              >
                ⚠️ {generalError}
              </div>
            )}
            {generalSuccess && (
              <div
                className="team-settings__alert team-settings__alert--success"
                role="status"
              >
                ✓ Settings saved!
              </div>
            )}

            <div className="team-settings__form-actions">
              <Button
                type="submit"
                variant="primary"
                loading={isSavingGeneral}
                disabled={!generalForm.name.trim()}
              >
                Save Changes
              </Button>
            </div>
          </form>
        </Tabs.Content>

        {/* ════════════════════════════════════
            Tab: Members
        ════════════════════════════════════ */}
        <Tabs.Content
          value="members"
          className="team-settings__panel"
          aria-labelledby="tab-members"
        >
          <MembersManager
            teamId={team.id}
            members={members}
            onMembersChange={setMembers}
          />
        </Tabs.Content>

        {/* ════════════════════════════════════
            Tab: Questions
        ════════════════════════════════════ */}
        <Tabs.Content
          value="questions"
          className="team-settings__panel"
          aria-labelledby="tab-questions"
        >
          <QuestionsManager
            teamId={team.id}
            initialQuestions={team.questions}
          />
        </Tabs.Content>
      </Tabs.Root>
    </div>
  );
}
