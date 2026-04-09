/**
 * StandupBot — Header Component
 */

import { useAuth } from '../../context/AuthContext';
import { Button } from '../ui/Button';
import './Header.css';

export function Header() {
  const { user, logout } = useAuth();

  return (
    <header className="header">
      <div className="header-left">
        {/* Mobile menu toggle – implemented in Module 6 */}
        <button className="header-menu-btn hide-desktop" aria-label="Toggle menu">
          ☰
        </button>
      </div>

      <div className="header-right">
        {user && (
          <div className="header-user">
            {user.avatar_url ? (
              <img src={user.avatar_url} alt={user.name} className="header-avatar" />
            ) : (
              <div className="header-avatar-fallback">
                {user.name.charAt(0).toUpperCase()}
              </div>
            )}
            <span className="header-user-name hide-mobile">{user.name}</span>
            <Button variant="ghost" size="sm" onClick={logout}>
              Logout
            </Button>
          </div>
        )}
      </div>
    </header>
  );
}
