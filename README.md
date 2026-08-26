# Kubernetes as LEGO: Building Platforms one block at a time

[![CI](https://github.com/BabuDip/kubernetes-as-lego/actions/workflows/ci.yaml/badge.svg)](https://github.com/BabuDip/kubernetes-as-lego/actions/workflows/ci.yaml)
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

## Step 2 — Containerize

Let's package the app into a Docker image, so we can run it anywhere (including Kubernetes).

### Build the image and tag it

```bash
docker build -f Dockerfile -t qless-cafe:v1 .
```

### Run the containerised application from the image

```bash
docker run --rm -it -p 8000:8000 qless-cafe:v1 bash
```

Then, inside the container, run each command yourself:

```bash
uv run manage.py migrate
uv run manage.py seed_demo_data
uv run manage.py runserver 0.0.0.0:8000
```

Now visit <http://localhost:8000/> — same app, same seeded credentials as Step 1.

`Ctrl+C` only stops `runserver` and drops you back to the shell prompt — the
container is still running because `bash`, not `runserver`, is its main process.
Type `exit` (or `Ctrl+D`) to leave the shell and actually stop the container
(`--rm` then removes it automatically).

---

## Step 3 — Start a local Kubernetes cluster (minikube)

minikube runs a Kubernetes cluster locally, with each node as a Docker
container (the `docker` driver).

Check what Docker Desktop has to offer, then size `--cpus`/`--memory` to fit.
Publishing ports 80/443 at start time means the Ingress in Step 5 is reachable
directly on `localhost` later, with no `minikube tunnel` or `kubectl
port-forward` needed — on the `docker` driver that only works cleanly with a
single node, since every extra node would try to bind those same host ports:

```bash
docker info --format '{{.NCPU}} CPUs / {{.MemTotal}} bytes memory'
minikube start --cpus=6 --memory=4000mb --driver=docker --ports=80:80 --ports=443:443
minikube addons enable ingress
kubectl get nodes   # should show STATUS Ready
```

(Curious how far this scales? `minikube start --nodes=N` spins up a genuine
multi-node cluster — just drop `--ports` for that, since node scheduling
across several nodes isn't the focus of the browser demo in Step 5.)

## Step 4 — Define and run your first Pod

A **Pod** is the smallest deployable unit in Kubernetes — one or more
containers scheduled together onto a node.

The `docker` driver's nodes don't share your local image store, so the
`qless-cafe:v1` image from Step 2 needs loading in explicitly:

```bash
minikube image load qless-cafe:v1
```

[k8s/pod.yaml](k8s/pod.yaml) runs the same image and command as Step 2's
`docker run`, using SQLite so it needs nothing else in the cluster:

```bash
kubectl apply -f k8s/pod.yaml
kubectl get pods -o wide   # STATUS should reach Running
```

Migrate and seed it, same as Step 2:

```bash
kubectl exec qless-cafe -- uv run manage.py migrate
kubectl exec qless-cafe -- uv run manage.py seed_demo_data
```

Forward a port and visit it:

```bash
kubectl port-forward pod/qless-cafe 8000:8000
```

Now visit <http://localhost:8000/> — same app, same seeded credentials as
Step 1 and Step 2.

```bash
kubectl logs qless-cafe          # see the runserver output
kubectl delete -f k8s/pod.yaml   # tear the Pod down when you're done
```

---

## Step 5 — Deployments, environments, and kustomize overlays

A **Deployment** manages a Pod for you: self-healing, replicas, rolling
updates. [k8s/base](k8s/base) defines one for the whole app (django,
celery-worker, celery-beat, a postgres StatefulSet, redis, a migrate Job).
[k8s/overlays/uat](k8s/overlays/uat) and [k8s/overlays/prod](k8s/overlays/prod)
layer environment-specific bits on top with kustomize — namespace, replica
counts, Ingress host — so uat and prod run side by side as two isolated
namespaces on the same cluster, each reachable by its own hostname.

### Get the image in shape

The overlays reference `qless-cafe` with no tag, i.e. `:latest`:

```bash
docker tag qless-cafe:v1 qless-cafe:latest
minikube image load qless-cafe:latest
```

### Provide secrets

Each overlay needs a `secrets.env` (git-ignored — never commit real secrets):

```bash
cp k8s/overlays/uat/secrets.env.example k8s/overlays/uat/secrets.env
cp k8s/overlays/prod/secrets.env.example k8s/overlays/prod/secrets.env
# edit both with real values
```

### Map the Ingress hostnames to localhost

Each overlay's Ingress routes on a hostname (`uat.qless.cafe` / `qless.cafe`),
so the browser needs to resolve them to your machine:

```bash
sudo sh -c 'cat >> /etc/hosts << EOF

# QLess Cafe local development (k8s-as-lego)
127.0.0.1  qless.cafe
127.0.0.1  uat.qless.cafe
EOF'
```

`config.settings.local`'s default `ALLOWED_HOSTS` is `localhost`/`127.0.0.1`
only — the overlays patch in `qless.cafe`/`uat.qless.cafe` via
`DJANGO_ALLOWED_HOSTS` (see `k8s/overlays/*/kustomization.yaml`), so this
works without touching app code further.

### Deploy both environments

```bash
kubectl apply -k k8s/overlays/uat
kubectl apply -k k8s/overlays/prod
kubectl get pods -n qless-cafe-uat
kubectl get pods -n qless-cafe-prod
```

Seed each once its `django` Deployment is `Running` (the `migrate` Job already
ran as part of `apply -k`):

```bash
kubectl -n qless-cafe-uat exec deploy/django -- uv run manage.py seed_demo_data
kubectl -n qless-cafe-prod exec deploy/django -- uv run manage.py seed_demo_data
```

### View them in the browser

Because the cluster published ports 80/443 in Step 3, both Ingresses are
already reachable — no `minikube tunnel`, no `kubectl port-forward`, nothing
else to run:

Visit <http://uat.qless.cafe/> and <http://qless.cafe/> side by side.

```bash
kubectl delete -k k8s/overlays/uat    # tear an environment down when you're done
kubectl delete -k k8s/overlays/prod
```

---

## Step 6 — Deploy to a real GKE cluster (HTTPS, Artifact Registry, GCS)

Everything so far ran on minikube. This step takes the exact same
[k8s/base](k8s/base) manifests to a real GKE cluster in its own GCP project,
fronted by a Google-managed TLS certificate on a public domain —
[k8s/overlays/prod](k8s/overlays/prod) is the GKE-specific overlay (one
project, one cluster, one environment — no uat here).

The full step-by-step runbook (VPC, firewall rules, node service account,
the cluster itself, Artifact Registry, GCS buckets for static/media,
Workload Identity, secrets, and the HTTPS Ingress) lives in
**[k8s/README.md](k8s/README.md)**, not here — it's long enough, and specific
enough to a real cloud deployment, that it belongs next to the manifests it
documents rather than in this local-first tutorial.

---

## Step 7 — Package the same app with Helm

Steps 1–6 use kustomize (`k8s/base` + `k8s/overlays/{uat,prod}`) — that stays
the manifest source for [k8s/skaffold.yaml](k8s/skaffold.yaml)/Cloud Deploy.
[k8s/helm-charts](k8s/helm-charts) packages the identical app as a
**Helm chart** instead: the same Deployments/Services/StatefulSet, but as Go
templates driven by `values.yaml` + `values-{uat,prod}.yaml`, rather than
kustomize's base + JSON-patch overlays. It's a second, parallel way to deploy
the same manifests — a lesson in contrasting the two tools, not a
replacement. (One chart today, so it lives flat under `k8s/helm-charts`
rather than `k8s/helm-charts/qless-cafe` — a second chart later would each
get their own subfolder instead.)

```bash
cd k8s/helm-charts
cp secrets-uat.yaml.example secrets-uat.yaml   # edit with real values, git-ignored
helm install qless-cafe . -n qless-cafe-uat --create-namespace \
  -f values-uat.yaml -f secrets-uat.yaml --set image.tag=latest
```

See [k8s/helm-charts/README.md](k8s/helm-charts/README.md) for the
full install/upgrade commands (uat and prod) and how it maps onto the
kustomize overlays.

A chart directory is only half the picture — the other reason to use Helm
over kustomize is that a chart **packages and versions** into something you
can push to a registry and reuse without the source tree at all:

```bash
cd k8s/helm-charts
helm package . --version 0.1.0             # produces qless-cafe-0.1.0.tgz
helm push qless-cafe-0.1.0.tgz oci://REGISTRY/REPO

# anywhere else, no checkout of this repo needed:
helm install qless-cafe oci://REGISTRY/REPO/qless-cafe --version 0.1.0 \
  -f values-prod.yaml --set image.tag=$(git rev-parse --short HEAD)
```

kustomize has no equivalent of this — `k8s/overlays/prod` only ever works
checked out from this exact repo.

---

## Step 8 — Hand-rolled templates vs. official chart dependencies

Everything in [k8s/helm-charts](k8s/helm-charts) is hand-written,
including Postgres and Redis. That's the right call for `django`/`celery-worker`/`celery-beat` — it's our own app, so we want every field
explicit. For infrastructure you *don't* maintain the logic for, Helm's own
answer is chart **dependencies** (subcharts) instead of hand-rolling a
Deployment/StatefulSet for it:

```yaml
# Chart.yaml
dependencies:
  - name: postgresql
    version: "18.x.x"                  # pin a version — see helm's own best practices
    repository: "oci://registry-1.docker.io/bitnamicharts"
    condition: postgresql.enabled       # lets values.yaml turn it on/off
```

`helm dependency update` then downloads it into `charts/` (plus a `Chart.lock`
for reproducible re-fetches), and you configure it under its own namespaced
values key (`postgresql.*`) instead of writing templates for it yourself.

Two things worth knowing before reaching for this:

1. **Namespacing** — a subchart only sees values under its own top-level key
   in the parent's `values.yaml` (`postgresql:` here), except for `global:`
   values, which every chart in the tree can read — see
   [Helm's docs on global values](https://helm.sh/docs/topics/charts/#global-values).
2. **Supply-chain risk** — Bitnami, the most commonly reached-for library of
   "official" charts (Postgres, Redis, Mongo, ...), moved to a paid
   "Bitnami Secure Images" model: only the newest chart version is reliably
   free to pull anonymously, and pinning an exact version — this repo's own
   "immutable tag, never `:latest`" rule (see [AGENTS.md](AGENTS.md)) — can
   quietly stop working later without a subscription. Check a chart's
   licensing model before depending on it in anything that needs to stay
   reproducible.

This repo keeps Redis hand-rolled long-term — it's an ephemeral cache/broker
with no persistence or clustering to justify an off-the-shelf chart. Postgres
is moving to [CloudNativePG](https://cloudnative-pg.io/) in a future step —
a CNCF-hosted operator + `Cluster` custom resource, not a drop-in chart
swap — rather than a paywalled Bitnami subchart.

---

## Step 9 — Custom Resources and the Kopf operator pattern

A **CustomResourceDefinition (CRD)** teaches the Kubernetes API server a new
`kind` — after installing one, `kubectl apply`/`get`/`watch` work on your own
resource exactly like they do on a built-in `Pod` or `Deployment`. On its
own, a CRD is just a validated, versioned bucket of YAML the API server will
store — nothing *acts* on it until an **operator** (a controller that
watches that kind and reconciles the cluster to match) is also running.
[Kopf](https://kopf.readthedocs.io/) is a Python framework for writing that
controller as plain `@kopf.on.create`/`on.update`/`on.delete`/`timer`
functions, instead of Go + client-go/controller-runtime (the traditional
route, e.g. via [Kubebuilder](https://book.kubebuilder.io/) or
[Operator SDK](https://sdk.operatorframework.io/)).

### CRDs you'll actually meet in the wild, and what installs them

Almost every CRD you'll encounter in a real cluster comes bundled with a
specific tool, not written from scratch:

| Tool | CRDs it installs | What they're for |
|---|---|---|
| [cert-manager](https://cert-manager.io/) | `Certificate`, `Issuer`, `ClusterIssuer` | Automated TLS cert issuance/renewal (Let's Encrypt, private CAs) |
| [Prometheus Operator](https://prometheus-operator.dev/) (`kube-prometheus-stack`) | `Prometheus`, `ServiceMonitor`, `PodMonitor`, `PrometheusRule`, `Alertmanager` | Declarative "what to scrape"/"what to alert on" instead of hand-edited scrape configs |
| [CloudNativePG](https://cloudnative-pg.io/) | `Cluster`, `Backup`, `ScheduledBackup`, `Pooler` | Postgres HA, failover, PITR backups — this repo's planned Postgres replacement (Step 8) |
| [external-secrets](https://external-secrets.io/) | `ExternalSecret`, `SecretStore`, `ClusterSecretStore` | Sync secrets from Vault/AWS/GCP Secret Manager into native `Secret` objects |
| [Argo CD](https://argo-cd.readthedocs.io/) | `Application`, `AppProject` | GitOps: "this Git path should equal this cluster state" |
| [Crossplane](https://www.crossplane.io/) | Composite Resource Definitions (XRDs) — user-defined, e.g. `Database`, `Bucket` | Provision *cloud* infra (an RDS instance, a GCS bucket) via `kubectl apply` |
| [KEDA](https://keda.sh/) | `ScaledObject`, `ScaledJob` | Autoscale on external metrics (queue depth, cron) that the HPA can't see |
| [Gateway API](https://gateway-api.sigs.k8s.io/) (successor to `Ingress`) | `GatewayClass`, `Gateway`, `HTTPRoute` | Ingress traffic routing — the annotation-heavy `Ingress` object (this repo's `ingress.yaml`) is being superseded by this |
| Istio / Linkerd (service mesh) | `VirtualService`/`DestinationRule` (Istio), `ServiceProfile` (Linkerd) | Traffic splitting, retries, mTLS between services |
| [Velero](https://velero.io/) | `Backup`, `Restore`, `Schedule` | Cluster/namespace-level backup and disaster recovery |

Notice the pattern: every one of these solves an **infrastructure** problem
that's the same for everybody (TLS, backups, metrics, secrets, autoscaling).
That's precisely why they're pre-built and installable — and precisely why
you should reach for one of these (or a Helm chart per Step 8) rather than
writing your own controller for any of them.

### Where CRDs stop making sense to buy, and start making sense to write

None of the tools above know anything about *this app's* business rules.
[k8s/operators/cafe-tenant-operator](k8s/operators/cafe-tenant-operator) is
a small Kopf operator + `CafeTenant` CRD built for exactly that gap:
provisioning a new, isolated QLess Cafe tenant (its own Namespace, generated
secrets, a `k8s/helm-charts` release, and an optional demo-data seed job) is
an app-specific workflow — Helm/kustomize/Argo CD only ever apply *one* set
of values you hand them; none of them turn "a new cafe signed up" into "the
right Kubernetes objects" by themselves. See its
[README.md](k8s/operators/cafe-tenant-operator/README.md) for the CRD
schema, the Kopf handlers, and how to run it locally against minikube
(no image build required for development).

---

## License

MIT — see [LICENSE](LICENSE).
