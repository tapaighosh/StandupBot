# StandupBot — Step-by-Step Module Prompts

> **How to use this file:**
> Run each prompt one at a time, in order. After each prompt completes, **read
> the generated code**, ask questions about anything you don't understand, and
> verify the output before moving to the next prompt.
>
> Each section tells you:
> - 🎯 **What it does** — the goal of this step
> - 🧠 **What you'll learn** — the concepts and patterns you'll pick up
> - 📁 **Files involved** — what gets created or changed
> - ✅ **How to verify** — how to confirm it worked
> - 💬 **The prompt** — exactly what to paste

---

## Before You Start — How to Give Context

Every time you start a **new conversation**, paste this at the top of your first
message so the agent understands your project:

```
I'm building StandupBot — an async daily standup collector for remote teams.

Tech stack:
- Backend: Python FastAPI (async), PostgreSQL, SQLAlchemy, Alembic, APScheduler
- Frontend: React + Vite + TypeScript, Vanilla CSS + Radix UI
- Auth: Google OAuth (managers) + JWT magic links (members)
- LLM: OpenAI/Anthropic for digest summaries

Refer to these files for context:
- .ai-context/project_context.md — product overview
- .ai-context/architecture.md — DB schema, API routes, service layer
- .ai-context/test_cases.md — test scenarios
- .agent/rules/production-standards.md — coding standards

Follow the /module-implement workflow for all implementations.
```

---

## Prompt 0 — Project Setup & Scaffolding

> ✅ **Already done!** This is the scaffolding we completed. You already have the
> folder structure, models, schemas, routes (stubs), services (stubs), and the
> frontend shell.

### 🧠 What you should review now

Before running any module prompts, **read these files** to understand the
foundation:

| File | What it teaches you |
|------|-------------------|
| `backend/app/main.py` | How a FastAPI app is assembled (middleware, CORS, routers, lifespan) |
| `backend/app/config.py` | How Pydantic Settings loads env vars — the config pattern |
| `backend/app/database.py` | Async SQLAlchemy engine + session factory pattern |
| `backend/app/exceptions.py` | Custom exception hierarchy + global error handlers |
| `backend/app/dependencies.py` | FastAPI's dependency injection system |
| `backend/app/models/base.py` | SQLAlchemy mixins for timestamps, soft-delete, UUID PKs |
| `backend/app/models/user.py` | How a SQLAlchemy model looks with relationships |
| `frontend/src/App.tsx` | React Router setup with protected + public routes |
| `frontend/src/api/client.ts` | Axios interceptors for JWT auth + token refresh |
| `frontend/src/context/AuthContext.tsx` | React Context + useReducer for auth state |
| `frontend/src/styles/variables.css` | CSS custom properties design system |

> **Tip:** Open each file, read it top to bottom, and if anything confuses you,
> ask: *"Explain what `backend/app/dependencies.py` does and why we use the
> `Annotated` pattern"*

---

## Prompt 1 — Google OAuth + JWT Auth (Backend)

### 🎯 What it does
Implements the manager authentication system: Google OAuth login, JWT token
generation (access + refresh), and the `/auth/me` endpoint.

### 🧠 What you'll learn
- How Google OAuth token verification works (server-side)
- JWT access/refresh token pattern
- FastAPI dependency injection for auth (`get_current_user`)
- SQLAlchemy async CRUD operations (create user, find by google_id)
- How Pydantic schemas validate request/response data

### 📁 Files involved
- `backend/app/services/auth_service.py` — full implementation
- `backend/app/api/v1/auth.py` — route handlers
- `backend/app/dependencies.py` — real JWT validation
- `backend/app/utils/security.py` — already has JWT utils
- `backend/tests/test_auth.py` — new tests

### ✅ How to verify
```bash
# Start the server
cd backend && uvicorn app.main:app --reload

# Health check
curl http://localhost:8000/api/v1/health/

# Check Swagger docs
# Open http://localhost:8000/docs — you should see auth endpoints
```

### 💬 The Prompt

