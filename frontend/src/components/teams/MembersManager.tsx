/**
 * StandupBot — MembersManager Component
 *
 * Handles member invite (by email + name), listing active members,
 * and soft-removing them. Used inside the TeamSettings Members tab.
 */

import { useState } from 'react';
import { teamsApi } from '../../api/teams';
import type { Member } from '../../types/member';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';
import { Spinner } from '../ui/Spinner';
import './MembersManager.css';

interface MembersManagerProps {
  teamId: string;
  members: Member[];
  onMembersChange: (members: Member[]) => void;
}

export function MembersManager({
  teamId,
  members,
  onMembersChange,
}: MembersManagerProps) {
  const [email, setEmail] = useState('');
  const [memberName, setMemberName] = useState('');
  const [inviting, setInviting] = useState(false);
  const [inviteError, setInviteError] = useState<string | null>(null);
  const [inviteSuccess, setInviteSuccess] = useState<string | null>(null);
  const [removingId, setRemovingId] = useState<string | null>(null);

  // ── Invite ──────────────────────────────────────────────────────
  const handleInvite = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim() || !memberName.trim()) return;

    setInviting(true);
    setInviteError(null);
    setInviteSuccess(null);

    try {
      const res = await teamsApi.inviteMember(teamId, {
        email: email.trim().toLowerCase(),
        name: memberName.trim(),
      });
      onMembersChange([...members, res.data]);
      setInviteSuccess(`✓ ${memberName} has been invited!`);
      setEmail('');
      setMemberName('');
    } catch (err: unknown) {
      const apiErr = err as { response?: { data?: { detail?: string } } };
      setInviteError(
        apiErr?.response?.data?.detail ?? 'Failed to invite member.'
      );
    } finally {
      setInviting(false);
    }
  };

  // ── Remove ──────────────────────────────────────────────────────
  const handleRemove = async (memberId: string, memberDisplayName: string) => {
    if (!window.confirm(`Remove ${memberDisplayName} from this team?`)) return;

    setRemovingId(memberId);
    try {
      await teamsApi.removeMember(teamId, memberId);
      onMembersChange(members.filter((m) => m.id !== memberId));
    } catch (err: unknown) {
      const apiErr = err as { response?: { data?: { detail?: string } } };
      alert(apiErr?.response?.data?.detail ?? 'Failed to remove member.');
    } finally {
      setRemovingId(null);
    }
  };

  const activeMembers = members.filter((m) => m.is_active);

  return (
    <div className="members-manager">
      {/* ── Invite Form ── */}
      <div className="members-manager__invite-card">
        <h4 className="members-manager__section-title">Invite a New Member</h4>
        <form onSubmit={handleInvite} className="members-manager__invite-form">
          <div className="members-manager__invite-fields">
            <Input
              id="invite-name"
              label="Full Name"
              placeholder="Jane Smith"
              value={memberName}
              onChange={(e) => setMemberName(e.target.value)}
              required
            />
            <Input
              id="invite-email"
              type="email"
              label="Email Address"
              placeholder="jane@company.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>

          {inviteError && (
            <div className="members-manager__alert members-manager__alert--error" role="alert">
              ⚠️ {inviteError}
            </div>
          )}
          {inviteSuccess && (
            <div className="members-manager__alert members-manager__alert--success" role="status">
              {inviteSuccess}
            </div>
          )}

          <div className="members-manager__invite-action">
            <Button
              type="submit"
              variant="primary"
              size="md"
              loading={inviting}
              disabled={!email.trim() || !memberName.trim()}
              icon={<span>✉️</span>}
            >
              Send Invite
            </Button>
          </div>
        </form>
      </div>

      {/* ── Members List ── */}
      <div className="members-manager__list-section">
        <div className="members-manager__list-header">
          <h4 className="members-manager__section-title">Team Members</h4>
          <span className="members-manager__count">
            {activeMembers.length} active
          </span>
        </div>

        {activeMembers.length === 0 ? (
          <div className="members-manager__empty">
            <div className="members-manager__empty-icon">👥</div>
            <p>No members yet. Invite someone to get started!</p>
          </div>
        ) : (
          <ul className="members-manager__list" role="list">
            {activeMembers.map((member) => (
              <li key={member.id} className="members-manager__item">
                <div className="members-manager__avatar">
                  {(member.name || member.email).charAt(0).toUpperCase()}
                </div>
                <div className="members-manager__info">
                  <span className="members-manager__name">
                    {member.name || '—'}
                  </span>
                  <span className="members-manager__email">{member.email}</span>
                </div>
                <button
                  className="members-manager__remove-btn"
                  onClick={() => handleRemove(member.id, member.name || member.email)}
                  disabled={removingId === member.id}
                  aria-label={`Remove ${member.name || member.email}`}
                >
                  {removingId === member.id ? (
                    <Spinner size="sm" />
                  ) : (
                    <span>✕</span>
                  )}
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
