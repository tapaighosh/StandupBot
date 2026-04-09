/**
 * StandupBot — Sidebar Component
 */

import { NavLink } from 'react-router-dom';
import './Sidebar.css';

export function Sidebar() {
  return (
    <aside className="sidebar" role="navigation" aria-label="Main navigation">
      <div className="sidebar-brand">
        <span className="sidebar-logo">⚡</span>
        <span className="sidebar-title">StandupBot</span>
      </div>

      <nav className="sidebar-nav">
        <NavLink to="/dashboard" end className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}>
          <span className="sidebar-icon">📊</span>
          <span>Dashboard</span>
        </NavLink>

        <NavLink to="/dashboard/teams" className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}>
          <span className="sidebar-icon">👥</span>
          <span>Teams</span>
        </NavLink>

        <NavLink to="/dashboard/digests" className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}>
          <span className="sidebar-icon">📋</span>
          <span>Digests</span>
        </NavLink>

        <NavLink to="/dashboard/analytics" className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}>
          <span className="sidebar-icon">📈</span>
          <span>Analytics</span>
        </NavLink>

        <NavLink to="/dashboard/settings" className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}>
          <span className="sidebar-icon">⚙️</span>
          <span>Settings</span>
        </NavLink>
      </nav>

      <div className="sidebar-footer">
        <span className="sidebar-version">v0.1.0 — MVP</span>
      </div>
    </aside>
  );
}