```
Implement Module 1a — Google OAuth Authentication (Backend Only)

Follow the /module-implement workflow. Read .ai-context/architecture.md for the
API spec and .ai-context/test_cases.md Section 1.1–1.2 for test cases.

Implement these pieces:
1. Complete `backend/app/services/auth_service.py`:
   - `verify_google_token()` — use httpx to call Google's tokeninfo endpoint
   - `find_or_create_user()` — find by google_id or create new user
   - `generate_tokens()` — create access + refresh JWT using utils/security.py
   - `refresh_access_token()` — validate refresh token, issue new access token
   - `get_user_by_id()` — fetch user from DB

2. Complete `backend/app/api/v1/auth.py`:
   - POST /login/google — verify credential, find/create user, return tokens
   - POST /refresh — validate refresh token, return new access token
   - GET /me — return current user profile

3. Update `backend/app/dependencies.py`:
   - Replace the placeholder `get_current_user_id` with real JWT decoding
   - Use `utils/security.py decode_token()` to extract user_id from the token

4. Create `backend/tests/test_auth.py`:
   - Test Google login with mocked Google API response
   - Test token refresh flow
   - Test /me endpoint with valid/invalid tokens
   - Test expired token returns 401

Make sure all error cases use exceptions from `app/exceptions.py`.
Don't forget to run alembic migration if models change.
Explain each file you create/modify so I understand the code.
```

---

## Prompt 2 — Team CRUD + Member Management (Backend)

### 🎯 What it does
Implements team creation, listing, updating, deleting, and member invite/remove.
This is the core "setup" that a manager does on day one.

### 🧠 What you'll learn
- Full async CRUD pattern with SQLAlchemy
- Authorization checks (only team owner can modify)
- Soft-delete pattern (set `deleted_at` instead of deleting)
- Plan limit enforcement (free tier: 1 team, 5 members)
- Transactional operations (creating team + questions + settings in one commit)

### 📁 Files involved
- `backend/app/services/team_service.py` — full implementation
- `backend/app/api/v1/teams.py` — route handlers
- `backend/tests/test_teams.py` — new tests

### 💬 The Prompt

```
Implement Module 1b — Team CRUD & Member Management (Backend Only)

Follow the /module-implement workflow. Refer to .ai-context/architecture.md for
the Teams API route map and .ai-context/test_cases.md Section 1.3–1.4.

Implement `backend/app/services/team_service.py`:
1. create_team() — create team + 3 default questions + team settings in one
   transaction. Enforce plan limit (free: 1 team max).
2. list_teams() — return all active teams owned by user with member counts
3. get_team() — get by ID, verify owner, include questions + members
4. update_team() — partial update, verify owner
5. delete_team() — soft delete (set deleted_at), deactivate all members
6. invite_member() — create member, check duplicate email, enforce plan limit
   (free: 5 members max)
7. list_members() — return active members only
8. remove_member() — set is_active=False, verify owner

Then complete all route handlers in `backend/app/api/v1/teams.py`.
Create `backend/tests/test_teams.py` covering: create, list, update, delete,
invite member, remove member, plan limits, authorization checks.

Explain the authorization pattern and how plan limits work.
```

---

## Prompt 3 — Login Page + Dashboard Shell (Frontend)

### 🎯 What it does
Creates a working Google OAuth login page and the manager dashboard with
real sidebar navigation. After login, the user sees the dashboard.

### 🧠 What you'll learn
- Google OAuth flow in the browser (using Google Identity Services)
- React Router protected routes in action
- How AuthContext manages login/logout state
- Component composition (Layout → Sidebar → Pages)
- CSS glassmorphism and gradient effects

### 📁 Files involved
- `frontend/src/pages/Login.tsx` — real Google login
- `frontend/src/pages/Dashboard.tsx` — real dashboard with team overview
- `frontend/src/components/auth/LoginForm.tsx` — new
- `frontend/src/context/AuthContext.tsx` — connect to real API
- `frontend/index.html` — add Google Identity Services script

### 💬 The Prompt

