# QLess Cafe — Helm chart

Helm packaging of the same app as [../base](../base)'s kustomize manifests —
introduced as a parallel/alternative lesson (see [../../README.md](../../README.md)),
not a replacement. Kustomize stays the manifest source for
[../skaffold.yaml](../skaffold.yaml)/Cloud Deploy; this chart is installed
by hand with `helm`.

## Layout

- `values.yaml` — defaults (GKE-leaning, matching `../base`).
- `values-uat.yaml` / `values-prod.yaml` — overrides, mirroring
  `../overlays/{uat,prod}`. `values-uat.yaml` also overrides
  `postgres.storageClassName` to `standard` — `values.yaml`'s default
  (`standard-rwo`) is GKE's Persistent Disk class and doesn't exist on a
  vanilla minikube.
- `secrets-{uat,prod}.yaml.example` — copy to `secrets-{uat,prod}.yaml`
  (git-ignored) and fill in real values. Never commit real secrets.
- `templates/gke-*.yaml` — only rendered when `gke.enabled: true`
  (`values-prod.yaml`): GCE Ingress, ManagedCertificate, FrontendConfig,
  Workload Identity ServiceAccount, BackendConfig.
- `templates/migrate-job.yaml` — a `post-install,pre-upgrade` Helm hook, the
  idiomatic Helm equivalent of `../base/migrate-job.yaml` (which relies on
  kustomize giving it a unique name per release). Deliberately not
  `pre-install`: pre-install hooks run *before* the chart's own
  `configmap.yaml`/`secret.yaml`/`postgres-statefulset.yaml` are created, so
  a pre-install migrate Job would always fail on a fresh install.

## Install

Namespace creation and image tag are supplied at install time, not
hardcoded in templates (per
[Helm's chart conventions](https://helm.sh/docs/chart_best_practices/conventions/)).

UAT (minikube, `ingress-nginx`):

```bash
minikube image load qless-cafe:local   # or push to a registry and set image.repository
helm install qless-cafe . -n qless-cafe-uat --create-namespace \
  -f values-uat.yaml -f secrets-uat.yaml \
  --set image.tag=local
```

Prod (GKE):

```bash
helm install qless-cafe . -n qless-cafe --create-namespace \
  -f values-prod.yaml -f secrets-prod.yaml \
  --set image.repository=australia-southeast1-docker.pkg.dev/sandbox-k8s-as-lego/qless-cafe/qless-cafe \
  --set image.tag=$(git rev-parse --short HEAD)
```

Upgrades: same command with `helm upgrade --install` instead of `helm install`.

## Validate before installing

```bash
helm lint .
helm template qless-cafe . -f values-uat.yaml -f secrets-uat.yaml --set image.tag=local
```

## Tested on minikube

`helm install` with `values-uat.yaml` on a local minikube cluster confirms
the chart's own wiring end-to-end: the `qless-cafe-migrate` post-install hook
connects to Postgres and runs migrations successfully, and Postgres/Redis
come up healthy.

`django`/`celery-worker` won't fully start against a locally-built image on
minikube, though — this is an **existing constraint of the app, not the
chart**: `config.settings.production` unconditionally requires live Google
Cloud Storage credentials (`collectstatic` calls `google.auth.default()`),
which minikube has no way to provide (no GCP metadata server). This is the
same reason the production image is never meant to run outside a
GCS/Workload-Identity-backed environment — see `values-prod.yaml`'s
`gke.serviceAccountEmail`. Nothing to fix here; it's expected.
