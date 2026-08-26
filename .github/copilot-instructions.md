# QLess Cafe Copilot Instructions

Use this file as lightweight repo-wide context. For the full picture, read
`AGENTS.md` — the source of truth for humans and agents. For path-scoped
rules, see `.github/instructions/*.instructions.md`.

## Repo Map

- Backend: Django 6 + DRF + Channels (`qless_cafe/`: `identity`, `catalog`,
  `orders`, `notifications`) and `config/` (settings, urls, asgi). See
  `.github/instructions/python.instructions.md` and
  `.github/instructions/django.instructions.md`.
- Frontend: React 19 + Vite SPA, plain JSX, `frontend/src/`. See
  `.github/instructions/react.instructions.md`.
- Deployment: Docker Compose (`docker-compose.yaml`, `compose/`) for local
  dev; Kubernetes manifests under `k8s/` for minikube/GKE. See
  `.github/instructions/kubernetes.instructions.md`.

## Always Apply

- Run `uv run pre-commit run --all-files` before every commit — mandatory
  even for docs-only changes (see `AGENTS.md`).
- Prefer small, focused changes; follow existing project structure and
  patterns instead of introducing new abstractions.
- Never trust a price or label from the request body — route pricing
  through `catalog.modifiers.resolve_modifiers()`.
- Realtime events only via `notify()`/`notify_managers()` in
  `notifications/services.py`, called inside `transaction.on_commit()`.
- New models use a UUID7 primary key (see `AGENTS.md`'s "Conventions that
  matter").
- Never commit secrets; local config lives in the already-committed
  `.envs/.local/` files.

## Reviews

Prioritize security (server-trusted pricing, session/CSRF handling,
permission checks on `is_staff`-gated endpoints), realtime event correctness
(`transaction.on_commit`), N+1 queries, and missing tests. This project has
not shipped yet, so flag accumulated migrations for a single model change —
see `AGENTS.md`'s pre-first-release migration convention — instead of
leaving `0002_*`/`0003_*` files around.
