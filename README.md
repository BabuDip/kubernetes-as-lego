# Kubernetes as LEGO: Building Platforms one block at a time

[![CI](https://github.com/BabuDip/kubernetes-as-lego/actions/workflows/ci.yml/badge.svg)](https://github.com/BabuDip/kubernetes-as-lego/actions/workflows/ci.yml)
[![Python 3.14](https://img.shields.io/badge/python-3.14-3776AB?logo=python&logoColor=white)](pyproject.toml)
[![Django 6.0](https://img.shields.io/badge/django-6.0-092E20?logo=django&logoColor=white)](pyproject.toml)
[![React 19](https://img.shields.io/badge/react-19-61DAFB?logo=react&logoColor=white)](frontend/package.json)
[![uv](https://img.shields.io/badge/managed%20by-uv-DE5FE9?logo=uv&logoColor=white)](https://docs.astral.sh/uv/)
[![Docker](https://img.shields.io/badge/docker-required-2496ED?logo=docker&logoColor=white)](https://docs.docker.com/get-docker/)
[![Kubernetes](https://img.shields.io/badge/kubernetes-kind%20%2F%20minikube-326CE5?logo=kubernetes&logoColor=white)](https://kubernetes.io/)
[![kubectl](https://img.shields.io/badge/kubectl-required-326CE5?logo=kubernetes&logoColor=white)](https://kubernetes.io/docs/tasks/tools/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

This is the companion repo (playground) for the PyCon AU 2026 talk **[Kubernetes as LEGO: Building
Platforms one block at a time](https://2026.pycon.org.au/schedule/7JZY3E/)** — a
hands-on walkthrough guiding you through the nitty-gritty of building a platform from a real-world business problem to global scale, with the fun analogy and simplicity of LEGO bricks.

>
> - **Level 1 — Raw primitives**: Pods, Deployments, Services, ConfigMaps etc.
> - **Level 2 — Helm and Kustomize**: Helm for consuming and distributing packages;
>   Kustomize for environment overlays of the apps you own.
> - **Level 3 — Python operators with kopf**: when the built-in API can't express
>   your domain logic, Custom Resource Definitions (CRDs) let you extend it.
>

The demo application is **[QLess Cafe](qless_cafe/README.md)**, a full order-ahead
cafe app (Django + DRF + Channels + Celery backend, React SPA frontend, PostgreSQL,
Redis).

See [qless_cafe/README.md](qless_cafe/README.md) for the full application
documentation — architecture, API reference, order lifecycle, tech stack, testing,
etc.

---

## Prerequisites

What you need on your machine to follow along with the talk:

| Tool | Needed for |
|------|------------|
| [Python 3.14](https://www.python.org/downloads/) | bare local run |
| [uv](https://docs.astral.sh/uv/) | bare local run — manages the virtualenv and Python deps |
| [Node.js 20+](https://nodejs.org/) + npm | When building/running the SPA or editing `frontend/src/`; Django/Docker serves the generated static files |
| [Docker](https://docs.docker.com/get-docker/) & [Docker Compose](https://docs.docker.com/compose/install/) | Containerising and running a containerised application |
| [kind](https://kind.sigs.k8s.io/) or [minikube](https://minikube.sigs.k8s.io/) + `kubectl` | Running Kubernetes locally |
| [Helm](https://helm.sh/) & [Kustomize](https://kustomize.io/) | Running different Kubernetes configurations and overlays (different environments) |
| [kopf](https://kopf.readthedocs.io/) (Python, installed via `uv`) | Building operators and Custom Resource Definitions (CRDs) |

---

## Step 1 — Run the app locally

With the help of Cookiecutter Django, the application is scaffolded quickly, so you can run it locally:

### Build the frontend SPA (React) and serve it via Django
```bash
cd frontend # go into the frontend directory
npm install # install dependencies
npm run build # build the SPA into static files (served by Django)
```

### Run the backend (Django) locally
```bash
uv sync
export DJANGO_SETTINGS_MODULE=config.settings.local
uv run python manage.py migrate
uv run python manage.py seed_demo_data # seed the database with demo data (users, menu, etc.)
uv run python manage.py runserver
```

Now visit <http://localhost:8000/> to see the app running locally.
You can use the credentials below to log in as a manager or customer, seeded by the `seed_demo_data` command:

| Role | Email | Password |
|------|-------|----------|
| Manager | `manager@qless.cafe` | `Manager-Pass-123!` |
| Customer | `customer@qless.cafe` | `Customer-Pass-123!` |

---

## License

MIT — see [LICENSE](LICENSE).
