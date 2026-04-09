/**
 * StandupBot — Badge Component
 */

import { type ReactNode } from 'react';
import './Badge.css';

interface BadgeProps {
  variant?: 'default' | 'success' | 'warning' | 'danger' | 'info';
  size?: 'sm' | 'md';
  children: ReactNode;
}

export function Badge({ variant = 'default', size = 'sm', children }: BadgeProps) {
  return (
    <span className={`badge badge-${variant} badge-${size}`}>
      {children}
    </span>
  );
}

/** Status dot indicator (green/grey) */
interface StatusDotProps {
  active: boolean;
  label?: string;
}

export function StatusDot({ active, label }: StatusDotProps) {
  return (
    <span className="status-dot-container">
      <span className={`status-dot ${active ? 'status-dot-active' : 'status-dot-inactive'}`} />
      {label && <span className="status-dot-label">{label}</span>}
    </span>
  );
}
