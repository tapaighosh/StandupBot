/**
 * StandupBot — PublicLayout
 * Simple centered layout for public pages (standup form, landing).
 */

import { Outlet } from 'react-router-dom';
import './PublicLayout.css';

export function PublicLayout() {
  return (
    <div className="public-layout">
      <main className="public-content">
        <Outlet />
      </main>
    </div>
  );
}
