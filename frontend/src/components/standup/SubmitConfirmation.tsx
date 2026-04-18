/**
 * StandupBot — SubmitConfirmation Component
 *
 * Success screen shown after a standup is submitted.
 * Checkmark animation + date + timestamp.
 */

import './SubmitConfirmation.css';

interface SubmitConfirmationProps {
  standupDate: string;
  submittedAt: string;
}

export function SubmitConfirmation({
  standupDate,
  submittedAt,
}: SubmitConfirmationProps) {
  const formattedDate = new Date(standupDate + 'T00:00:00').toLocaleDateString(
    'en-US',
    { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' }
  );

  const formattedTime = new Date(submittedAt).toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
  });

  return (
    <div className="submit-confirmation">
      {/* Animated checkmark */}
      <div className="submit-confirmation__checkmark">
        <svg
          className="submit-confirmation__svg"
          viewBox="0 0 52 52"
          aria-hidden="true"
        >
          <circle
            className="submit-confirmation__circle"
            cx="26"
            cy="26"
            r="25"
            fill="none"
          />
          <path
            className="submit-confirmation__check"
            fill="none"
            d="M14.1 27.2l7.1 7.2 16.7-16.8"
          />
        </svg>
      </div>

      <h2 className="submit-confirmation__title">You&apos;re all set!</h2>
      <p className="submit-confirmation__subtitle">
        Your standup has been submitted successfully.
      </p>

      {/* Details */}
      <div className="submit-confirmation__details">
        <div className="submit-confirmation__detail">
          <span className="submit-confirmation__detail-icon">📅</span>
          <div>
            <span className="submit-confirmation__detail-label">Standup Date</span>
            <span className="submit-confirmation__detail-value">{formattedDate}</span>
          </div>
        </div>

        <div className="submit-confirmation__detail">
          <span className="submit-confirmation__detail-icon">🕐</span>
          <div>
            <span className="submit-confirmation__detail-label">Submitted At</span>
            <span className="submit-confirmation__detail-value">{formattedTime}</span>
          </div>
        </div>
      </div>

      <p className="submit-confirmation__footer">
        You can now close this tab. See you tomorrow! 👋
      </p>
    </div>
  );
}
