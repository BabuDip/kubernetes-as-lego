---
description: "Kubernetes, Docker, and GKE conventions for QLess Cafe"
applyTo: "{k8s/**,compose/**,Dockerfile,docker-compose.yaml}"
---

# Kubernetes / Docker / GKE Instructions

- Two independent deploy targets — don't conflate them: **local** is minikube
  (README.md Steps 3–5); **GKE** is a real cluster with its own standalone
  runbook, [k8s/README.md](../../k8s/README.md). Both apply the same
  [k8s/base](../../k8s/base) manifests via kustomize overlays
  ([k8s/overlays/{uat,prod}](../../k8s/overlays)) — always
  `kubectl apply -k <overlay>`, never apply `base/` directly for uat/prod.
- Three Docker images, don't mix them up:
  - Root `Dockerfile` — minimal `manage.py runserver` image, only for the
    README's Step 2 / minikube walkthrough (SQLite, no Postgres).
  - `compose/local/django/Dockerfile` — dev image for `docker-compose.yaml`
    (uvicorn `--reload`, source bind-mounted).
  - `compose/production/django/Dockerfile` — the real image: built SPA baked
    in, runs gunicorn+uvicorn-worker+celery. Used by both
    `docker-compose.yaml`'s postgres build and every k8s/GKE build. Never
    build the root Dockerfile for a GKE deploy.
- minikube (`docker` driver): the cluster's CPU/mem ceiling is Docker
  Desktop's allocation, not the host's — check with
  `docker info --format '{{.NCPU}} CPUs / {{.MemTotal}} bytes memory'` before
  `minikube start`. Its nodes don't share your local image store: after
  `docker build`, run `minikube image load <tag>` and set
  `imagePullPolicy: Never` in the manifest, or kubelet will try (and fail) to
  pull from a registry.
- GKE builds: `docker build --platform linux/amd64 -f
compose/production/django/Dockerfile` (an arm64 image crash-loops on GKE's
  default node pool), push to Artifact Registry with an immutable tag (git
  SHA — never `:latest`), bump `newTag` under `images:` in
  `k8s/overlays/prod/kustomization.yaml`, then `kubectl apply -k
k8s/overlays/prod`.
- No standalone `kustomize` CLI in this environment — hand-edit
  `kustomization.yaml` directly instead of `kustomize edit set image`.
- Secrets: `k8s/overlays/{uat,prod}/secrets.env` (git-ignored, copy from the
  committed `.example` file) — never commit real secrets there or anywhere
  else.
- For flags/behavior not covered here or in `k8s/README.md`, follow the
  official docs rather than guessing:
  [kubernetes.io/docs](https://kubernetes.io/docs/home/),
  [minikube docs](https://minikube.sigs.k8s.io/docs/),
  [Docker docs](https://docs.docker.com/),
  [kustomize docs](https://kubectl.docs.kubernetes.io/references/kustomize/),
  [GKE docs](https://cloud.google.com/kubernetes-engine/docs).
