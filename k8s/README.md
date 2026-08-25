# Deploying to a real GKE cluster

> Part of the [k8s-as-lego](../README.md) Kubernetes learning repo — see the root
> README for the local/minikube tutorial (Steps 1–5). This document is the
> standalone runbook for the *other* deployment target: a real GKE cluster in its
> own GCP project, fronted by a Google-managed TLS certificate on a public
> domain.

Everything in the root README's Step 5 ran on minikube. This doc takes the
exact same [base](base) manifests to GKE — [overlays/prod](overlays/prod) is
the GKE-specific overlay (there's no uat here: one project, one cluster, one
environment). Replace `sandbox-k8s-as-lego` / `australia-southeast1` /
`qless-cafe.example.com` throughout with your own project, region,
and domain.

## 1 — A standalone VPC

No Shared VPC, no host/service project split — this cluster gets its own VPC,
entirely contained in the sandbox project, with private nodes and Cloud NAT
for outbound internet access (pulling base images, talking to Google APIs):

```bash
gcloud compute networks create qless-cafe-vpc --project=sandbox-k8s-as-lego --subnet-mode=custom

gcloud compute networks subnets create qless-cafe-subnet \
  --project=sandbox-k8s-as-lego --network=qless-cafe-vpc --region=australia-southeast1 \
  --range=10.10.0.0/20 --enable-private-ip-google-access \
  --secondary-range=pods=10.16.0.0/14,services=10.20.0.0/20

# Cloud NAT: private nodes have no external IP of their own.
gcloud compute routers create qless-cafe-router \
  --project=sandbox-k8s-as-lego --network=qless-cafe-vpc --region=australia-southeast1
gcloud compute routers nats create qless-cafe-nat \
  --project=sandbox-k8s-as-lego --router=qless-cafe-router --region=australia-southeast1 \
  --auto-allocate-nat-external-ips --nat-all-subnet-ip-ranges

# Only what's needed: in-VPC traffic, IAP-tunneled SSH (no public :22), and
# the load balancer's health-check ranges.
gcloud compute firewall-rules create qless-cafe-allow-internal \
  --project=sandbox-k8s-as-lego --network=qless-cafe-vpc --direction=INGRESS \
  --source-ranges=10.10.0.0/20,10.16.0.0/14,10.20.0.0/20 --allow=tcp,udp,icmp
gcloud compute firewall-rules create qless-cafe-allow-iap-ssh \
  --project=sandbox-k8s-as-lego --network=qless-cafe-vpc --direction=INGRESS \
  --source-ranges=35.235.240.0/20 --allow=tcp:22
gcloud compute firewall-rules create qless-cafe-allow-lb-health-checks \
  --project=sandbox-k8s-as-lego --network=qless-cafe-vpc --direction=INGRESS \
  --source-ranges=130.211.0.0/22,35.191.0.0/16 --allow=tcp:8000

# Reserved ahead of time so the Ingress (step 8) and your DNS A record both
# have a fixed target from the start.
gcloud compute addresses create qless-cafe-ip --project=sandbox-k8s-as-lego --global
gcloud compute addresses describe qless-cafe-ip --project=sandbox-k8s-as-lego --global --format='value(address)'
```

No firewall rule here allows `0.0.0.0/0` on any port — every ingress rule is
scoped to either an internal VPC range or a Google-managed source range (IAP,
GFE health checks). GKE itself also auto-creates a couple of rules scoped to
the pod/node CIDRs and the GFE ranges for the Ingress in step 8 — that's
expected, not something to prune.

## 2 — A minimal-scope node service account

GKE nodes run as a service account — never the Compute Engine default one.
This one can only write logs/metrics and pull from Artifact Registry:

```bash
gcloud iam service-accounts create qless-cafe-gke-node \
  --project=sandbox-k8s-as-lego --display-name="QLess Cafe GKE node SA"

for role in roles/logging.logWriter roles/monitoring.metricWriter \
            roles/monitoring.viewer roles/stackdriver.resourceMetadata.writer \
            roles/artifactregistry.reader; do
  gcloud projects add-iam-policy-binding sandbox-k8s-as-lego \
    --member="serviceAccount:qless-cafe-gke-node@sandbox-k8s-as-lego.iam.gserviceaccount.com" \
    --role="$role"
done
```

