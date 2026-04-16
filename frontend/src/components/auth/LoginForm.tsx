/**
 * StandupBot — LoginForm Component
 *
 * Renders the Google "Sign in with Google" button using Google Identity Services (GIS).
 *
 * HOW GOOGLE IDENTITY SERVICES WORKS:
 * 1. We load the GIS script in index.html (<script src="accounts.google.com/gsi/client">)
 * 2. On component mount, we call google.accounts.id.initialize() with our client ID
 * 3. We call google.accounts.id.renderButton() to render Google's pre-built button
 * 4. When the user clicks and authenticates, Google calls our callback
 * 5. The callback receives a CredentialResponse with a `credential` (JWT from Google)
 * 6. We pass that credential to authContext.login() which sends it to our backend
 * 7. Our backend verifies it with Google and returns our own JWT tokens
 */

import { useEffect, useRef, useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import { env } from '../../config/env';
import './LoginForm.css';

// TypeScript declaration for Google Identity Services global
declare global {
  interface Window {
    google?: {
      accounts: {
        id: {
          initialize: (config: {
            client_id: string;
            callback: (response: { credential: string }) => void;
            auto_select?: boolean;
          }) => void;
          renderButton: (
            element: HTMLElement,
            config: {
              theme?: string;
              size?: string;
              width?: number;
              text?: string;
              shape?: string;
              logo_alignment?: string;
            }
          ) => void;
        };
      };
    };
  }
}

export function LoginForm() {
  const { login } = useAuth();
  const googleButtonRef = useRef<HTMLDivElement>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Wait for the Google Identity Services script to load
    const initializeGoogle = () => {
      if (!window.google?.accounts?.id) {
        // Script not loaded yet — retry after a short delay
        setTimeout(initializeGoogle, 200);
        return;
      }

      window.google.accounts.id.initialize({
        client_id: env.GOOGLE_CLIENT_ID,
        callback: handleGoogleCallback,
      });

      // Render Google's pre-built button into our container
      if (googleButtonRef.current) {
        window.google.accounts.id.renderButton(googleButtonRef.current, {
          theme: 'outline',
          size: 'large',
          width: 320,
          text: 'continue_with',
          shape: 'pill',
          logo_alignment: 'left',
        });
      }
    };

    initializeGoogle();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function handleGoogleCallback(response: { credential: string }) {
    setIsLoading(true);
    setError(null);

    try {
      await login(response.credential);
      // AuthContext handles redirect after login
    } catch (err) {
      console.error('Login failed:', err);
      setError('Login failed. Please try again.');
      setIsLoading(false);
    }
  }

  return (
    <div className="login-form">
      {/* App branding */}
      <div className="login-form__brand">
        <div className="login-form__icon">⚡</div>
        <h1 className="login-form__title">StandupBot</h1>
        <p className="login-form__subtitle">
          Replace your standup calls with a<br />
          2-minute async ritual
        </p>
      </div>

      {/* Divider */}
      <div className="login-form__divider">
        <span>Get started</span>
      </div>

      {/* Google Sign-in button container */}
      <div className="login-form__google-wrapper">
        {isLoading ? (
          <div className="login-form__loading">
            <div className="login-form__spinner" />
            <span>Signing you in...</span>
          </div>
        ) : (
          <div ref={googleButtonRef} className="login-form__google-button" />
        )}
      </div>

      {/* Error message */}
      {error && (
        <div className="login-form__error animate-fade-in-up">
          <span className="login-form__error-icon">⚠️</span>
          {error}
        </div>
      )}

      {/* Features list */}
      <div className="login-form__features">
        <div className="login-form__feature">
          <span className="login-form__feature-icon">📧</span>
          <span>Daily magic links to your team</span>
        </div>
        <div className="login-form__feature">
          <span className="login-form__feature-icon">🤖</span>
          <span>AI-powered daily digests</span>
        </div>
        <div className="login-form__feature">
          <span className="login-form__feature-icon">📊</span>
          <span>Track blockers & team health</span>
        </div>
      </div>

      {/* Terms */}
      <p className="login-form__terms">
        By continuing, you agree to our{' '}
        <a href="#terms">Terms of Service</a> and{' '}
        <a href="#privacy">Privacy Policy</a>.
      </p>
    </div>
  );
}
