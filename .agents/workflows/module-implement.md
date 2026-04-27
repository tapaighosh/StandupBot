---
description: Step-by-step workflow to implement any BRD module for StandupBot
---

# Module Implementation Workflow

Use this workflow when implementing any of the 7 BRD modules. Follow every step in order.

## Prerequisites
- Read `.ai-context/BRD.md` — understand the full module specification
- Read `.ai-context/architecture.md` — understand the database schema and API design
- Read `.agent/rules/production-standards.md` — ensure all code matches standards

## Steps

### Step 1 — Understand the Module
1. Read the specific module section from `.ai-context/BRD.md`
2. List all functional requirements for this module
3. Identify dependencies on other modules (e.g., Module 3 depends on Module 2's token system)
4. Confirm any open questions with the user before proceeding

### Step 2 — Database Models
1. Create or update SQLAlchemy models in `backend/app/models/`
2. Ensure models inherit from `Base` and use `TimestampMixin`
3. Define relationships, indexes, and constraints
4. Generate Alembic migration: `alembic revision --autogenerate -m "add {module} models"`
5. Review the generated migration before applying

### Step 3 — Pydantic Schemas
1. Create request/response schemas in `backend/app/schemas/`
2. Include validation rules (min/max length, patterns, enums)
3. Create separate schemas for: Create, Update, Response, List
4. Add example values for OpenAPI documentation

### Step 4 — Service Layer
1. Create business logic in `backend/app/services/`
2. Services should be `async` and accept a database session as parameter
3. Handle all business rules (e.g., submission window validation, token expiry)
4. Implement error handling with custom exceptions from `app/exceptions.py`
5. Add retry/fallback logic for external service calls

### Step 5 — API Routes
1. Create endpoints in `backend/app/api/v1/`
2. Use dependency injection for auth, DB session, and services
3. Add OpenAPI docstrings with descriptions and response models
4. Apply rate limiting to public endpoints
5. Register the router in `backend/app/api/router.py`

### Step 6 — Frontend Components
1. Create page component(s) in `frontend/src/pages/`
2. Create reusable components in `frontend/src/components/{module}/`
3. Add API functions in `frontend/src/api/`
4. Add TypeScript types in `frontend/src/types/`
5. Implement proper loading, error, and empty states
6. Ensure responsive design — test at all breakpoints
7. Add route to `frontend/src/App.tsx`

### Step 7 — Write Tests
1. Follow the `/generate-tests` workflow
2. Backend: Create `backend/tests/test_{module}.py`
3. Frontend: Create `*.test.tsx` files alongside components
4. Verify coverage meets 80% threshold

### Step 8 — Integration Check
1. Start the backend: `cd backend && uvicorn app.main:app --reload`
2. Start the frontend: `cd frontend && npm run dev`
3. Test the full flow end-to-end via the browser
4. Verify API responses match schema expectations

### Step 9 — Update Documentation
1. Log the implementation to `.ai-context/prompt_history.md`
2. Update `.ai-context/test_cases.md` if new test scenarios were discovered
3. Update `README.md` if new setup steps are required

## Module Dependency Order

Implement modules in this order to satisfy dependencies:

```
Module 1: Auth & Team Setup      → No dependencies
Module 2: Link Engine            → Depends on Module 1 (members, teams)
Module 3: Submission Form        → Depends on Module 2 (tokens)
Module 4: Digest Engine          → Depends on Module 3 (submissions)
Module 5: Notification System    → Depends on Modules 1, 2
Module 6: Manager Dashboard      → Depends on Modules 3, 4
Module 7: Billing & Plans        → Depends on Module 1
```
