/**
 * StandupBot — TeamCreateModal Component
 *
 * Accessible modal (Radix Dialog) for creating a new team.
 * Posts to teamsApi.create() and redirects to the new team's settings page.
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import * as Dialog from '@radix-ui/react-dialog';
import { teamsApi } from '../../api/teams';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';
import './TeamCreateModal.css';

// Common IANA timezones for the dropdown
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

interface TeamCreateModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function TeamCreateModal({ open, onOpenChange }: TeamCreateModalProps) {
  const navigate = useNavigate();
  const [name, setName] = useState('');
  const [timezone, setTimezone] = useState('UTC');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const reset = () => {
    setName('');
    setTimezone('UTC');
    setError(null);
    setIsLoading(false);
  };

  const handleClose = (open: boolean) => {
    if (!open) reset();
    onOpenChange(open);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) {
      setError('Team name is required.');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const res = await teamsApi.create({
        name: name.trim(),
        timezone,
        // Sensible defaults — editable later in General settings tab
        reminder_time: '08:00:00',
        digest_time: '10:00:00',
        submission_window_start: '08:00:00',
        submission_window_end: '10:00:00',
        allow_late_submissions: false,
        questions: [
          { text: 'What did you accomplish yesterday?', order_index: 0 },
          { text: 'What are you working on today?', order_index: 1 },
          { text: 'Any blockers or help needed?', order_index: 2 },
        ],
      });
      onOpenChange(false);
      reset();
      navigate(`/dashboard/teams/${res.data.id}`);
    } catch (err: unknown) {
      const apiErr = err as { response?: { data?: { detail?: string } } };
      setError(
        apiErr?.response?.data?.detail ??
          'Failed to create team. Please try again.'
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Dialog.Root open={open} onOpenChange={handleClose}>
      <Dialog.Portal>
        <Dialog.Overlay className="modal-overlay" />
        <Dialog.Content
          className="modal-content"
          aria-describedby="create-team-desc"
        >
          {/* ── Header ── */}
          <div className="modal-header">
            <div className="modal-icon">🚀</div>
            <div>
              <Dialog.Title className="modal-title">
                Create a New Team
              </Dialog.Title>
              <Dialog.Description
                id="create-team-desc"
                className="modal-subtitle"
              >
                Set up your team and start collecting async standups.
              </Dialog.Description>
            </div>
            <Dialog.Close asChild>
              <button className="modal-close" aria-label="Close">
                ✕
              </button>
            </Dialog.Close>
          </div>

          {/* ── Form ── */}
          <form onSubmit={handleSubmit} className="modal-form">
            <Input
              id="team-name"
              label="Team Name"
              placeholder="e.g. Frontend Squad"
              value={name}
              onChange={(e) => setName(e.target.value)}
              autoFocus
              required
              maxLength={100}
            />

            <div className="modal-field">
              <label htmlFor="team-timezone" className="input-label">
                Timezone
              </label>
              <select
                id="team-timezone"
                className="modal-select"
                value={timezone}
                onChange={(e) => setTimezone(e.target.value)}
              >
                {TIMEZONES.map((tz) => (
                  <option key={tz} value={tz}>
                    {tz.replace(/_/g, ' ')}
                  </option>
                ))}
              </select>
              <span className="input-hint">
                Standup reminders will be sent in this timezone.
              </span>
            </div>

            {/* ── Default questions note ── */}
            <div className="modal-notice">
              <span className="modal-notice__icon">💡</span>
              <p className="modal-notice__text">
                3 default questions will be created. You can customize them in
                the team settings.
              </p>
            </div>

            {error && (
              <div className="modal-error" role="alert">
                <span>⚠️ {error}</span>
              </div>
            )}

            {/* ── Actions ── */}
            <div className="modal-actions">
              <Dialog.Close asChild>
                <Button variant="ghost" type="button" disabled={isLoading}>
                  Cancel
                </Button>
              </Dialog.Close>
              <Button
                type="submit"
                variant="primary"
                loading={isLoading}
                disabled={!name.trim()}
              >
                Create Team
              </Button>
            </div>
          </form>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
