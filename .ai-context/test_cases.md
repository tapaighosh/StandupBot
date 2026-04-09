# StandupBot — Master Test Cases

This document defines all test scenarios derived from the BRD modules. Use this as the source of truth when generating tests via the `/generate-tests` workflow.

---

## Module 1 — Auth & Team Setup

### 1.1 Manager Signup
- [TC-1.1.1] Successful signup with valid email and Google OAuth
- [TC-1.1.2] Reject signup with already-registered email
- [TC-1.1.3] Reject signup with invalid email format
- [TC-1.1.4] Google OAuth returns valid user profile and creates account
- [TC-1.1.5] Google OAuth failure returns appropriate error

### 1.2 Authentication
- [TC-1.2.1] Login with valid Google OAuth token returns JWT
- [TC-1.2.2] JWT token contains correct claims (user_id, email, exp)
- [TC-1.2.3] Expired JWT is rejected with 401
- [TC-1.2.4] Refresh token generates new access token
- [TC-1.2.5] Invalidated refresh token is rejected
- [TC-1.2.6] GET /me returns current user profile

### 1.3 Team Management
- [TC-1.3.1] Create team with valid name, timezone, and questions
- [TC-1.3.2] Reject team creation with missing required fields
- [TC-1.3.3] List teams returns only teams owned by current user
- [TC-1.3.4] Update team settings (timezone, reminder time, questions)
- [TC-1.3.5] Delete team performs soft delete
- [TC-1.3.6] Enforce plan limits (free tier: 1 team max)

### 1.4 Member Management
- [TC-1.4.1] Invite member by email — creates member record
- [TC-1.4.2] Reject duplicate member email within same team
- [TC-1.4.3] Remove member marks as inactive
- [TC-1.4.4] List members returns active members only
- [TC-1.4.5] Enforce plan limits (free tier: 5 members max)

---

## Module 2 — Link Engine

### 2.1 Token Generation
- [TC-2.1.1] Generate unique token per member per day
- [TC-2.1.2] Token contains correct claims (member_id, team_id, date, exp)
- [TC-2.1.3] Token expires at configured submission window end
- [TC-2.1.4] Re-generating token for same member+date returns same token

### 2.2 Token Validation
- [TC-2.2.1] Valid, unused token passes validation
- [TC-2.2.2] Expired token is rejected
- [TC-2.2.3] Already-used token is rejected
- [TC-2.2.4] Token with tampered signature is rejected
- [TC-2.2.5] Token for non-existent member is rejected
- [TC-2.2.6] Token for inactive team is rejected

---

## Module 3 — Submission Form

### 3.1 Form Loading
- [TC-3.1.1] Valid token loads team's custom questions
- [TC-3.1.2] Expired token shows "submission window closed" message
- [TC-3.1.3] Used token shows "already submitted" message
- [TC-3.1.4] Invalid token shows error page

### 3.2 Submission
- [TC-3.2.1] Submit all answers successfully within window
- [TC-3.2.2] Reject submission with empty answers
- [TC-3.2.3] Late submission is accepted with `is_late: true` flag
- [TC-3.2.4] Late submission rejected if `allow_late_submissions: false`
- [TC-3.2.5] Re-submission overwrites previous (if enabled)
- [TC-3.2.6] Re-submission blocked (if disabled)
- [TC-3.2.7] Submission stores correct timestamp and metadata

---

## Module 4 — Digest Engine

### 4.1 Digest Generation
- [TC-4.1.1] Digest collects all submissions for the day
- [TC-4.1.2] Non-responders are correctly identified
- [TC-4.1.3] Entries with blocker keywords are flagged
- [TC-4.1.4] LLM is called with correct prompt and all submissions
- [TC-4.1.5] LLM failure does not block digest delivery
- [TC-4.1.6] Digest record is saved to database
- [TC-4.1.7] Digest is sent via email
- [TC-4.1.8] Digest is posted to Slack (if connected)
- [TC-4.1.9] Digest not generated if no submissions exist
- [TC-4.1.10] Manual trigger works for authorized manager

### 4.2 Digest Content
- [TC-4.2.1] AI summary is 3–5 sentences
- [TC-4.2.2] Summary leads with blockers
- [TC-4.2.3] Summary ends with momentum assessment
- [TC-4.2.4] Non-responders listed in digest
- [TC-4.2.5] Response count is accurate

---

## Module 5 — Notification System

### 5.1 Reminders
- [TC-5.1.1] Reminder sent at configured time per team timezone
- [TC-5.1.2] Reminder contains correct personalized magic link
- [TC-5.1.3] Reminder sent via email when email reminders enabled
- [TC-5.1.4] Reminder sent via Slack DM when Slack enabled
- [TC-5.1.5] No reminder sent to inactive members

### 5.2 Nudges
- [TC-5.2.1] Nudge sent if no submission by T + configured delay
- [TC-5.2.2] No nudge sent if already submitted
- [TC-5.2.3] No nudge sent if nudges disabled for team
- [TC-5.2.4] Only one nudge per member per day

### 5.3 Manager Alerts
- [TC-5.3.1] Alert sent if response rate drops below threshold (e.g., 50%)
- [TC-5.3.2] No alert if response rate is above threshold

---

## Module 6 — Manager Dashboard

### 6.1 Digest View
- [TC-6.1.1] Today's digest loads with all submissions
- [TC-6.1.2] Historical digests paginated correctly
- [TC-6.1.3] Individual digest detail view renders correctly
- [TC-6.1.4] Empty state shown when no digest exists

### 6.2 Analytics
- [TC-6.2.1] 30-day response rate calculated correctly per member
- [TC-6.2.2] Blocker frequency trends displayed
- [TC-6.2.3] Participation heatmap shows correct data
- [TC-6.2.4] Export to CSV generates valid file
- [TC-6.2.5] Export to PDF generates valid file

### 6.3 Settings
- [TC-6.3.1] Question editor saves and reorders questions
- [TC-6.3.2] Schedule settings update reminder and digest times
- [TC-6.3.3] Member management (add/remove) works correctly

---

## Module 7 — Billing & Plans

### 7.1 Plan Enforcement
- [TC-7.1.1] Free tier limits: 1 team, 5 members, 14-day history
- [TC-7.1.2] Starter tier limits: 1 team, 15 members, full history
- [TC-7.1.3] Growth tier limits: 5 teams, 50 members, analytics, Slack
- [TC-7.1.4] Exceeding limits returns clear upgrade message

### 7.2 Stripe Integration
- [TC-7.2.1] Checkout session created for plan upgrade
- [TC-7.2.2] Webhook processes `checkout.session.completed`
- [TC-7.2.3] Webhook processes `invoice.payment_failed`
- [TC-7.2.4] Subscription cancellation downgrades to free tier
- [TC-7.2.5] Annual billing discount applied correctly