## 3 — The cluster

Zonal (not regional) to keep a demo cluster cheap; private nodes, Shielded
VMs, network policy enabled, and Workload Identity turned on for step 6:

```bash
gcloud container clusters create qless-cafe-demo \
  --project=sandbox-k8s-as-lego --location=australia-southeast1-a \
  --network=qless-cafe-vpc --subnetwork=qless-cafe-subnet \
  --cluster-secondary-range-name=pods --services-secondary-range-name=services \
  --enable-ip-alias \
  --enable-private-nodes --master-ipv4-cidr=172.16.0.0/28 \
  --enable-master-authorized-networks --master-authorized-networks=0.0.0.0/0 \
  --enable-shielded-nodes --shielded-secure-boot --shielded-integrity-monitoring \
  --enable-network-policy \
  --workload-pool=sandbox-k8s-as-lego.svc.id.goog \
  --release-channel=regular \
  --num-nodes=2 --machine-type=e2-standard-4 --disk-type=pd-standard --disk-size=50 \
  --service-account=qless-cafe-gke-node@sandbox-k8s-as-lego.iam.gserviceaccount.com \
  --no-enable-basic-auth --no-issue-client-certificate \
  --labels=app=qless-cafe,env=prod

gcloud container clusters get-credentials qless-cafe-demo \
  --project=sandbox-k8s-as-lego --location=australia-southeast1-a
kubectl get nodes -o wide   # both should be Ready, with no EXTERNAL-IP
```

Two known gaps to close before this cluster outlives the conference demo it
was built for:

- `--master-authorized-networks=0.0.0.0/0` is a demo-only shortcut — the
  control plane's public endpoint is reachable from any IP (auth-protected
  only by client cert/token). Restrict it to your office/VPN CIDR for
  anything longer-lived.
