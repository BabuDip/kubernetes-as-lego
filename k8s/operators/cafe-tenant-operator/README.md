# cafe-tenant-operator

A [Kopf](https://kopf.readthedocs.io/)-based Python operator that turns a
`CafeTenant` custom resource into a fully provisioned, isolated tenant:
Namespace + generated secrets + a `k8s/helm-charts` release, with a
reconciliation loop that reflects real rollout status and (optionally) fires
a one-off demo-data seed `Job` once the tenant is `Ready`.

## Why this needs a custom operator (no off-the-shelf tool does this)

Helm/kustomize/ArgoCD all deploy *one* release from *one* set of values you
hand them — none of them turn "a business event" (a new cafe signs up) into
"the right sequence of Kubernetes objects" on their own. That translation
from a domain-specific request (`displayName`, `plan`, `seedDemoData`) into
infrastructure is exactly the kind of app-specific operational knowledge the
[operator pattern](https://kubernetes.io/docs/concepts/extend-kubernetes/operator/)
exists for — see the CRD landscape survey in
[README.md § Step 9](../../../README.md).

## Files

- `crds/cafetenant-crd.yaml` — the `CafeTenant` CRD (cluster-scoped, one per
  tenant), with a validating OpenAPI schema and `status` printer columns.
- `rbac.yaml` — `ServiceAccount`/`ClusterRole`/`ClusterRoleBinding`, scoped to
  exactly the resource kinds this operator (and the chart it installs) touch
  — not cluster-admin.
- `deployment.yaml` — runs the built image in-cluster.
- `operator/handlers.py` — the Kopf handlers (`on.create`/`on.update`/
  `on.delete`/`timer`).
- `examples/sample-cafetenant.yaml` — a CR to try it with.

## Run it locally against minikube (no image build needed)

Kopf is a plain Python process — point it at any reachable cluster via your
current kubeconfig context, no Docker image required for development:

```bash
cd k8s/operators/cafe-tenant-operator
uv sync
kubectl apply -f crds/cafetenant-crd.yaml
QLESS_CAFE_CHART_PATH=../../helm-charts uv run kopf run --standalone operator/handlers.py
```

In another terminal:

```bash
kubectl apply -f examples/sample-cafetenant.yaml
kubectl get cafetenants                      # STATUS column tracks phase
kubectl get all -n cafe-downtown
kubectl delete -f examples/sample-cafetenant.yaml   # triggers helm uninstall + namespace cleanup
```

Expect Postgres/Redis to come up `Running` and `status.phase` to stay
`Provisioning` rather than reach `Ready` — the same
[GCS-credential limitation](../../helm-charts/README.md#tested-on-minikube)
already documented for the Helm chart itself applies here too; this operator
doesn't change the app's own requirements, only automates deploying it.

## Run it in-cluster (built image)

```bash
docker build -f Dockerfile -t cafe-tenant-operator:local ../../..
minikube image load cafe-tenant-operator:local
kubectl apply -f crds/cafetenant-crd.yaml -f rbac.yaml -f deployment.yaml
```

## Known simplifications (would need hardening for real production use)

- Single replica, no leader election — fine for a demo, not for HA.
- `on.delete` fires `helm uninstall` + `delete_namespace` without waiting for
  namespace `Terminating` to fully finish before releasing kopf's finalizer.
- Tenant secrets are generated in-process and only ever read back via
  `helm get values` — no external secret store (Vault/External Secrets)
  integration.
