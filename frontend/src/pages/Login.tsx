/**
 * StandupBot — Login Page
 *
 * Full-screen login experience with animated background and glassmorphism card.
 * If already authenticated, redirects to /dashboard.
 *
 * LAYOUT:
 *   - Full viewport dark background with animated gradient orbs
 *   - Centered glassmorphism card containing the LoginForm
 *   - Responsive — works on mobile, tablet, and desktop
 */

import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { LoginForm } from '../components/auth/LoginForm';
import { Spinner } from '../components/ui/Spinner';
import './Login.css';

export function Login() {
  const { isAuthenticated, isLoading } = useAuth();

  // Already logged in? Go straight to dashboard.
  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  // Still checking token on mount? Show loading.
  if (isLoading) {
    return (
      <div className="login-page">
        <div className="login-page__loading">
          <Spinner size="lg" label="Checking session..." />
        </div>
      </div>
    );
  }

  return (
    <div className="login-page">
      {/* Animated background orbs */}
      <div className="login-page__bg" aria-hidden="true">
        <div className="login-page__orb login-page__orb--1" />
        <div className="login-page__orb login-page__orb--2" />
        <div className="login-page__orb login-page__orb--3" />
      </div>

      {/* Glassmorphism card */}
      <div className="login-page__card">
        <LoginForm />
      </div>
    </div>
  );
}
