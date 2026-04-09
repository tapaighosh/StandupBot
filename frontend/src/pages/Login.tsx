/**
 * StandupBot — Login Page (placeholder)
 * Full implementation in Module 1.
 */

import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';

export function Login() {
  return (
    <Card variant="glass" padding="lg">
      <div style={{ textAlign: 'center' }}>
        <span style={{ fontSize: '3rem' }}>⚡</span>
        <h1 style={{ margin: 'var(--space-4) 0 var(--space-2)' }}>StandupBot</h1>
        <p style={{
          color: 'var(--color-text-tertiary)',
          marginBottom: 'var(--space-8)',
          fontSize: 'var(--font-size-sm)',
        }}>
          Replace your standup calls with a 2-minute async ritual
        </p>

        <Button
          variant="primary"
          size="lg"
          style={{ width: '100%' }}
          onClick={() => alert('Google OAuth — implement in Module 1')}
        >
          Continue with Google
        </Button>

        <p style={{
          marginTop: 'var(--space-6)',
          fontSize: 'var(--font-size-xs)',
          color: 'var(--color-text-muted)',
        }}>
          By continuing, you agree to our Terms of Service and Privacy Policy.
        </p>
      </div>
    </Card>
  );
}
