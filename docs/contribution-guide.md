# Contribution Guide

## Workflow Expectations

- Keep commits focused and use concise conventional prefixes (`fix:`, `feat(ui):`, `docs:`, `test:`, `chore:`, etc.).
- Include test evidence and affected paths in pull requests.
- For UI changes, include screenshots or interaction notes where relevant.

## Security Rules

- Never commit `.env` or secret-bearing files.
- Use environment variables for credentials and sensitive tokens.
- Validate no secrets are staged before committing.

## Quality Standards

- Run backend quality gates and relevant tests before PR.
- Run UI build + unit tests for UI-impacting changes.
- Preserve API contract compatibility unless explicitly planned and documented.
