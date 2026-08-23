# K8s as Lego

A hands-on, step-by-step path from *"a working application"* to *"that application
running on Kubernetes"* — building up the pieces one Lego brick at a time instead of
dropping a finished cluster manifest on day one.

The demo application is **[QLess Cafe](qless_cafe/README.md)**, a full order-ahead
cafe app (Django + DRF + Channels + Celery backend, React SPA frontend, PostgreSQL,
Redis). It's a real, non-trivial app on purpose — a "hello world" container doesn't
exercise the things that actually make deploying to Kubernetes interesting: a
database, background workers, WebSockets, scheduled tasks, secrets, and a build step
for the frontend.

See [qless_cafe/README.md](qless_cafe/README.md) for the full application
documentation — architecture, API reference, order lifecycle, tech stack, testing,
etc. This README only tracks the Kubernetes learning path built around it.

---

## The Plan

Each step below adds one new concept on top of the previous one, without changing
what the application actually does. Steps are checked off as they're written up.

- [x] **Step 0 — Run the app locally.** No containers, no orchestration — just the
      Django dev server and SQLite, to confirm what "working" looks like before any
      infrastructure gets layered on top. *(see below)*
- [ ] **Step 1 — Containerize.** Package the backend (and later the frontend build)
      as Docker images.
- [ ] **Step 2 — Local multi-container orchestration.** Run the full stack (app,
      Postgres, Redis, Celery worker/beat) together with Docker Compose.
- [ ] **Step 3 — Kubernetes fundamentals.** Pods, Deployments, Services — get the
      same containers running on a local cluster (e.g. kind/minikube).
- [ ] **Step 4 onward — TBD** as the guide progresses (config/secrets, persistent
      storage, ingress, scaling, health checks, CI/CD, …).

---

## Step 0 — Run the app locally

Before containerizing anything, get the application itself running bare-metal —
straight `python manage.py runserver`, no Docker, no Postgres or Redis install
required.

### Prerequisites

- Python 3.14
- [uv](https://docs.astral.sh/uv/) (manages the virtualenv and dependencies)

### Run the backend

```bash
uv sync
export DJANGO_SETTINGS_MODULE=config.settings.local
uv run python manage.py migrate
uv run python manage.py seed_demo_data
uv run python manage.py runserver
```

With no `POSTGRES_*` environment variables set, Django automatically falls back to
a local SQLite database (`db.sqlite3`) — see
[qless_cafe/README.md § Bare local run](qless_cafe/README.md#bare-local-run-no-docker)
for exactly what else gets swapped out (Celery, Channels, email) and why.

`seed_demo_data` is idempotent (safe to re-run) and creates a demo catalogue plus
two test accounts:

| Role | Email | Password |
|------|-------|----------|
| Manager | `manager@qless.cafe` | `Manager-Pass-123!` |
| Customer | `customer@qless.cafe` | `Customer-Pass-123!` |

### Try it out

Visit <http://localhost:8000/> and log in as the customer to browse the menu and
place an order, or <http://localhost:8000/manage> as the manager to see it land on
the live Kanban board.

> The frontend isn't built yet at this point — `manage.py runserver` alone serves
> API/admin routes. To see the actual UI, also build or run the SPA (see
> [qless_cafe/README.md § Getting Started](qless_cafe/README.md#getting-started)).

Once you can place an order as the customer and watch it move through the Kanban
board as the manager, the app is confirmed working end-to-end — that's the baseline
Step 1 will package into a container without changing.

---

## License

MIT — see [LICENSE](LICENSE).
