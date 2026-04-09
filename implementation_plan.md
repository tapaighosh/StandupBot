# StandupBot — Full Project Setup Plan

## Goal
Set up a production-ready, agent-assisted monorepo for the **StandupBot** Micro-SaaS —  
**Backend**: Python FastAPI | **Frontend**: React + Vite + TypeScript  
All agent rules, workflows, and AI context files will be derived from the [BRD.md](file:///c:/Users/user/Desktop/Project/StandupBot/BRD.md).

---

## User Review Required

> [!IMPORTANT]
> **Tech Stack Deviation from BRD**: The BRD suggests Next.js + Node/Express. Per your request, we are switching to **FastAPI (Python)** for backend and **React Vite (TypeScript)** for frontend. All features remain the same; only the implementation layer changes.

> [!IMPORTANT]
> **Database**: The BRD specifies PostgreSQL. This plan assumes PostgreSQL with **SQLAlchemy + Alembic** for ORM/migrations. Confirm if you'd prefer a different DB or ORM.

> [!WARNING]
> **LLM Provider**: The BRD mentions OpenAI (GPT-4o-mini) or Anthropic (Haiku). The backend will have an abstract LLM service layer — you choose the provider via `.env`. No provider-specific code will leak into business logic.

---

## Proposed Changes

The work is organized into **5 phases** executed sequentially.

---

### Phase 1 — Agent Control Plane (`.agent/`)

Sets up the rules and reusable workflows that govern how the Antigravity agent behaves across the entire project.

#### [NEW] `.agent/rules/production-standards.md`
Global coding standards enforced on every agent interaction:
- Python: PEP 8, type hints on all functions, Pydantic for all I/O, `async` by default
- TypeScript: strict mode, ESLint + Prettier, named exports, no `any`
- Git: conventional commits, atomic PRs, branch naming (`feat/`, `fix/`, `chore/`)
- Security: no secrets in code, HTTPS only, input validation everywhere, CORS whitelist
- Error handling: all API endpoints return structured `{ detail, code }` errors
- Testing: minimum 80% coverage, all new features must ship with tests

#### [NEW] `.agent/rules/.agentignore`
Tells the agent to skip generated artifacts, `node_modules`, `__pycache__`, `.venv`, `dist/`, etc.

#### [NEW] `.agent/rules/auto-log.md`
Instructs the agent to append a timestamped entry to `.ai-context/prompt_history.md` after every meaningful interaction.

#### [NEW] `.agent/workflows/code-review.md`
Prompt template for standardized code reviews — checks for security, performance, naming, test coverage, and BRD alignment.

#### [NEW] `.agent/workflows/generate-tests.md`
Prompt template for unit test generation — pytest for backend, Vitest for frontend, follows AAA pattern.

#### [NEW] `.agent/workflows/module-implement.md`
Step-by-step prompt template to implement any BRD module:
1. Read the module spec from `.ai-context/BRD.md`
2. Create DB models/migrations
3. Create Pydantic schemas
4. Create service layer
5. Create API routes
6. Create frontend components
7. Write tests
8. Update `prompt_history.md`

---

### Phase 2 — AI Knowledge Base (`.ai-context/`)

The memory center — all business logic, architecture, and historical data.

#### [NEW] `.ai-context/project_context.md`
High-level overview extracted from BRD Sections 1–3:
- Product pitch, target customer, core loop, the 3 questions, two interfaces
- Tech stack decisions (FastAPI + React Vite)

#### [NEW] `.ai-context/architecture.md`
System design document covering:
- **Database schema**: Teams, Members, Submissions, Digests, Tokens, Billing
- **API route map**: All endpoints grouped by module
- **Service layer**: Auth, Token, Submission, Digest, Notification, LLM, Billing
- **External integrations**: Slack, Email (Resend/Postmark), Stripe, OpenAI/Anthropic
- **Data flow diagrams**: Digest generation, token lifecycle, reminder scheduling

#### [NEW] `.ai-context/BRD.md`
Copy of the existing BRD.md into the knowledge base directory for agent reference.

#### [NEW] `.ai-context/test_cases.md`
Master test scenarios derived from all 7 BRD modules:
- Auth & signup flows
- Token generation/validation/expiry
- Submission CRUD + window enforcement
- Digest assembly + LLM fallback
- Notification scheduling + nudge logic
- Dashboard data queries
- Billing plan enforcement

#### [NEW] `.ai-context/prompt_history.md`
Auto-generated audit trail (initialized empty with header).

#### [NEW] `.ai-context/prompts.md`
Quick-reference prompt snippets for common tasks.

---

### Phase 3 — Backend Scaffolding (FastAPI + Python)

Production-ready Python backend structure inside `backend/`.

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI app factory, middleware, CORS, lifespan
│   ├── config.py                  # Pydantic Settings (env-based configuration)
│   ├── database.py                # SQLAlchemy async engine + session factory
│   ├── dependencies.py            # Shared FastAPI dependencies (get_db, get_current_user)
│   ├── exceptions.py              # Custom exceptions + global exception handlers
│   ├── middleware/
│   │   ├── __init__.py
│   │   ├── logging.py             # Request/response logging middleware
│   │   └── rate_limit.py          # Rate limiting middleware
│   ├── models/                    # SQLAlchemy ORM models
│   │   ├── __init__.py
│   │   ├── base.py                # Declarative base + common mixins (timestamps, soft-delete)
│   │   ├── team.py
│   │   ├── member.py
│   │   ├── submission.py
│   │   ├── digest.py
│   │   ├── token.py
│   │   └── user.py                # Manager user model
│   ├── schemas/                   # Pydantic request/response schemas
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── team.py
│   │   ├── member.py
│   │   ├── submission.py
│   │   ├── digest.py
│   │   └── common.py              # Shared schemas (pagination, error response)
│   ├── api/                       # API route modules
│   │   ├── __init__.py
│   │   ├── router.py              # Main API router aggregating all sub-routers
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py            # Signup, login, OAuth, token refresh
│   │   │   ├── teams.py           # Team CRUD + member management
│   │   │   ├── submissions.py     # Standup form submission
│   │   │   ├── digests.py         # Digest retrieval + manual trigger
│   │   │   ├── dashboard.py       # Analytics endpoints
│   │   │   └── health.py          # Health check endpoint
│   ├── services/                  # Business logic layer
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   ├── team_service.py
│   │   ├── token_service.py       # JWT magic link generation + validation
│   │   ├── submission_service.py
│   │   ├── digest_service.py      # Digest assembly + dispatch
│   │   ├── llm_service.py         # Abstract LLM interface (OpenAI / Anthropic)
│   │   ├── email_service.py       # Transactional email via Resend/Postmark
│   │   ├── slack_service.py       # Slack Bolt integration
│   │   ├── notification_service.py
│   │   └── billing_service.py     # Stripe integration
│   ├── tasks/                     # Background / scheduled tasks
│   │   ├── __init__.py
│   │   ├── scheduler.py           # APScheduler or Celery Beat config
│   │   ├── digest_job.py          # Daily digest generation job
│   │   ├── reminder_job.py        # Daily reminder sender
│   │   └── nudge_job.py           # Follow-up nudge sender
│   └── utils/
│       ├── __init__.py
│       ├── security.py            # Password hashing, JWT utilities
│       └── helpers.py             # General utility functions
├── alembic/                       # Database migrations
│   ├── env.py
│   ├── versions/
│   └── alembic.ini
├── tests/
│   ├── __init__.py
│   ├── conftest.py                # Shared fixtures (test DB, client, factories)
│   ├── test_auth.py
│   ├── test_teams.py
│   ├── test_submissions.py
│   ├── test_digests.py
│   └── test_tokens.py
├── .env.example                   # Template environment variables
├── .gitignore
├── pyproject.toml                 # Dependencies + tool config (ruff, pytest)
├── requirements.txt               # Pinned production dependencies
├── requirements-dev.txt           # Dev/test dependencies
└── README.md
```

#### Key Files Detail

##### [NEW] `backend/app/main.py`
- FastAPI app factory with lifespan handler (DB init/shutdown)
- CORS middleware with configurable origins
- Global exception handlers for structured error responses
- Request ID middleware for tracing
- Include all v1 routers

##### [NEW] `backend/app/config.py`
- Pydantic `BaseSettings` class loading from `.env`
- Sections: Database, Auth (JWT secret, expiry), Email, Slack, LLM, Stripe, App (debug, log level)

##### [NEW] `backend/app/exceptions.py`
- Custom exception hierarchy: `AppException` → `NotFoundError`, `AuthenticationError`, `ValidationError`, `PermissionError`, `RateLimitError`, `ExternalServiceError`
- FastAPI exception handlers returning `{ detail: str, code: str, status_code: int }`

##### [NEW] `backend/app/models/base.py`
- `TimestampMixin` (created_at, updated_at), `SoftDeleteMixin` (deleted_at)
- UUID primary key pattern

##### [NEW] `backend/app/services/llm_service.py`
- Abstract `LLMService` with `generate_summary()`, `detect_blockers()`, `generate_weekly_report()`
- Concrete implementations: `OpenAILLMService`, `AnthropicLLMService`
- Fallback behavior: if LLM call fails, return `None` (digest sends without summary)

##### [NEW] `backend/pyproject.toml`
Key dependencies:
```
fastapi, uvicorn, sqlalchemy[asyncio], asyncpg, alembic,
pydantic-settings, python-jose[cryptography], passlib[bcrypt],
httpx, openai, anthropic, stripe, slack-bolt,
apscheduler, resend, jinja2
```

---

### Phase 4 — Frontend Scaffolding (React + Vite + TypeScript)

Production-ready React frontend inside `frontend/`.

```
frontend/
├── public/
│   └── favicon.svg
├── src/
│   ├── main.tsx                   # App entry point
│   ├── App.tsx                    # Root component with routing
│   ├── vite-env.d.ts
│   ├── assets/                    # Static assets (images, fonts)
│   ├── config/
│   │   └── env.ts                 # Type-safe environment variables
│   ├── api/
│   │   ├── client.ts              # Axios instance with interceptors
│   │   ├── auth.ts                # Auth API calls
│   │   ├── teams.ts               # Teams API calls
│   │   ├── submissions.ts         # Submissions API calls
│   │   ├── digests.ts             # Digests API calls
│   │   └── dashboard.ts           # Dashboard/analytics API calls
│   ├── hooks/
│   │   ├── useAuth.ts
│   │   ├── useTeam.ts
│   │   ├── useDigest.ts
│   │   └── useLocalStorage.ts
│   ├── context/
│   │   └── AuthContext.tsx         # Auth state management
│   ├── components/
│   │   ├── ui/                    # Reusable UI primitives
│   │   │   ├── Button.tsx
│   │   │   ├── Input.tsx
│   │   │   ├── Card.tsx
│   │   │   ├── Modal.tsx
│   │   │   ├── Spinner.tsx
│   │   │   ├── Badge.tsx
│   │   │   ├── Toast.tsx
│   │   │   └── ErrorBoundary.tsx
│   │   ├── layout/
│   │   │   ├── DashboardLayout.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   ├── Header.tsx
│   │   │   └── PublicLayout.tsx
│   │   ├── auth/
│   │   │   ├── LoginForm.tsx
│   │   │   ├── SignupForm.tsx
│   │   │   └── ProtectedRoute.tsx
│   │   ├── team/
│   │   │   ├── TeamSetupWizard.tsx
│   │   │   ├── MemberList.tsx
│   │   │   └── QuestionEditor.tsx
│   │   ├── standup/
│   │   │   ├── StandupForm.tsx     # Member submission form
│   │   │   └── SubmitConfirmation.tsx
│   │   ├── digest/
│   │   │   ├── DigestView.tsx
│   │   │   ├── DigestCard.tsx
│   │   │   └── AISummary.tsx
│   │   └── dashboard/
│   │       ├── ResponseChart.tsx
│   │       ├── BlockerTrends.tsx
│   │       ├── ParticipationHeatmap.tsx
│   │       └── TeamOverview.tsx
│   ├── pages/
│   │   ├── Landing.tsx
│   │   ├── Login.tsx
│   │   ├── Signup.tsx
│   │   ├── Dashboard.tsx
│   │   ├── TeamSettings.tsx
│   │   ├── DigestHistory.tsx
│   │   ├── Analytics.tsx
│   │   ├── StandupSubmit.tsx       # Public page (token-validated)
│   │   └── NotFound.tsx
│   ├── styles/
│   │   ├── index.css              # Global styles + CSS custom properties
│   │   ├── variables.css          # Design tokens (colors, spacing, typography)
│   │   └── animations.css         # Reusable keyframe animations
│   ├── utils/
│   │   ├── formatters.ts          # Date, time, text formatting
│   │   ├── validators.ts          # Form validation helpers
│   │   └── constants.ts           # App-wide constants
│   └── types/
│       ├── api.ts                 # API response types
│       ├── team.ts
│       ├── member.ts
│       ├── submission.ts
│       └── digest.ts
├── .env.example
├── .gitignore
├── .eslintrc.cjs
├── .prettierrc
├── index.html
├── package.json
├── tsconfig.json
├── tsconfig.node.json
├── vite.config.ts
└── README.md
```

#### Key Files Detail

##### [NEW] `frontend/src/api/client.ts`
- Axios instance with base URL from env
- Request interceptor: attach JWT from localStorage
- Response interceptor: handle 401 → redirect to login, structured error parsing
- Retry logic for network failures

##### [NEW] `frontend/src/components/ui/ErrorBoundary.tsx`
- React error boundary with fallback UI
- Logs errors to console (extensible to error reporting service)

##### [NEW] `frontend/src/context/AuthContext.tsx`
- React Context + useReducer for auth state
- `login()`, `logout()`, `signup()`, `refreshToken()` actions
- Persists JWT in localStorage, auto-checks expiry

##### [NEW] `frontend/src/styles/variables.css`
Premium design system tokens:
- Dark mode color palette with vibrant accents
- Inter font family from Google Fonts
- Spacing scale (4px base), border-radius tokens
- Glassmorphism utility classes
- Smooth transition defaults

---

### Phase 5 — Root-Level Files

#### [NEW] `README.md` (updated)
Project overview, setup instructions for both backend and frontend, environment variable docs, deployment guide.

#### [NEW] `docker-compose.yml` (optional but recommended)
PostgreSQL + Redis services for local development.

#### [NEW] `.gitignore`
Root-level gitignore covering Python + Node + IDE files.

---

## Module-by-Module Implementation Prompts

After scaffolding is complete, each BRD module can be implemented using the `.agent/workflows/module-implement.md` workflow. Here's the ordered sequence:

| Order | Module | Backend Focus | Frontend Focus |
|-------|--------|--------------|----------------|
| 1 | **Auth & Team Setup** | User model, OAuth, JWT, team CRUD | Signup/Login pages, team wizard |
| 2 | **Link Engine** | Token generation, validation, expiry | — (backend only) |
| 3 | **Submission Form** | Submission CRUD, window validation | StandupForm page (public, mobile-first) |
| 4 | **Digest Engine** | Scheduled job, LLM call, email/Slack dispatch | DigestView, DigestHistory |
| 5 | **Notification System** | Reminder scheduler, nudge logic | — (backend only) |
| 6 | **Manager Dashboard** | Analytics queries, response rates | Dashboard, charts, heatmaps |
| 7 | **Billing & Plans** | Stripe webhooks, plan enforcement | Billing settings page |

---

## Open Questions

> [!IMPORTANT]
> **1. Task Queue**: For background jobs (digest, reminders), do you prefer **Celery + Redis** or **APScheduler** (simpler, in-process)? Celery is more scalable; APScheduler is easier for MVP.

> [!IMPORTANT]
> **2. Auth Provider**: Should manager OAuth be **Google only**, or also support GitHub/Microsoft?

> [!IMPORTANT]
> **3. Docker**: Do you want a `docker-compose.yml` for local PostgreSQL + Redis, or will you manage services separately?

> [!IMPORTANT]
> **4. CSS Framework**: The frontend uses vanilla CSS with a custom design system (per your request). Should I add any CSS utility or component library (e.g., Radix UI for headless components)?

> [!IMPORTANT]
> **5. Monorepo Tooling**: Do you want a root `package.json` with workspaces, or keep backend/frontend as fully independent projects?

---

## Verification Plan

### Automated Tests
```bash
# Backend
cd backend && pip install -r requirements-dev.txt
pytest --cov=app --cov-report=term-missing

# Frontend
cd frontend && npm install
npm run lint
npm run type-check
npm run build  # Ensures no build errors
```

### Manual Verification
- Confirm all directories and files exist with correct structure
- Backend: `uvicorn app.main:app --reload` starts without errors
- Frontend: `npm run dev` starts without errors, loads in browser
- Health endpoint: `GET /api/v1/health` returns `200 OK`
- All agent rules and workflows render correctly when referenced
