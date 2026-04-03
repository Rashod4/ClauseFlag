# Task Log

## Current Tasks

### Database Schema Expansion — User Accounts & Saved History
**Date:** 2026-04-03
**Status:** Complete

- [x] Create `users` table (id, username, password_hash, created_at)
- [x] Create `history` table (id, user_id FK, url, analysis_result JSON, created_at)
- [x] Migration/init in `backend/main.py` to auto-create tables on startup
- [x] Add tests for new schema
- [ ] Frontend integration (deferred)

### Authentication & History Endpoints
**Date:** 2026-04-03
**Status:** Complete

- [x] Add `PyJWT` and `bcrypt` dependencies
- [x] Add auth helpers (password hashing, JWT create/decode, FastAPI dependencies)
- [x] `POST /api/register` — create user, return JWT
- [x] `POST /api/login` — verify credentials, return JWT
- [x] `GET /api/history` — requires Bearer token, returns user's saved history
- [x] Modify `POST /api/analyze` to auto-save to `history` when Bearer token is present
- [x] Add tests (15 new tests covering all endpoints + edge cases)
- [ ] Frontend integration (deferred)

### Frontend Authentication & History UI
**Date:** 2026-04-03
**Status:** Complete

- [x] Install `@radix-ui/react-dialog` dependency
- [x] Update `src/apiClient.ts` — token management, auth headers on all requests, `register`/`login`/`fetchHistory` helpers
- [x] Create `src/components/AuthModal.tsx` — Radix Dialog with login/register toggle
- [x] Create `src/components/HistoryPanel.tsx` — collapsible panel with Radix ScrollArea, auto-refreshes after analysis
- [x] Update `src/App.tsx` — auth state, header auth controls, history panel integration
- [x] Vite build + TypeScript check passes

### Structured Clause Explanations
**Date:** 2026-04-03
**Status:** Complete

- [x] Rewrite `backend/explainer.py` — each rule now returns a 3-part explanation (`summary`, `unusual`, `risks`)
- [x] Update `backend/main.py` — serialize explanation dict to JSON on write, parse back on read (with backward compat for old plain strings)
- [x] Update `src/apiClient.ts` — new `ClauseExplanation` interface with `summary`, `unusual`, `risks`
- [x] Update `src/App.tsx` `ClauseCard` — renders three labeled sections instead of a single paragraph
- [x] Strengthen e2e test to assert explanation structure
- [x] All 27 tests pass, Vite build succeeds

### Expanded Testing Coverage
**Date:** 2026-04-03
**Status:** Complete

- [x] Create `tests/test_explainer.py` — 20 unit tests for 3-part explanation structure (all keywords, fallbacks, case insensitivity, singleton, content quality)
- [x] Create `tests/test_auth_history.py` — 18 tests for auth endpoints with edge cases (password hashing, JWT expiry/wrong secret, register/login validation, history isolation between users, backward-compat `_parse_clause_row`)
- [x] Install frontend testing deps (`@testing-library/react`, `@testing-library/jest-dom`, `@testing-library/user-event`, `jsdom`)
- [x] Create `vitest.config.ts` (separate from `vite.config.ts` to avoid ESM-only `@tailwindcss/vite` conflict)
- [x] Create `src/test-setup.ts` with localStorage polyfill for Node v25+
- [x] Create `src/__tests__/apiClient.test.ts` — 7 tests for localStorage token/user helpers
- [x] Create `src/__tests__/App.test.tsx` — 10 tests for main App component (rendering, auth state, mode switching, filter buttons)
- [x] Create `src/__tests__/AuthModal.test.tsx` — 7 tests for AuthModal (fields, toggle, close button, open/closed state)
- [x] Update `package.json` scripts: `test` / `test:frontend` (vitest), `test:backend` (pytest), `test:all` (both sequentially)
- [x] All 90 tests pass (66 backend + 24 frontend)

### Clickable History — Reload Past Analyses
**Date:** 2026-04-03
**Status:** Complete

- [x] Add `raw_text` to `GET /api/analyses/{id}` response in `backend/main.py`
- [x] Add `fetchAnalysis(analysisId)` function and `raw_text` field to `AnalysisResponse` in `src/apiClient.ts`
- [x] Make `HistoryPanel` entries clickable with `onSelect` callback and active-entry highlight
- [x] Wire `handleHistorySelect` in `App.tsx` — loads full analysis results + restores original URL or text input
- [x] Update frontend tests for the new props
- [x] All 90 tests pass (66 backend + 24 frontend)

---

## Discovered During Work
- Node v25+ native `localStorage` conflicts with jsdom's implementation; fixed via custom `MockStorage` in test setup
- Vitest v2 cannot load ESM-only `@tailwindcss/vite` plugin; separate `vitest.config.ts` required
