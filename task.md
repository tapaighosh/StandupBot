# StandupBot Project Setup — Task Tracker

## Phase 1 — Agent Control Plane (`.agent/`)
- [ ] `.agent/rules/production-standards.md`
- [ ] `.agent/rules/.agentignore`
- [ ] `.agent/rules/auto-log.md`
- [ ] `.agent/workflows/code-review.md`
- [ ] `.agent/workflows/generate-tests.md`
- [ ] `.agent/workflows/module-implement.md`

## Phase 2 — AI Knowledge Base (`.ai-context/`)
- [ ] `.ai-context/project_context.md`
- [ ] `.ai-context/architecture.md`
- [ ] `.ai-context/BRD.md`
- [ ] `.ai-context/test_cases.md`
- [ ] `.ai-context/prompt_history.md`
- [ ] `.ai-context/prompts.md`

## Phase 3 — Backend Scaffolding (FastAPI)
- [ ] `backend/pyproject.toml` + `requirements.txt` + `requirements-dev.txt`
- [ ] `backend/.env.example` + `backend/.gitignore`
- [ ] `backend/app/main.py` (app factory)
- [ ] `backend/app/config.py` (Pydantic Settings)
- [ ] `backend/app/database.py` (SQLAlchemy async)
- [ ] `backend/app/dependencies.py`
- [ ] `backend/app/exceptions.py`
- [ ] `backend/app/middleware/` (logging, rate limit)
- [ ] `backend/app/models/` (base, user, team, member, submission, digest, token)
- [ ] `backend/app/schemas/` (auth, team, member, submission, digest, common)
- [ ] `backend/app/api/` (router, v1 routes)
- [ ] `backend/app/services/` (all service layers)
- [ ] `backend/app/tasks/` (scheduler, jobs)
- [ ] `backend/app/utils/` (security, helpers)
- [ ] `backend/alembic/` (migration config)
- [ ] `backend/tests/` (conftest + stubs)
- [ ] `backend/README.md`

## Phase 4 — Frontend Scaffolding (React + Vite + TS)
- [ ] Initialize Vite project
- [ ] `frontend/src/styles/` (variables, index, animations)
- [ ] `frontend/src/config/env.ts`
- [ ] `frontend/src/types/` (api, team, member, submission, digest)
- [ ] `frontend/src/api/` (client, auth, teams, submissions, digests, dashboard)
- [ ] `frontend/src/context/AuthContext.tsx`
- [ ] `frontend/src/hooks/` (useAuth, useTeam, useDigest, useLocalStorage)
- [ ] `frontend/src/components/ui/` (Button, Input, Card, Modal, Spinner, Badge, Toast, ErrorBoundary)
- [ ] `frontend/src/components/layout/` (DashboardLayout, Sidebar, Header, PublicLayout)
- [ ] `frontend/src/components/auth/` (LoginForm, SignupForm, ProtectedRoute)
- [ ] `frontend/src/components/team/` (TeamSetupWizard, MemberList, QuestionEditor)
- [ ] `frontend/src/components/standup/` (StandupForm, SubmitConfirmation)
- [ ] `frontend/src/components/digest/` (DigestView, DigestCard, AISummary)
- [ ] `frontend/src/components/dashboard/` (ResponseChart, BlockerTrends, ParticipationHeatmap, TeamOverview)
- [ ] `frontend/src/pages/` (all pages)
- [ ] `frontend/src/utils/` (formatters, validators, constants)
- [ ] `frontend/src/App.tsx` + `frontend/src/main.tsx`
- [ ] `frontend/.env.example` + config files

## Phase 5 — Root-Level Files
- [ ] `docker-compose.yml`
- [ ] `DOCKER_README.md` (step-by-step Docker/DB guide)
- [ ] Root `.gitignore`
- [ ] Root `README.md`

## Verification
- [ ] Backend starts without errors
- [ ] Frontend builds without errors
