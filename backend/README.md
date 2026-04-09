# StandupBot — Backend

Async daily standup collector for remote teams. Built with **FastAPI** (Python 3.11+).

## Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL 15+ (via Docker — see `DOCKER_README.md` in project root)

### Setup

```bash
# Create virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Activate (macOS/Linux)
source .venv/bin/activate

# Install dependencies
pip install -r requirements-dev.txt

# Copy environment variables
cp .env.example .env
# Edit .env with your actual values

# Start PostgreSQL (from project root)
docker compose up -d

# Run database migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload --port 8000
```

### API Documentation
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health check: http://localhost:8000/api/v1/health/

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=term-missing

# Run specific test file
pytest tests/test_health.py -v
```

### Linting

```bash
# Check code style
ruff check app/

# Auto-fix issues
ruff check --fix app/

# Format code
ruff format app/
```

## Project Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI app factory
│   ├── config.py             # Pydantic Settings
│   ├── database.py           # SQLAlchemy async engine
│   ├── dependencies.py       # Shared FastAPI dependencies
│   ├── exceptions.py         # Custom exceptions + handlers
│   ├── middleware/            # Request logging, rate limiting
│   ├── models/               # SQLAlchemy ORM models
│   ├── schemas/              # Pydantic request/response schemas
│   ├── api/v1/               # API route handlers
│   ├── services/             # Business logic layer
│   ├── tasks/                # Background jobs (APScheduler)
│   └── utils/                # Security, helpers
├── alembic/                  # Database migrations
├── tests/                    # pytest test suite
└── requirements.txt          # Production dependencies
```