```
Implement Module 1c — Login Page + Dashboard Shell (Frontend)

The backend auth API is now ready. Build the frontend to connect to it.

1. Update `frontend/index.html`:
   - Add the Google Identity Services script tag

2. Create `frontend/src/components/auth/LoginForm.tsx`:
   - Render the Google "Sign in with Google" button using Google Identity
     Services (GIS) library
   - On success, call authContext.login(credential) which sends the credential
     to POST /api/v1/auth/login/google
   - Show loading spinner during auth
   - Show error toast on failure
   - Style it with our design system (glassmorphism card, gradient accents)

3. Update `frontend/src/pages/Login.tsx`:
   - Replace the placeholder with the real LoginForm
   - If already authenticated, redirect to /dashboard
   - Make it visually stunning — dark background, centered glass card, animated

4. Update `frontend/src/pages/Dashboard.tsx`:
   - Show a welcome message with the user's name from AuthContext
   - Display placeholder cards for: "Today's Digest", "Team Overview", "Blockers"
   - Use the Card glass variant with stagger animations
   - Make it responsive (cards stack on mobile)

5. Update `frontend/src/context/AuthContext.tsx`:
   - Make sure login() calls the real API and stores tokens
   - Make sure the initial token check on mount works correctly

The design should feel premium — dark mode, subtle gradients, smooth animations.
Use our design system from styles/variables.css. Mobile-responsive at all
breakpoints.
```

---

## Prompt 4 — Token (Magic Link) Engine (Backend)

### 🎯 What it does
Generates unique, time-scoped tokens per team member per day. These are the
"magic links" that members click to submit standups — no login needed.

### 🧠 What you'll learn
- JWT as one-time-use tokens (not just session tokens)
- Token lifecycle: generate → validate → mark used
- Time window enforcement (submissions only within configured hours)
- Timezone-aware date/time handling with `zoneinfo`
- Idempotent token generation (same member+date = same token)

### 📁 Files involved
- `backend/app/services/token_service.py` — full implementation
- `backend/tests/test_tokens.py` — new tests

### 💬 The Prompt

```
Implement Module 2 — Link Engine (Magic Link Token System)

Follow /module-implement. Refer to .ai-context/architecture.md "Token Lifecycle"
diagram and .ai-context/test_cases.md Section 2.

Implement `backend/app/services/token_service.py`:

1. generate_token(member_id, team_id, standup_date):
   - Create a JWT containing: member_id, team_id, date, exp
   - Expiry = team's submission_window_end in team's timezone
   - Hash the token and store in standup_tokens table
   - If token already exists for this member+date, return existing
   - Return the raw JWT string

2. validate_token(token_string):
   - Decode the JWT, verify signature
   - Look up the token hash in DB
   - Check: not expired, not already used, member is active, team is active
   - Return { member_id, team_id, standup_date }
   - Raise TokenExpiredError, TokenUsedError, or AuthenticationError as needed

3. mark_token_used(token_string):
   - Set is_used=True and used_at=now

4. generate_daily_tokens(team_id):
   - For all active members, generate today's token
   - Return list of { member_id, email, name, token, magic_link }
   - The magic_link = FRONTEND_URL/standup/{token}

Create `backend/tests/test_tokens.py` covering:
- Valid token generation and validation
- Expired token rejection
- Already-used token rejection  
- Tampered token rejection
- Token for inactive member/team

Explain the security model: why JWTs work as magic links, and why we also
store the hash in the DB.
```

---

## Prompt 5 — Standup Submission Form (Full Stack)

### 🎯 What it does
The member-facing standup form. A member clicks their magic link, sees 3
questions, types answers, and submits — all without logging in.

### 🧠 What you'll learn
- Public API endpoints (no auth required, token-validated)
- Dynamic form rendering from API data
- localStorage auto-save (draft protection)
- Form validation and error handling
- Mobile-first responsive design
- How the backend validates submission window + late submissions

