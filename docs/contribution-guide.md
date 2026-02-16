# Contribution Guide

## Workflow Expectations

- Keep commits focused and use concise conventional prefixes (`fix:`, `feat(ui):`, `docs:`, `test:`, `chore:`, etc.).
- Include test evidence and affected paths in pull requests.
- For UI changes, include screenshots or interaction notes where relevant.
- Mention rollback or migration notes for behavior-impacting changes.
- Split large changes by slice and document sequencing in PR description.

## Security Rules

- Never commit `.env` or secret-bearing files.
- Use environment variables for credentials and sensitive tokens.
- Validate no secrets are staged before committing.
- Never hardcode credentials in docs, examples, scripts, or code.
- Confirm `.env` and environment-specific templates remain out of git history.

## Quality Standards

- Run backend quality gates and relevant tests before PR.
- Run UI build + unit tests for UI-impacting changes.
- Preserve API contract compatibility unless explicitly planned and documented.

## Change categories and suggested evidence

- `docs:`: include changed file list plus verification command (for doc validation if applicable).
- `fix:` or `feat:`: include reproduction steps and before/after behavior notes.
- `test:`: include objective assertions and failure surface covered.
- `refactor:`: include why behavior is unchanged and where regression tests guard key flow.

## Pull-request checklist

- [ ] Scope is explicit and scoped to one goal.
- [ ] Test evidence provided (commands and outputs summary).
- [ ] Relevant docs updated (including this guide and impacted references).
- [ ] Security checklist acknowledged for any auth/config/runtime changes.
- [ ] Any API change notes API compatibility impact.
- [ ] Screenshots or interaction notes included for UI changes.

## Review and merge expectations

- Prefer early review on high-impact docs that alter onboarding, API, deployment, or run semantics.
- Call out assumptions and trade-offs in PR description when behavior or dependency assumptions change.
- Add follow-up tasks if the change creates documentation gaps.
