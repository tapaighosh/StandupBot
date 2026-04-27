---
description: Global production coding standards enforced on all agent interactions for the StandupBot project
---

# Production Standards

These rules MUST be followed in all code generation, reviews, and modifications across the StandupBot project.

---

## Python / Backend (FastAPI)

### Style & Structure
- Follow **PEP 8** strictly. Line length: 120 characters max.
- Use **type hints** on ALL function parameters and return types — no exceptions.
- Use `async def` by default for all route handlers and service methods.
- Use **Pydantic v2** models for ALL request/response schemas.
- All database models must inherit from the `Base` class in `app/models/base.py`.
- Every model must include `created_at` and `updated_at` timestamp fields via `TimestampMixin`.

### Naming Conventions
- Files: `snake_case.py`
- Classes: `PascalCase`
- Functions/variables: `snake_case`
- Constants: `UPPER_SNAKE_CASE`
- API route prefixes: `/api/v1/{resource}` (plural nouns)

### Error Handling
- NEVER use bare `except:` — always catch specific exceptions.
- All API errors must return structured JSON: `{ "detail": str, "code": str }`.
- Use custom exceptions from `app/exceptions.py` — never raise raw `HTTPException` in service layers.
- All external service calls (LLM, email, Slack, Stripe) MUST have try/except with fallback behavior.
- LLM failures must NEVER block digest delivery.

### Security
- **No secrets in code** — all sensitive values come from environment variables via `app/config.py`.
- All user input MUST be validated via Pydantic schemas before reaching service layer.
- Use parameterized queries only — no raw SQL string interpolation.
- JWT tokens must have expiration times. Refresh tokens must be rotatable.
- CORS must be configured with explicit allowed origins — never use `*` in production.
- Rate limiting must be applied to all public-facing endpoints.

### Database
- Use **SQLAlchemy async** with `asyncpg` driver.
- All schema changes go through **Alembic migrations** — never modify DB directly.
- Use UUID primary keys for all models.
- Implement soft-delete pattern where business logic requires data retention.
- Always use transactions for multi-step operations.

### Testing
- Minimum **80% code coverage** target.
- Use **pytest** with `pytest-asyncio` for async tests.
- Follow **Arrange-Act-Assert (AAA)** pattern.
- Use fixtures and factories — never hardcode test data inline.
- All new features MUST ship with corresponding tests.

---

## TypeScript / Frontend (React + Vite)

### Style & Structure
- `tsconfig.json` must have `"strict": true` — no exceptions.
- Use **named exports** — avoid default exports (except for pages/lazy-loaded routes).
- Use **functional components** with hooks — no class components.
- All component props must be typed with explicit interfaces (suffix: `Props`).
- No `any` type — use `unknown` if type is genuinely uncertain, then narrow.

### Naming Conventions
- Components: `PascalCase.tsx`
- Hooks: `useCamelCase.ts`
- Utilities: `camelCase.ts`
- Types: `PascalCase` (interfaces prefixed with descriptive name, NOT `I`)
- CSS files: `kebab-case.css`

### Error Handling
- All pages must be wrapped in `ErrorBoundary` components.
- API calls must handle errors with user-friendly toast messages.
- Never swallow errors silently — log or display them.
- Use TypeScript discriminated unions for API response states: `loading | success | error`.

### Security
- NEVER store sensitive data in localStorage except JWT tokens.
- Sanitize all user-generated content before rendering.
- API base URL must come from environment variables.
- No inline `<script>` tags or `dangerouslySetInnerHTML` without explicit sanitization.

### Accessibility & Responsiveness
- All interactive elements must be keyboard-accessible.
- Use semantic HTML elements (`<main>`, `<nav>`, `<section>`, `<article>`).
- All images must have `alt` attributes.
- Design must be responsive — mobile-first approach, breakpoints at 480px, 768px, 1024px, 1280px.
- Minimum touch target size: 44x44px on mobile.

### Performance
- Lazy-load pages with `React.lazy()` and `Suspense`.
- Memoize expensive computations with `useMemo` and callbacks with `useCallback`.
- Avoid unnecessary re-renders — use React DevTools Profiler to verify.

---

## Git & Version Control

- **Conventional Commits**: `feat:`, `fix:`, `chore:`, `docs:`, `test:`, `refactor:`
- Branch naming: `feat/module-name`, `fix/issue-description`, `chore/task-name`
- Atomic PRs: one feature or fix per pull request
- No commits to `main` directly — always use feature branches

---

## Documentation

- Every new module must have a docstring/comment block explaining its purpose.
- API endpoints must have OpenAPI docstrings (FastAPI auto-generates docs from these).
- README files must be kept up-to-date with setup instructions.
- All environment variables must be documented in `.env.example`.
