/**
 * StandupBot — Dashboard Page (placeholder)
 * Full implementation in Module 6.
 */

import { Card, CardHeader } from '../components/ui/Card';

export function Dashboard() {
  return (
    <div>
      <h1 style={{ marginBottom: 'var(--space-6)' }}>Dashboard</h1>

      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
        gap: 'var(--space-6)',
      }}>
        <Card variant="glass">
          <CardHeader title="Today's Digest" subtitle="No digest generated yet" />
          <p style={{ color: 'var(--color-text-tertiary)', fontSize: 'var(--font-size-sm)' }}>
            Implement Module 4 (Digest Engine) to see today&apos;s standup digest here.
          </p>
        </Card>

        <Card variant="glass">
          <CardHeader title="Team Response" subtitle="0 / 0 responded" />
          <p style={{ color: 'var(--color-text-tertiary)', fontSize: 'var(--font-size-sm)' }}>
            Implement Module 1 (Team Setup) to see response rates here.
          </p>
        </Card>

        <Card variant="glass">
          <CardHeader title="Blockers" subtitle="No blockers flagged" />
          <p style={{ color: 'var(--color-text-tertiary)', fontSize: 'var(--font-size-sm)' }}>
            Implement Module 4 (Digest Engine) to see blocker alerts here.
          </p>
        </Card>
      </div>
    </div>
  );
}
