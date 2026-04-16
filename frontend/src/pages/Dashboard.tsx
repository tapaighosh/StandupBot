/**
 * StandupBot — Dashboard Page
 *
 * The main landing page after login. Shows:
 * - Welcome greeting with the user's name
 * - Quick stats at a glance (placeholder data for now)
 * - Three overview cards: Today's Digest, Team Overview, Blockers
 *
 * These cards will be populated with real data in later modules:
 * - Module 4 (Digest Engine) → Today's Digest content
 * - Module 1 (Team Setup) → Team member counts / response rates
 * - Module 4 (Digest Engine) → Blocker alerts
 */

import { useAuth } from '../context/AuthContext';
import { Card, CardHeader } from '../components/ui/Card';
import './Dashboard.css';

export function Dashboard() {
  const { user } = useAuth();

  // Get time-based greeting
  const hour = new Date().getHours();
  const greeting = hour < 12 ? 'Good morning' : hour < 17 ? 'Good afternoon' : 'Good evening';

  return (
    <div className="dashboard-page">
      {/* ── Welcome Header ── */}
      <div className="dashboard-page__header">
        <div className="dashboard-page__greeting">
          <h1 className="dashboard-page__title">
            {greeting}, {user?.name?.split(' ')[0] || 'there'} 👋
          </h1>
          <p className="dashboard-page__subtitle">
            Here&apos;s what&apos;s happening with your teams today.
          </p>
        </div>
      </div>

      {/* ── Quick Stats Row ── */}
      <div className="dashboard-page__stats stagger-children">
        <div className="dashboard-page__stat-card">
          <span className="dashboard-page__stat-icon">👥</span>
          <div className="dashboard-page__stat-content">
            <span className="dashboard-page__stat-value">—</span>
            <span className="dashboard-page__stat-label">Team Members</span>
          </div>
        </div>

        <div className="dashboard-page__stat-card">
          <span className="dashboard-page__stat-icon">✅</span>
          <div className="dashboard-page__stat-content">
            <span className="dashboard-page__stat-value">—</span>
            <span className="dashboard-page__stat-label">Responded Today</span>
          </div>
        </div>

        <div className="dashboard-page__stat-card">
          <span className="dashboard-page__stat-icon">🚧</span>
          <div className="dashboard-page__stat-content">
            <span className="dashboard-page__stat-value">—</span>
            <span className="dashboard-page__stat-label">Active Blockers</span>
          </div>
        </div>

        <div className="dashboard-page__stat-card">
          <span className="dashboard-page__stat-icon">📈</span>
          <div className="dashboard-page__stat-content">
            <span className="dashboard-page__stat-value">—</span>
            <span className="dashboard-page__stat-label">Response Rate</span>
          </div>
        </div>
      </div>

      {/* ── Main Cards Grid ── */}
      <div className="dashboard-page__grid stagger-children">
        {/* Today's Digest Card */}
        <Card variant="glass" padding="lg" className="dashboard-page__card">
          <CardHeader
            title="📋 Today's Digest"
            subtitle="Not generated yet"
          />
          <div className="dashboard-page__card-body">
            <div className="dashboard-page__empty-state">
              <div className="dashboard-page__empty-icon">📝</div>
              <p className="dashboard-page__empty-text">
                Your daily standup digest will appear here once your team
                starts submitting their updates.
              </p>
              <p className="dashboard-page__empty-hint">
                Set up a team → invite members → they submit → you get a digest
              </p>
            </div>
          </div>
        </Card>

        {/* Team Overview Card */}
        <Card variant="glass" padding="lg" className="dashboard-page__card">
          <CardHeader
            title="👥 Team Overview"
            subtitle="0 teams configured"
          />
          <div className="dashboard-page__card-body">
            <div className="dashboard-page__empty-state">
              <div className="dashboard-page__empty-icon">🏗️</div>
              <p className="dashboard-page__empty-text">
                Create your first team to get started.
                You can customize standup questions, set submission
                windows, and invite team members.
              </p>
              <p className="dashboard-page__empty-hint">
                Navigate to Teams → Create Team
              </p>
            </div>
          </div>
        </Card>

        {/* Blockers Card */}
        <Card variant="glass" padding="lg" className="dashboard-page__card">
          <CardHeader
            title="🚧 Blockers"
            subtitle="No blockers flagged"
          />
          <div className="dashboard-page__card-body">
            <div className="dashboard-page__empty-state">
              <div className="dashboard-page__empty-icon">✨</div>
              <p className="dashboard-page__empty-text">
                When team members mention blockers in their standups,
                they&apos;ll be highlighted here for quick visibility.
              </p>
              <p className="dashboard-page__empty-hint">
                AI-powered blocker detection coming in Module 4
              </p>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}