- `--enable-network-policy` turns on the Calico enforcement engine, but no
  [NetworkPolicy](https://kubernetes.io/docs/concepts/services-networking/network-policies/)
  objects exist yet in [base](base) — so pod-to-pod traffic inside the
  cluster is still effectively default-allow (any pod could reach
  `postgres:5432`/`redis:6379` directly). Add explicit policies before
  treating this as anything more than a demo.

## 4 — Artifact Registry, built and pushed by hand

No Cloud Build for this cluster — plain `docker build`/`docker push`:

```bash
gcloud artifacts repositories create qless-cafe \
  --project=sandbox-k8s-as-lego --location=australia-southeast1 --repository-format=docker
gcloud auth configure-docker australia-southeast1-docker.pkg.dev

IMAGE=australia-southeast1-docker.pkg.dev/sandbox-k8s-as-lego/qless-cafe/qless-cafe
TAG=$(git rev-parse --short HEAD)   # an immutable tag — never deploy :latest
# Run from the repo root. NOT the root Dockerfile (that one is the minikube
# tutorial's minimal runserver image) — this one bakes in the built SPA and
# runs gunicorn+uvicorn.
docker build --platform linux/amd64 -f compose/production/django/Dockerfile -t "${IMAGE}:${TAG}" .
docker push "${IMAGE}:${TAG}"
```

`--platform linux/amd64` matters if you're building on Apple Silicon — GKE's
default node pool is amd64, and an arm64 image just crash-loops on it.

## 5 — Two GCS buckets: public static, private media

`STATIC_URL` needs a stable, public prefix; `MEDIA_URL` (user/staff-uploaded
product photos) doesn't need to be public at all. Splitting them into two
buckets — one with public read, one entirely private behind
[signed URLs](https://django-storages.readthedocs.io/en/latest/backends/gcloud.html) —
is what [../config/settings/production.py](../config/settings/production.py)'s
`STORAGES` expects:

```bash
gcloud storage buckets create gs://sandbox-k8s-as-lego-qless-cafe-static \
  --project=sandbox-k8s-as-lego --location=australia-southeast1 --uniform-bucket-level-access
gcloud storage buckets create gs://sandbox-k8s-as-lego-qless-cafe-media \
  --project=sandbox-k8s-as-lego --location=australia-southeast1 --uniform-bucket-level-access
```

Most orgs also run
[`iam.managed.allowedPolicyMembers`](https://cloud.google.com/resource-manager/docs/organization-policy/organization-policy-constraints),
which blocks granting `allUsers` any role — public buckets included — unless a
resource carries a specific exemption tag. If that applies to you, bind
whatever conditional tag your org already defines for this (ask your org
admin — don't invent a new tag key) to the **project**, not the bucket
(bucket-level tag bindings aren't supported by this API):

```bash
gcloud resource-manager tags bindings create \
  --tag-value=ORGANIZATION_ID/TAG_KEY/TAG_VALUE \
  --parent=//cloudresourcemanager.googleapis.com/projects/sandbox-k8s-as-lego \
  --location=global
```

Then grant public read on the **static** bucket only:

```bash
gcloud storage buckets add-iam-policy-binding gs://sandbox-k8s-as-lego-qless-cafe-static \
  --member=allUsers --role=roles/storage.objectViewer
```

The SPA's JS bundle is fetched cross-origin (the app is served from
`qless-cafe.example.com`, its static assets from
`storage.googleapis.com`), so the static bucket also needs CORS or the
browser silently refuses to execute the module and the page renders blank:

```bash
cat > /tmp/gcs-static-cors.json <<'EOF'
[{"origin": ["https://qless-cafe.example.com"], "method": ["GET", "HEAD"],
  "responseHeader": ["Content-Type"], "maxAgeSeconds": 3600}]
EOF
gcloud storage buckets update gs://sandbox-k8s-as-lego-qless-cafe-static --cors-file=/tmp/gcs-static-cors.json
```

## 6 — Workload Identity for the django Pods only

The node service account (step 2) has no storage permissions at all. Only the
`django` Deployment gets GCS access (celery-worker/celery-beat/migrate never
touch storage), via a dedicated GSA impersonated through
[Workload Identity](https://cloud.google.com/kubernetes-engine/docs/how-to/workload-identity) —
no downloaded JSON key anywhere, and no project-level roles at all:

```bash
gcloud iam service-accounts create qless-cafe-django \
  --project=sandbox-k8s-as-lego --display-name="QLess Cafe Django Workload Identity SA"

for bucket in static media; do
  gcloud storage buckets add-iam-policy-binding \
    gs://sandbox-k8s-as-lego-qless-cafe-$bucket \
    --member="serviceAccount:qless-cafe-django@sandbox-k8s-as-lego.iam.gserviceaccount.com" \
    --role=roles/storage.objectAdmin
done

gcloud iam service-accounts add-iam-policy-binding \
  qless-cafe-django@sandbox-k8s-as-lego.iam.gserviceaccount.com \
  --project=sandbox-k8s-as-lego --role=roles/iam.workloadIdentityUser \
  --member="serviceAccount:sandbox-k8s-as-lego.svc.id.goog[qless-cafe/qless-cafe-django]"
```

[overlays/prod/serviceaccount.yaml](overlays/prod/serviceaccount.yaml) creates
the matching Kubernetes ServiceAccount (`qless-cafe/qless-cafe-django`) with
the `iam.gke.io/gcp-service-account` annotation that ties the two together;
the overlay's `kustomization.yaml` patches only `django`'s `serviceAccountName`
to use it.

## 7 — Secrets, then deploy

Run from the repo root:

```bash
cp k8s/overlays/prod/secrets.env.example k8s/overlays/prod/secrets.env
python3 -c "import secrets; print(secrets.token_urlsafe(50))"   # -> DJANGO_SECRET_KEY
# edit k8s/overlays/prod/secrets.env: DJANGO_SECRET_KEY, POSTGRES_PASSWORD,
# and DJANGO_ADMIN_URL (obscures /admin/ behind a random path — never commit this file)

cd k8s/overlays/prod && kustomize edit set image qless-cafe="$IMAGE:$TAG"; cd - || true
kubectl apply -k k8s/overlays/prod
kubectl -n qless-cafe rollout status deployment/django
```

This creates the Namespace, ConfigMap/Secret, the `postgres` StatefulSet with
its PVC (`standard-rwo`, GKE's default Persistent Disk class), `redis`, the
`django`/`celery-worker`/`celery-beat` Deployments, and a one-shot `migrate`
Job — running [`config.settings.production`](../config/settings/production.py)
(see [base/configmap.yaml](base/configmap.yaml)).

`migrate` is a plain `batch/v1` Job with a static name, and a Job's
`spec.template` is immutable once created — re-applying after a rebuild fails
with `field is immutable` if a completed `migrate` Job from a previous deploy
is still around. Delete it first if that happens (harmless — it already ran):

```bash
kubectl -n qless-cafe delete job migrate --ignore-not-found
```

Seed it once `django` is `Running`:

```bash
kubectl -n qless-cafe exec deploy/django -- uv run manage.py seed_demo_data
```

## 8 — HTTPS: static IP, DNS, and a Google-managed certificate

[overlays/prod/ingress.yaml](overlays/prod/ingress.yaml) is a GCE-class
Ingress (GKE's built-in controller — no ingress-nginx/cert-manager to install)
bound to the static IP from step 1, a
[ManagedCertificate](overlays/prod/managedcertificate.yaml) for the real
domain, and a [FrontendConfig](overlays/prod/frontendconfig.yaml) that
redirects HTTP → HTTPS at the load balancer — this is what makes the app
HTTPS-only, not just HTTPS-available.

Point your domain's DNS **A record** at the reserved static IP
(`gcloud compute addresses describe qless-cafe-ip --global --format='value(address)'`).
The `ManagedCertificate` only goes `Active` after that DNS record resolves and
propagates — check with:

```bash
kubectl -n qless-cafe describe managedcertificate qless-cafe-cert
```

This can take anywhere from a few minutes to about an hour. Once it's
`Active`:

```bash
curl -I https://qless-cafe.example.com/           # 200
curl https://qless-cafe.example.com/healthcheck/  # {"status": "ok"}
curl -I http://qless-cafe.example.com/            # 301 -> https
```

## A gotcha worth knowing: health checks vs. `SECURE_SSL_REDIRECT`

kubelet's probes and the GCE load balancer's health check both talk to the
Pod **directly** over plain HTTP — they never go through the HTTPS load
balancer, so they never send `X-Forwarded-Proto`. With
`SECURE_SSL_REDIRECT=True` (the correct, secure default for real traffic),
that means every health check gets a 301 back instead of a 200, and the
Deployment/Ingress backend never goes healthy.

The fix is **not** to turn `SECURE_SSL_REDIRECT` off — that would stop
enforcing HTTPS for real users too. Django has a purpose-built setting for
exactly this:
[`SECURE_REDIRECT_EXEMPT`](https://docs.djangoproject.com/en/dev/ref/settings/#secure-redirect-exempt).
[../config/views.py](../config/views.py) adds a dependency-free
`/healthcheck/` endpoint (no DB/Redis — a liveness probe shouldn't
cascade-fail when a downstream service blips), and
[../config/settings/production.py](../config/settings/production.py) exempts
only that one path:

```python
SECURE_REDIRECT_EXEMPT = [r"^healthcheck/$"]
```

[base/django-deployment.yaml](base/django-deployment.yaml)'s probes and
[base/django-backendconfig.yaml](base/django-backendconfig.yaml)'s
`requestPath` both point at `/healthcheck/` accordingly — every other URL
still gets redirected to HTTPS.

Note that `django-backendconfig.yaml` only sets `healthCheck.timeoutSec` (the
probe response timeout), not the backend service's own `spec.timeoutSec` —
GCLB's default of 30 seconds applies, which can close an idle
`/ws/notifications/` WebSocket connection if nothing is sent for 30s+. Add an
explicit `spec.timeoutSec` (e.g. `3600`) to that BackendConfig if long-idle
WebSocket connections matter for your demo.

```bash
kubectl delete -k k8s/overlays/prod   # tear the whole demo down when you're done, run from repo root
```
