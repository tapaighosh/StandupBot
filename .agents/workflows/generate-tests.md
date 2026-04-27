---
description: Standardized unit test generation workflow for StandupBot
---

# Generate Tests Workflow

Use this workflow to generate comprehensive unit tests for any module or file.

## Steps

1. **Identify the target** — Read the source file(s) to be tested.

2. **Read test cases** — Check `.ai-context/test_cases.md` for pre-defined scenarios relevant to this module.

3. **Determine test framework**:
   - **Backend (Python):** pytest + pytest-asyncio + httpx (for FastAPI TestClient)
   - **Frontend (TypeScript):** Vitest + React Testing Library + MSW (for API mocking)

4. **Generate tests following AAA pattern**:
   ```
   # Arrange — Set up test data, mocks, fixtures
   # Act — Execute the function/endpoint being tested
   # Assert — Verify the expected outcome
   ```

5. **Test categories to cover**:
   - ✅ **Happy path** — Normal successful operation
   - ❌ **Error cases** — Invalid input, missing data, unauthorized access
   - 🔒 **Auth/permissions** — Correct role enforcement
   - ⏱️ **Edge cases** — Boundary values, empty inputs, expired tokens
   - 🔄 **Integration points** — External service failures (LLM, email, Slack)

6. **Backend test structure**:
   ```python
   # File: tests/test_{module}.py
   import pytest
   from httpx import AsyncClient
   
   @pytest.mark.asyncio
   async def test_{feature}_{scenario}(client: AsyncClient, db_session):
       # Arrange
       ...
       # Act
       response = await client.post("/api/v1/...", json={...})
       # Assert
       assert response.status_code == 200
   ```

7. **Frontend test structure**:
   ```typescript
   // File: src/components/{Component}.test.tsx
   import { render, screen, fireEvent } from '@testing-library/react';
   import { describe, it, expect } from 'vitest';
   
   describe('ComponentName', () => {
     it('should render correctly', () => {
       // Arrange
       render(<Component {...props} />);
       // Act & Assert
       expect(screen.getByText('...')).toBeInTheDocument();
     });
   });
   ```

8. **Mocking rules**:
   - Mock ALL external services (database, APIs, email, Slack, LLM)
   - Use factories for test data — never hardcode inline
   - Backend: use `conftest.py` fixtures
   - Frontend: use MSW handlers for API mocking

9. **Coverage target**: 80% minimum per module.

10. **Log the generation** to `.ai-context/prompt_history.md`.