### 📁 Files involved
- `backend/app/services/submission_service.py` — full implementation
- `backend/app/api/v1/submissions.py` — route handlers
- `frontend/src/pages/StandupSubmit.tsx` — complete rewrite
- `frontend/src/components/standup/StandupForm.tsx` — new
- `frontend/src/components/standup/SubmitConfirmation.tsx` — new
- `backend/tests/test_submissions.py` — new tests

### 💬 The Prompt

```
Implement Module 3 — Standup Submission Form (Full Stack)

Follow /module-implement. This is the member-facing form — the core UX of the
product. Refer to test_cases.md Section 3.

### Backend:

1. Complete `backend/app/services/submission_service.py`:
   - load_form(member_id, team_id, date): fetch team questions, check if
     already submitted, return form data
   - submit_standup(member_id, team_id, date, answers):
     a. Check submission window (use utils/helpers.py is_within_window)
     b. If outside window: allow if allow_late_submissions=true (flag is_late)
     c. Check for existing submission (reject or overwrite based on settings)
     d. Create Submission + Answer records
     e. Mark token as used
     f. Return confirmation

2. Complete `backend/app/api/v1/submissions.py`:
   - GET /form/{token} — validate token via TokenService, load form
   - POST /form/{token} — validate token, submit standup

### Frontend:

3. Rewrite `frontend/src/pages/StandupSubmit.tsx`:
   - On mount: call GET /api/v1/submissions/form/{token}
   - Handle states: loading, error (expired/used/invalid), form, submitted
   - If already submitted, show "already submitted" message

4. Create `frontend/src/components/standup/StandupForm.tsx`:
   - Render each question dynamically as a textarea
   - Auto-save drafts to localStorage on every keystroke
   - Restore from localStorage on mount (draft recovery)
   - Validate: all answers must be non-empty
   - Submit button with loading state
   - Mobile-first design — must be usable on phone without pinching

5. Create `frontend/src/components/standup/SubmitConfirmation.tsx`:
   - Success screen with checkmark animation
   - "You're all set for today!" message
   - Show standup date and submission time

The form MUST load in under 1 second and be fully usable on mobile.
Design it to be dead-simple — a member should submit in under 2 minutes.
```

---

## Prompt 6 — Digest Engine + LLM Summary (Backend)

### 🎯 What it does
The scheduled job that collects all standup submissions, detects blockers,
calls the LLM for a summary paragraph, assembles the digest, and saves it.

### 🧠 What you'll learn
- Background job scheduling with APScheduler
- LLM API integration (OpenAI/Anthropic chat completions)
- Prompt engineering for structured summarization
- Fallback patterns (if LLM fails, digest still sends)
- Template rendering with Jinja2 for email HTML

### 📁 Files involved
- `backend/app/services/digest_service.py` — full implementation
- `backend/app/services/llm_service.py` — real OpenAI/Anthropic calls
- `backend/app/tasks/digest_job.py` — APScheduler job
- `backend/app/tasks/scheduler.py` — register the job
- `backend/tests/test_digests.py` — new tests

### 💬 The Prompt

```
Implement Module 4 — Digest Engine with LLM Summary (Backend)

Follow /module-implement. This is the core value of the product. Refer to
architecture.md "Data Flow — Daily Digest Generation" and test_cases.md Section 4.

1. Complete `backend/app/services/llm_service.py`:
   - OpenAILLMService.generate_summary():
     * Use the prompt from BRD.md Section 7: "You are a chief of staff..."
     * Model: gpt-4o-mini
     * Pass all submissions formatted as: [Member]: Yesterday: X | Today: Y | Blockers: Z
     * Return 3-5 sentence summary. Lead with blockers. End with momentum score.
   - OpenAILLMService.detect_blockers():
     * Classify each answer as blocker/not-blocker
     * Use helpers.py detect_blocker_keywords() as fallback
   - If ANY LLM call fails, log the error and return None — never block the digest

2. Complete `backend/app/services/digest_service.py`:
   - generate_digest(team_id, digest_date):
     a. Fetch team + active members
     b. Fetch all submissions for the date
     c. Identify non-responders (members who didn't submit)
     d. For each submission, check answers for blockers (keyword + LLM)
     e. Call LLM for summary paragraph (with fallback to None)
     f. Build Digest record with: ai_summary, responded_count, non_responders, blockers
     g. Save to DB
     h. Return the digest

3. Complete `backend/app/tasks/digest_job.py`:
   - Async function that gets a DB session and calls DigestService.generate_digest()
   - Retry up to 3 times on failure
   - Log success/failure

4. Update `backend/app/tasks/scheduler.py`:
   - Implement add_team_jobs() to schedule digest_job at team's digest_time

5. Complete the digest API routes in `backend/app/api/v1/digests.py`

6. Create `backend/tests/test_digests.py`:
   - Mock the LLM service
   - Test: digest with all responses, digest with non-responders, LLM failure
     fallback, blocker detection

Explain the LLM prompt structure and why the fallback pattern is critical.
```

