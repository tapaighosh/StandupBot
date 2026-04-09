/**
 * StandupBot — StandupSubmit Page (placeholder)
 * Public page for member standup submission.
 * Full implementation in Module 3.
 */

import { useParams } from 'react-router-dom';
import { Card } from '../components/ui/Card';

export function StandupSubmit() {
  const { token } = useParams<{ token: string }>();

  return (
    <Card variant="glass" padding="lg">
      <div style={{ textAlign: 'center', marginBottom: 'var(--space-6)' }}>
        <span style={{ fontSize: '2.5rem' }}>✍️</span>
        <h1 style={{ margin: 'var(--space-3) 0' }}>Daily Standup</h1>
        <p style={{ color: 'var(--color-text-tertiary)', fontSize: 'var(--font-size-sm)' }}>
          Answer these questions in under 2 minutes
        </p>
      </div>

      <p style={{ color: 'var(--color-text-muted)', textAlign: 'center', fontSize: 'var(--font-size-sm)' }}>
        Standup form will be implemented in Module 3.
        <br />
        Token: <code style={{ color: 'var(--color-primary-light)' }}>{token?.slice(0, 12)}...</code>
      </p>
    </Card>
  );
}
