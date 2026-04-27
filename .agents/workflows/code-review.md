---
description: Standardized code review workflow for StandupBot codebase
---

# Code Review Workflow

Use this workflow to perform a thorough code review on any file or set of files.

## Steps

1. **Read the file(s)** to be reviewed in full.

2. **Check production standards** — Verify compliance with `.agent/rules/production-standards.md`:
   - [ ] Type hints on all functions (Python) or strict TypeScript types
   - [ ] No bare except blocks; structured error handling
   - [ ] No secrets or hardcoded credentials
   - [ ] Input validation via Pydantic (backend) or typed props (frontend)
   - [ ] Naming conventions followed

3. **Check BRD alignment** — Cross-reference with `.ai-context/BRD.md`:
   - [ ] Does the code implement the specified behavior correctly?
   - [ ] Are edge cases from the BRD handled (e.g., late submissions, token expiry)?
   - [ ] Are non-functional requirements met (performance, security, reliability)?

4. **Security review**:
   - [ ] No SQL injection vectors (parameterized queries only)
   - [ ] No XSS vulnerabilities (sanitized user content)
   - [ ] Authentication/authorization checks in place
   - [ ] Rate limiting on public endpoints
   - [ ] CORS properly configured

5. **Performance review**:
   - [ ] No N+1 query patterns
   - [ ] Async operations used where appropriate
   - [ ] No unnecessary re-renders (frontend)
   - [ ] Database queries use proper indexes

6. **Test coverage check**:
   - [ ] New code has corresponding tests
   - [ ] Tests follow AAA pattern
   - [ ] Edge cases and error paths tested
   - [ ] Mocking used for external services

7. **Output a review summary** with:
   - 🟢 **Approved** items
   - 🟡 **Suggestions** (nice-to-have improvements)
   - 🔴 **Required changes** (must fix before merge)

8. **Log the review** to `.ai-context/prompt_history.md` using the auto-log format.