---

## Prompt 7 — Digest View + History (Frontend)

### 🎯 What it does
Manager sees today's digest with AI summary, member responses, blocker
highlights, and can browse past digests.

### 🧠 What you'll learn
- Data fetching patterns (loading/error/success states)
- Conditional rendering (with/without AI summary)
- Color-coded status indicators
- Paginated list rendering
- Date-based navigation

### 💬 The Prompt

```
Implement Module 4b — Digest View + History (Frontend)

The digest API is ready. Build the frontend views.

1. Create `frontend/src/pages/DigestHistory.tsx`:
   - Paginated list of past digests
   - Each item shows: date, response rate (color-coded), status badge
   - Click a digest to see its detail view
   - Empty state: "No digests yet — they'll appear after your first standup day"

2. Create `frontend/src/components/digest/DigestView.tsx`:
   - Full digest detail view
   - AI Summary section at the top (highlighted card, gradient border)
   - Responses section: each member's answers in collapsible cards
   - Non-responders section: grey dots with names
   - Blockers section: red-highlighted entries
   - Response rate bar visual

3. Create `frontend/src/components/digest/DigestCard.tsx`:
   - Summary card for digest list items
   - Shows date, response count, rate badge (green >80%, yellow >50%, red <50%)

4. Create `frontend/src/components/digest/AISummary.tsx`:
   - Styled card for the AI summary text
   - Gradient border, subtle glow effect
   - "AI Generated" badge
   - Fallback: "Summary unavailable" if null

5. Add the route: /dashboard/digests → DigestHistory
   Add the route: /dashboard/digests/:id → DigestView

Make it feel like reading a clean email digest — scannable, well-organized,
with clear visual hierarchy. Use stagger animations for the response list.
```

---

## Prompt 8 — Email Reminders + Nudge System (Backend)

### 🎯 What it does
Sends daily reminder emails with magic links, follow-up nudges to
non-responders, and alerts the manager if response rate drops.

### 🧠 What you'll learn
- Transactional email delivery (Resend API)
- Jinja2 HTML email templates
- APScheduler timezone-aware scheduling
- Nudge logic (conditional follow-up after delay)
- Monitoring patterns (response rate alerts)

### 💬 The Prompt

```
Implement Module 5 — Notification System (Backend)

Follow /module-implement. Refer to test_cases.md Section 5.

1. Complete `backend/app/services/email_service.py`:
   - Use the Resend Python SDK
   - Create Jinja2 HTML templates for: reminder, nudge, digest, low_response_alert
   - send_reminder(): includes member name, magic link, team name
   - send_nudge(): slightly different tone ("Don't forget your standup!")
   - send_digest(): sends the formatted digest HTML to the manager
   - All sends wrapped in try/except — email failure should never crash the app

2. Complete `backend/app/services/notification_service.py`:
   - send_daily_reminders(team_id):
     a. Generate daily tokens for all active members
     b. Send email to each (and Slack DM if enabled)
     c. Return { sent, failed, skipped }
   - send_nudges(team_id):
     a. Only if nudge_enabled in team settings
     b. Only to members who haven't submitted by now
     c. Only one nudge per member per day
   - check_response_rate_alert(team_id):
     a. Calculate today's response rate
     b. If below threshold, email the manager

3. Complete `backend/app/tasks/reminder_job.py` and `nudge_job.py`:
   - reminder_job runs at team's reminder_time
   - nudge_job runs at reminder_time + nudge_delay_minutes

4. Update scheduler.py to register reminder + nudge jobs per team

5. Create email templates in `backend/app/templates/`:
   - reminder.html, nudge.html, digest.html, alert.html

Create tests with mocked email sending.
```

