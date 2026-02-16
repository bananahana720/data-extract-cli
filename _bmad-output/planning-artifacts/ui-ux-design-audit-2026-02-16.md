# UI/UX Design Audit

Date: 2026-02-16
Project: data-extraction-tool-main
Scope: `ui/` React + MUI application
BMAD skills applied: `bmad-bmm-create-ux-design`, `bmad-review-adversarial-general`
Execution mode: Parallel explorer subagents for IA/flows, design-system coherence, and accessibility

## Method

This audit was aligned to BMAD UX workflow concerns:
- Information architecture and user journeys
- Visual foundation and design token consistency
- Component strategy and reusable interaction patterns
- Responsive/accessibility baseline and interaction feedback

## Findings (Prioritized)

### P1

1. Accent color source-of-truth is split between theme tokens and CSS custom properties.
Evidence: `/home/andrewhana/projects/codex-fun/data-extraction-tool-main/ui/src/theme/tokens.ts:30`, `/home/andrewhana/projects/codex-fun/data-extraction-tool-main/ui/src/styles.css:28`.
Impact: Brand identity and state cues are inconsistent across MUI vs CSS-driven controls.
Recommendation: Generate CSS vars from theme tokens (or inject token-derived vars at app bootstrap).

### P2

2. Success state color semantics diverge between MUI palette and CSS variables.
Evidence: `/home/andrewhana/projects/codex-fun/data-extraction-tool-main/ui/src/theme/theme.ts:50`, `/home/andrewhana/projects/codex-fun/data-extraction-tool-main/ui/src/styles.css:33`.
Impact: Success feedback appears inconsistent and weakens trust in state meaning.
Recommendation: Map CSS success vars directly to tokenized success palette.

3. Error state color semantics diverge between MUI palette and CSS variables.
Evidence: `/home/andrewhana/projects/codex-fun/data-extraction-tool-main/ui/src/theme/theme.ts:62`, `/home/andrewhana/projects/codex-fun/data-extraction-tool-main/ui/src/styles.css:39`.
Impact: Error severity is visually inconsistent across components.
Recommendation: Unify all error colors through token-driven palette exports.

4. Job detail route lacks hierarchy context (no breadcrumb/current-location cue).
Evidence: `/home/andrewhana/projects/codex-fun/data-extraction-tool-main/ui/src/App.tsx:58`.
Impact: Users arriving from deep links can lose orientation in app structure.
Recommendation: Add breadcrumb and page-context title state for detail routes.

5. Job detail page has no explicit back-to-list action.
Evidence: `/home/andrewhana/projects/codex-fun/data-extraction-tool-main/ui/src/pages/JobDetailPage.tsx:347`.
Impact: Core Jobs -> Detail -> Jobs loop is slower and less discoverable.
Recommendation: Add "Back to Jobs" action in the summary/header region.

6. Upload dropzone in New Run is pointer-centric and not keyboard-activatable.
Evidence: `/home/andrewhana/projects/codex-fun/data-extraction-tool-main/ui/src/pages/NewRunPage.tsx:771`.
Impact: Keyboard-only users cannot trigger upload workflow.
Recommendation: Add keyboard focus, semantic button role, and Enter/Space handlers.

### P3

7. App layout lacks a skip link to main content.
Evidence: `/home/andrewhana/projects/codex-fun/data-extraction-tool-main/ui/src/App.tsx:19`.
Impact: Keyboard/screen-reader users must traverse full nav each page load.
Recommendation: Add skip link and `id` target on main content container.

8. New Run file selection summary does not announce updates to assistive tech.
Evidence: `/home/andrewhana/projects/codex-fun/data-extraction-tool-main/ui/src/pages/NewRunPage.tsx:843`.
Impact: Users do not receive confirmation when upload selection changes.
Recommendation: Add `aria-live="polite"` or `role="status"` for file count updates.

9. Jobs list caps at 300 without paging/continuation UX.
Evidence: `/home/andrewhana/projects/codex-fun/data-extraction-tool-main/ui/src/pages/JobsPage.tsx:77`.
Impact: Older jobs become undiscoverable and may appear missing.
Recommendation: Add pagination or load-more affordance with count context.

10. Jobs summary chips use mixed navigation/state behavior that can reset search context.
Evidence: `/home/andrewhana/projects/codex-fun/data-extraction-tool-main/ui/src/pages/JobsPage.tsx:210`.
Impact: Flow interruptions and filter state loss.
Recommendation: Use client-side routing/state updates consistently (`useNavigate` + filter state).

11. New Run source sections remain simultaneously visible despite exclusive source intent.
Evidence: `/home/andrewhana/projects/codex-fun/data-extraction-tool-main/ui/src/pages/NewRunPage.tsx:719`.
Impact: Form hierarchy is cognitively noisy and error-prone.
Recommendation: Collapse/hide non-selected source panel.

12. Blocking validation reasons are surfaced too late in page scan order.
Evidence: `/home/andrewhana/projects/codex-fun/data-extraction-tool-main/ui/src/pages/NewRunPage.tsx:1095`.
Impact: Users cannot quickly diagnose why run start is disabled.
Recommendation: Promote blocking signals inline and/or add sticky top summary.

13. Sessions rows are non-interactive and do not support drill-down.
Evidence: `/home/andrewhana/projects/codex-fun/data-extraction-tool-main/ui/src/pages/SessionsPage.tsx:393`.
Impact: Session table is a dead-end in the investigative workflow.
Recommendation: Link session identifiers to detail or pre-filtered jobs context.

14. Sessions filtered empty state offers only reset, no forward path.
Evidence: `/home/andrewhana/projects/codex-fun/data-extraction-tool-main/ui/src/pages/SessionsPage.tsx:439`.
Impact: Dead-end state increases user thrash.
Recommendation: Add secondary CTA to related jobs/new run.

15. Spacing and focus ring systems are duplicated in CSS and tokenized theme.
Evidence: `/home/andrewhana/projects/codex-fun/data-extraction-tool-main/ui/src/theme/tokens.ts:86`, `/home/andrewhana/projects/codex-fun/data-extraction-tool-main/ui/src/styles.css:11`, `/home/andrewhana/projects/codex-fun/data-extraction-tool-main/ui/src/styles.css:66`.
Impact: Visual drift over time and inconsistent focus semantics.
Recommendation: Eliminate duplicate scale definitions; hydrate CSS vars from theme tokens.

## Suggested Remediation Sequence

1. Token unification pass (colors, spacing, focus, radius) to remove cross-system drift.
2. Navigation and wayfinding pass (breadcrumbs, back links, drill-down affordances).
3. Accessibility interaction pass (skip link, keyboard dropzone, live region announcements).
4. Journey continuity pass (jobs/session pagination, contextual CTAs, inline validation reasons).
5. Regression validation with unit + E2E coverage for updated interaction patterns.

## Audit Notes

- This audit reports design and interaction risks only; no source changes were applied.
- Findings were intentionally adversarial to maximize defect discovery and reduce UX debt.
