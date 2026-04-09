# StandupBot — Project Context

## Product Overview

**StandupBot** is an async daily standup collector for small remote teams (3–20 people). Team members click a personalized link, answer 3 customizable questions, and the manager receives a clean AI-powered digest summary every morning.

**One-line pitch:** Replace your 15-minute standup call with a 2-minute async ritual that actually works.

**Target customer:** Founders and engineering/product managers running remote teams.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | React + Vite + TypeScript |
| **Backend** | Python FastAPI (async) |
| **Database** | PostgreSQL (SQLAlchemy async + Alembic) |
| **Job Scheduler** | APScheduler (in-process) |
| **Email** | Resend or Postmark (transactional) |
| **Slack** | Slack Bolt SDK (Python) |
| **LLM** | OpenAI (GPT-4o-mini) or Anthropic (Haiku) — configurable |
| **Auth** | Google OAuth (manager) + JWT magic links (members) |
| **Payments** | Stripe |
| **Hosting** | Docker → Railway or Render |
| **CSS** | Vanilla CSS + Radix UI (headless components) |

---

## Core Loop (Daily Workflow)

1. **8:00 AM** → Each team member gets a reminder (email or Slack DM) with their personal standup link
2. **8:00–10:00 AM** → Members click the link, answer 3 questions in under 2 minutes (no login required)
3. **10:00 AM** → Manager receives a single digest email/Slack message with all responses, grouped and summarized by AI

## The 3 Questions (Customizable per team)

1. What did you accomplish yesterday?
2. What are you working on today?
3. Any blockers or help needed?

## Two Interfaces

- **Member view** — Clean, dead-simple form. No account needed. Just answer and submit.
- **Manager dashboard** — Today's digest, who hasn't responded, historical trends, blocker highlights.

---

## Module Breakdown

| # | Module | Description |
|---|--------|-------------|
| 1 | Onboarding & Team Setup | Manager signup, team creation, member invites, Slack connection |
| 2 | Link Engine | Unique time-scoped tokens per member per day |
| 3 | Submission Form | Dynamic questions, auto-save, mobile-friendly |
| 4 | Digest Engine | Scheduled collection, LLM summary, email/Slack dispatch |
| 5 | Notification System | Reminders, nudges, manager alerts |
| 6 | Manager Dashboard | Digest view, analytics, settings |
| 7 | Billing & Plans | Free/Starter/Growth tiers via Stripe |

---

## Pricing Tiers

| Plan | Price | Limits |
|------|-------|--------|
| Free | $0 | 1 team, 5 members, 14-day history |
| Starter | $12/mo | 1 team, 15 members, full history |
| Growth | $29/mo | 5 teams, 50 members, analytics, Slack |

---

## Key Design Decisions

1. **APScheduler** for background jobs (digest, reminders) — simpler than Celery for MVP
2. **Google OAuth only** for manager authentication
3. **JWT magic links** for member access — no password, no account creation
4. **LLM as enhancement, not dependency** — digest sends without summary if LLM fails
5. **Independent frontend/backend** — no monorepo tooling, separate projects
6. **Docker** for local development (PostgreSQL)
7. **Vanilla CSS + Radix UI** for responsive, accessible UI components
