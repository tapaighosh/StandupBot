/**
 * StandupBot — Root App Component
 *
 * Sets up routing, auth provider, and error boundaries.
 */

import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { ErrorBoundary } from './components/ui/ErrorBoundary';
import { ProtectedRoute } from './components/auth/ProtectedRoute';
import { DashboardLayout } from './components/layout/DashboardLayout';
import { PublicLayout } from './components/layout/PublicLayout';

// Pages
import { Login } from './pages/Login';
import { Dashboard } from './pages/Dashboard';
import { Teams } from './pages/Teams';
import { TeamSettings } from './pages/TeamSettings';
import { StandupSubmit } from './pages/StandupSubmit';
import { DigestHistory } from './pages/DigestHistory';
import { DigestDetail } from './pages/DigestDetail';
import { NotFound } from './pages/NotFound';

export default function App() {
  return (
    <ErrorBoundary>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            {/* Public Routes */}
            <Route element={<PublicLayout />}>
              <Route path="/login" element={<Login />} />
              <Route path="/standup/:token" element={<StandupSubmit />} />
            </Route>

            {/* Protected Dashboard Routes */}
            <Route
              path="/dashboard"
              element={
                <ProtectedRoute>
                  <DashboardLayout />
                </ProtectedRoute>
              }
            >
              <Route index element={<Dashboard />} />
              {/* Module 1b: Team CRUD & Member Management */}
              <Route path="teams" element={<Teams />} />
              <Route path="teams/:id" element={<TeamSettings />} />
              <Route path="digests" element={<DigestHistory />} />
              <Route path="digests/:id" element={<DigestDetail />} />
              {/* Module 6: <Route path="analytics" element={<Analytics />} /> */}
            </Route>

            {/* Redirect root to dashboard */}
            <Route path="/" element={<Login />} />

            {/* 404 */}
            <Route path="*" element={<NotFound />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </ErrorBoundary>
  );
}