---

## Prompt 9 — Manager Dashboard + Analytics (Full Stack)

### 🎯 What it does
The analytics dashboard: response rate charts, blocker trend visualization,
per-member stats, and participation heatmap.

### 🧠 What you'll learn
- SQL aggregation queries (GROUP BY, COUNT, window functions)
- Chart rendering with CSS (no heavy chart library needed)
- Dashboard layout composition
- Data visualization best practices

### 💬 The Prompt

```
Implement Module 6 — Manager Dashboard & Analytics (Full Stack)

Follow /module-implement. Refer to test_cases.md Section 6.

### Backend:
1. Complete `backend/app/api/v1/dashboard.py` analytics endpoints:
   - GET /{team_id}/stats: 30-day response rate, per-member rates, total standups
   - GET /{team_id}/blockers: blocker frequency trends, common themes
   - GET /{team_id}/export: CSV generation using Python csv module

### Frontend:
2. Update `frontend/src/pages/Dashboard.tsx`:
   - Fetch real data from the team API
   - Show: team name, member count, today's response status
   - Quick stats row: response rate, standups this week, active blockers

3. Create `frontend/src/components/dashboard/ResponseChart.tsx`:
   - 30-day response rate line/bar chart
   - Use pure CSS + divs (no chart library) — each bar is a styled div
   - Color: green >80%, yellow >50%, red <50%

4. Create `frontend/src/components/dashboard/BlockerTrends.tsx`:
   - Show common blocker themes as tags
   - Daily blocker count visualization

5. Create `frontend/src/components/dashboard/TeamOverview.tsx`:
   - Member list with green/grey status dots (submitted/not)
   - Per-member 30-day response rate percentage

6. Create `frontend/src/pages/TeamSettings.tsx`:
   - Question editor (reorder, edit text, add/remove)
   - Schedule settings (reminder time, digest time, timezone)
   - Member management (invite form, remove button)

Add routes: /dashboard/analytics, /dashboard/settings
```

---

## Prompt 10 — Billing & Plans (Full Stack)

### 🎯 What it does
Stripe integration for Free/Starter/Growth plans with upgrade flows
and plan limit enforcement.

### 🧠 What you'll learn
- Stripe Checkout Sessions and webhooks
- Webhook signature verification
- Plan-based feature gating
- Subscription lifecycle (create, cancel, renew)

### 💬 The Prompt

```
Implement Module 7 — Billing & Plans (Full Stack)

Follow /module-implement. Refer to test_cases.md Section 7.

### Backend:
1. Complete `backend/app/services/billing_service.py`:
   - get_user_plan(): look up subscription, return plan name
   - check_team_limit() / check_member_limit(): enforce Free/Starter/Growth limits
   - create_checkout_session(): Stripe Checkout for plan upgrade
   - handle_webhook(): process checkout.session.completed, invoice.payment_failed,
     customer.subscription.deleted
   - cancel_subscription(): cancel in Stripe, downgrade to free

2. Add billing API routes:
   - POST /api/v1/billing/checkout — create Stripe checkout session
   - POST /api/v1/billing/webhook — Stripe webhook handler
   - GET /api/v1/billing/subscription — current plan details

### Frontend:
3. Create `frontend/src/pages/Billing.tsx`:
   - Plan comparison cards (Free / Starter $12/mo / Growth $29/mo)
   - Current plan highlighted
   - "Upgrade" button → redirects to Stripe Checkout
   - "Cancel" button with confirmation modal

Add route: /dashboard/billing

Plan limits from BRD:
- Free: 1 team, 5 members, 14-day history
- Starter: 1 team, 15 members, full history
- Growth: 5 teams, 50 members, analytics, Slack
```

