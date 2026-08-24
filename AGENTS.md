# AGENTS.md

Instructions for AI coding agents working in this repository. Humans: see
[README.md](README.md) for the Kubernetes learning-path guide, and
[qless_cafe/README.md](qless_cafe/README.md) for the application write-up
(architecture, API reference, order lifecycle, etc.) — this file only covers what
an agent needs to work safely and productively.

## Stack

- Backend: Python 3.14, Django 6.0.8, Django REST Framework, Django Channels
  (WebSockets) + Redis, Celery + django-celery-beat, PostgreSQL 18. Managed with
  `uv` (`pyproject.toml` / `uv.lock`).
- Frontend: React 19 + Vite, plain JSX (no TypeScript), React Router. `frontend/`
  is a separate npm project.
- Everything runs in Docker Compose by default. A bare local run (no containers,
  SQLite instead of Postgres, in-memory Channels layer, eager Celery, console
  email) is also supported for quick iteration — see
  [qless_cafe/README.md § Bare local run](qless_cafe/README.md#bare-local-run-no-docker).

## Running things

Always go through `just` (a thin wrapper around `docker compose`), not `docker
compose` directly, unless you need flags `just` doesn't expose:

```bash
just up                          # start all services (django, postgres, redis, celeryworker, celerybeat, mailpit)
just manage migrate              # run Django management commands
just manage seed_demo_data       # create demo catalogue + manager/customer accounts
just pytest                      # run the backend test suite
just pytest qless_cafe/orders    # scope to one app
```

Frontend (only needed when editing `frontend/src/`):

```bash
cd frontend && npm install
npm run build   # one-shot build into ../qless_cafe/static/spa/ (this build output is not committed)
npm run dev     # live reload at :5173, proxies /api and /ws to the Django container on :8000
```

## Before every commit (mandatory, no exceptions)

CI runs `pre-commit` across **every file in the repo** on every PR — docs-only,
YAML-only, and markdown-only changes are not exempt (README.md whitespace has
broken CI before). Strict adherence to this project's policy means running
this locally before every commit, not just before "code" changes:

```bash
uv run pre-commit run --show-diff-on-failure --color=always --all-files
```

- If it reports "files were modified by this hook", that is not optional
  cleanup — `git add` the modified files and re-run the command until it is
  fully green, *then* commit.
- Never commit or push while a pre-commit run is still reporting failures or
  unstaged hook-modified files. A dirty/red pre-commit run is the single most
  common avoidable CI failure in this repo — do not rely on CI to catch it.
- This applies in addition to (not instead of) the backend-specific checks
  below when the change touches backend code.

## Checks to run before considering backend work done

```bash
docker compose -f docker-compose.local.yml run --rm django ruff check .
docker compose -f docker-compose.local.yml run --rm django ruff format --check .
docker compose -f docker-compose.local.yml run --rm django mypy qless_cafe
docker compose -f docker-compose.local.yml run --rm django pytest
```

Frontend: `npm run lint && npm run format:check` inside `frontend/`.

## Code layout

- `qless_cafe/identity` — custom `User` model (email login, no username), session
  auth API.
- `qless_cafe/catalog` — categories, products, and `modifiers.py` (the single
  place that resolves a modifier selection into a price and label).
- `qless_cafe/orders` — `Order`/`OrderItem`, checkout, the Kanban status
  workflow, the receipt-email Celery task.
- `qless_cafe/notifications` — the Channels consumer and the only two functions
  allowed to publish realtime events: `notify()` and `notify_managers()` in
  `notifications/services.py`.
- `config/settings/{base,local,production,test}.py` — environment-driven
  settings (`django-environ`).
- `frontend/src/{pages,components,context,api,utils}` — standard React SPA
  layout; `pages/manager/` is staff-only (guarded client-side by `RequireManager`
  and server-side by each view's own permission check).

## Conventions that matter

- **New models use a UUID7 primary key**: `id = models.UUIDField(primary_key=True,
  default=uuid.uuid7, editable=False)` (stdlib `uuid.uuid7`, no extra dependency).
- **Pre-first-release migration convention**: this project has not shipped yet, so
  when a model changes, delete that app's existing migration file(s) and
  regenerate a single fresh `0001_initial` via `makemigrations` rather than
  accumulating `0002_*`, `0003_*`, etc. Reset Docker volumes and migrate fresh
  afterward. Start keeping incremental migrations once there is real data.
- **Session auth only** — no JWT, no `django-allauth`. The SPA is same-origin;
  `GET /api/auth/csrf/` primes the CSRF cookie before any unsafe request.
- **Manager = `is_staff=True`** on the standard `User` model — there is no
  separate Manager model or group.
- **Server-trusted pricing** — the client only ever sends modifier *selections*;
  `catalog.modifiers.resolve_modifiers()` is the only place a price or label is
  computed. Never trust a price from the request body.
- **Realtime events only go through `notify()` / `notify_managers()`** — nothing
  else should call `group_send` directly, and both should be called from inside
  `transaction.on_commit()` so an event never fires for a rolled-back change.
- No i18n (`USE_I18N = False`) — don't add `gettext`/translation machinery.

## Things that don't exist yet (don't assume otherwise)

- No `docs/adr/` or `docs/worklog/` — there are no ADRs or worklogs to consult.
- No frontend test suite (no vitest/jest/testing-library configured).
- No `.env.example` — the local dev env files under `.envs/.local/` are already
  committed with working (non-secret) values; only `.envs/.production/` is
  git-ignored.
