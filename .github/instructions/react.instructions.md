---
description: "React/Vite frontend conventions specific to QLess Cafe"
applyTo: "frontend/src/**"
---

# React / Frontend Instructions

- Plain JSX, no TypeScript — don't introduce `.tsx` files or type
  annotations; this project deliberately stays TS-free.
- React 19 + Vite + React Router. ESLint flat config
  (`frontend/eslint.config.js`) + Prettier own formatting — run
  `npm run lint && npm run format:check` before considering frontend work
  done.
- Shared state lives in React Context
  (`src/context/{AuthContext,CartContext,NotificationContext}.jsx`) —
  extend these rather than introducing a new state-management library.
- All backend calls go through `src/api/client.js`'s `api` helper, which
  handles CSRF token fetching/echoing and JSON error unwrapping — don't call
  `fetch()` directly for backend requests.
- `pages/manager/` is staff-only UI, client-side guarded by
  `RequireManager` — mirror that pattern for new manager-only screens, and
  confirm the equivalent server-side permission check exists too (client-side
  guards are UX only, never the real access control).
- The built SPA (`qless_cafe/static/spa/`) isn't committed — after changes
  under `frontend/src/`, rebuild with `npm run build`, or use `npm run dev`
  for live reload against the Docker backend.
- No test suite is configured (no vitest/jest/testing-library) — don't
  assume test files exist or invent a testing framework choice.