---

## Prompt 11 — Slack Integration (Backend)

### 🎯 What it does
Optional Slack bot that sends reminders via DM and posts digests to a channel.

### 🧠 What you'll learn
- Slack Bolt SDK for Python
- Bot tokens and OAuth scopes
- Slack message formatting (Block Kit)
- Feature flags (Slack is optional, never required)

### 💬 The Prompt

```
Implement Module 5b — Slack Integration (Growth Feature)

This is only for Growth plan users. It should work alongside email — Slack
is an enhancement, not a replacement.

1. Complete `backend/app/services/slack_service.py`:
   - Use slack_bolt AsyncApp
   - send_reminder_dm(): find user by email, send DM with magic link
   - post_digest(): post formatted digest to configured channel
   - verify_workspace_connection(): test.auth Slack API call

2. Add Slack OAuth flow:
   - Manager clicks "Connect Slack" in settings
   - Redirects to Slack OAuth, gets bot token
   - Store bot token in team settings

3. Update notification_service.py:
   - If Slack enabled AND user is on Growth plan, also send Slack DMs
   - If Slack channel configured, also post digest to channel

4. Update the TeamSettings page:
   - "Connect to Slack" button (Growth plan only)
   - Show connected workspace name
   - "Disconnect" option

All Slack features gated behind Growth plan. If Slack fails, email still sends.
```

---

## Prompt 12 — Polish, Testing & Deployment

### 🎯 What it does
Final polish: comprehensive tests, error handling review, performance
optimization, and deployment setup.

### 💬 The Prompt

```
Final polish and deployment preparation for StandupBot.

1. Run /code-review on all service files. Fix any issues found.

2. Run /generate-tests for any modules with less than 80% coverage.

3. Performance review:
   - Check for N+1 queries in SQLAlchemy (use eager loading)
   - Add database indexes for frequently queried columns
   - Review React re-renders with the useMemo/useCallback checklist

4. Create a Dockerfile for the backend:
   - Python 3.11 slim base
   - Install requirements, copy app code
   - CMD: uvicorn app.main:app --host 0.0.0.0 --port 8000

5. Create a Dockerfile for the frontend:
   - Node 18 for build, nginx:alpine for serving
   - Multi-stage build

6. Update docker-compose.yml:
   - Add backend and frontend services
   - Add environment variables from .env
   - Add nginx reverse proxy (optional)

7. Update README.md with deployment instructions.

Review all files, estimate test coverage, and list any remaining TODO items.
```

---

## Tips for Maximum Learning

### 🔄 After each prompt:
1. **Read every file** that was created or modified
2. **Ask "why?"** — e.g., *"Why does DigestService catch LLM errors instead of
   letting them propagate?"*
3. **Test manually** — use Swagger docs, curl, or the browser
4. **Run the tests** — `pytest -v` and understand what each test proves
5. **Break it intentionally** — change a value and see what error you get

### 📝 Ask explanatory follow-ups like:
- *"Walk me through the auth flow from Google button click to dashboard load"*
- *"Explain how the token lifecycle works step by step"*
- *"Why is the LLM called at digest time instead of submission time?"*
- *"What happens if the database is down when a reminder job runs?"*

### 🎓 Concepts you'll master across all modules:
| Concept | Where you'll learn it |
|---------|----------------------|
| OAuth 2.0 | Prompt 1 |
| JWT tokens | Prompts 1, 4 |
| Async Python | Prompts 1–8 |
| SQLAlchemy ORM | Prompts 1–2 |
| FastAPI DI | Prompts 1–3 |
| React Context | Prompt 3 |
| React Router | Prompt 3 |
| Background jobs | Prompts 6, 8 |
| LLM integration | Prompt 6 |
| Email delivery | Prompt 8 |
| Stripe billing | Prompt 10 |
| Slack API | Prompt 11 |
| Docker deployment | Prompt 12 |
