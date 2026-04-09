# StandupBot

> Async daily standup collector for small remote teams. Members click a personalized link, answer 3 questions, and the manager receives a clean AI-powered digest summary every morning.

**One-line pitch:** Replace your 15-minute standup call with a 2-minute async ritual that actually works.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React + Vite + TypeScript |
| Backend | Python FastAPI (async) |
| Database | PostgreSQL (SQLAlchemy + Alembic) |
| Scheduler | APScheduler |
| Auth | Google OAuth + JWT magic links |
| LLM | OpenAI / Anthropic (configurable) |
| Payments | Stripe |
| Styling | Vanilla CSS + Radix UI |

---

## Project Structure

```
StandupBot/
├── .agent/                    # Agent rules & workflows
│   ├── rules/                 # Production standards, auto-log
│   └── workflows/             # Code review, test gen, module implement
├── .ai-context/               # AI knowledge base (BRD, architecture, tests)
├── backend/                   # FastAPI Python backend
│   ├── app/                   # Application code
│   │   ├── api/v1/            # API routes
│   │   ├── models/            # SQLAlchemy models
│   │   ├── schemas/           # Pydantic schemas
│   │   ├── services/          # Business logic
│   │   ├── tasks/             # Background jobs
│   │   ├── middleware/        # Logging, rate limiting
│   │   └── utils/             # Security, helpers
│   ├── alembic/               # Database migrations
│   └── tests/                 # pytest test suite
├── frontend/                  # React + Vite + TypeScript frontend
│   └── src/
│       ├── api/               # API client layer
│       ├── components/        # UI components
│       ├── context/           # Auth state management
│       ├── pages/             # Page components
│       ├── styles/            # Design system
│       ├── types/             # TypeScript types
│       └── utils/             # Formatters, validators
├── docker-compose.yml         # PostgreSQL for local dev
├── DOCKER_README.md           # Database setup guide
└── BRD.md                     # Business Requirements Document
```

---

## Quick Start

### 1. Start the Database

```bash
docker compose up -d
```

See [DOCKER_README.md](./DOCKER_README.md) for detailed database setup instructions.

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS/Linux

# Install dependencies
pip install -r requirements-dev.txt

# Configure environment
cp .env.example .env
# Edit .env with your values

# Run migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload --port 8000
```

API docs: http://localhost:8000/docs

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Configure environment
cp .env.example .env

# Start development server
npm run dev
```

App: http://localhost:5173

---

## Module Implementation Order

Use the `/module-implement` workflow to build features step by step:

| Order | Module | What it Does |
|-------|--------|-------------|
| 1 | Auth & Team Setup | Manager signup, team creation, member invites |
| 2 | Link Engine | Magic link token generation + validation |
| 3 | Submission Form | Member standup submission |
| 4 | Digest Engine | AI-powered digest assembly + delivery |
| 5 | Notification System | Reminders, nudges, alerts |
| 6 | Manager Dashboard | Analytics, history, settings |
| 7 | Billing & Plans | Stripe subscription management |

---

## Agent Workflows

| Command | Description |
|---------|-------------|
| `/module-implement` | Step-by-step implementation of any BRD module |
| `/code-review` | Standardized code review checklist |
| `/generate-tests` | Generate tests following AAA pattern |

---

## License

Private — All rights reserved.
