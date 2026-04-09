# StandupBot — Quick Reference Prompts

Quick-reference prompt snippets for common development tasks. Use these as starting points.

---

## Module Implementation

```
Implement Module [N] — [Module Name] following the /module-implement workflow.
Read the BRD section for Module [N] and implement all backend + frontend components.
```

## Code Review

```
Review the following files using the /code-review workflow:
- [file paths]
Focus on: [security / performance / BRD compliance / all]
```

## Generate Tests

```
Generate tests for [file or module] using the /generate-tests workflow.
Reference test cases from .ai-context/test_cases.md section [Module N].
```

## Debug an Issue

```
Debug the following issue: [description]
Steps to reproduce: [steps]
Expected behavior: [expected]
Actual behavior: [actual]
```

## Add a New API Endpoint

```
Add a new endpoint: [METHOD] /api/v1/[path]
Purpose: [description]
Request body: [schema or description]
Response: [schema or description]
Auth required: [yes/no]
Follow production-standards.md for error handling and validation.
```

## Database Migration

```
Create a new database migration for: [description of schema change]
1. Update the SQLAlchemy model in backend/app/models/[file].py
2. Generate migration: alembic revision --autogenerate -m "[description]"
3. Review the migration file
4. Apply: alembic upgrade head
```

## Frontend Component

```
Create a new React component: [ComponentName]
Purpose: [what it does]
Props: [list of props with types]
Location: frontend/src/components/[category]/
Must be: responsive, accessible, typed, with loading/error states.
```

## Deploy Checklist

```
Pre-deployment checklist:
1. All tests pass: pytest (backend) + npm test (frontend)
2. No lint errors: ruff check (backend) + npm run lint (frontend)
3. Build succeeds: npm run build (frontend)
4. Environment variables documented in .env.example
5. Database migrations applied
6. Health check endpoint responding
```
