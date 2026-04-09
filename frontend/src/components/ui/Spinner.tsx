/**
 * StandupBot — Spinner Component
 */

import './Spinner.css';

interface SpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  label?: string;
}

export function Spinner({ size = 'md', label }: SpinnerProps) {
  return (
    <div className="spinner-container" role="status">
      <div className={`spinner spinner-${size}`} />
      {label && <span className="spinner-label">{label}</span>}
      <span className="sr-only">Loading...</span>
    </div>
  );
}
