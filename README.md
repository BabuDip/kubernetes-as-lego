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

A Kubernetes cluster is a pool of machines (**nodes**) glued together by a
control plane. minikube simulates that whole cluster on your laptop, with
each "node" being a container (the `docker` driver, used below) or a VM.

### check your machine's Docker resources

```bash
docker info --format '{{.NCPU}} CPUs / {{.MemTotal}} bytes memory'
# 18 CPUs / 8319410176 bytes memory
```

### Start the cluster
Now based on the resource you got, start kubernetes with Minikube. 
```bash
minikube start --nodes=3 --cpus=6 --memory=2200mb --driver=docker

# 😄  minikube v1.38.1 on Darwin 26.6.2 (arm64)
# ✨  Using the docker driver based on user configuration
# ❗  Starting v1.39.0, minikube will default to "containerd" container runtime. See #21973 for more info.
# 📌  Using Docker Desktop driver with root privileges
# 👍  Starting "minikube" primary control-plane node in "minikube" cluster
# 🚜  Pulling base image v0.0.50 ...
# 🔥  Creating docker container (CPUs=6, Memory=2200MB) ...
# 🐳  Preparing Kubernetes v1.35.1 on Docker 29.2.1 ...
# 🔗  Configuring CNI (Container Networking Interface) ...
# 🔎  Verifying Kubernetes components...
#    ▪ Using image gcr.io/k8s-minikube/storage-provisioner:v5
# 🌟  Enabled addons: storage-provisioner, default-storageclass
#
# 👍  Starting "minikube-m02" worker node in "minikube" cluster
# 🚜  Pulling base image v0.0.50 ...
# 🔥  Creating docker container (CPUs=6, Memory=2200MB) ...
# 🌐  Found network options:
#     ▪ NO_PROXY=192.168.49.2
# 🐳  Preparing Kubernetes v1.35.1 on Docker 29.2.1 ...
#     ▪ env NO_PROXY=192.168.49.2
# 🔎  Verifying Kubernetes components...
# 
# 👍  Starting "minikube-m03" worker node in "minikube" cluster
# 🚜  Pulling base image v0.0.50 ...
# 🔥  Creating docker container (CPUs=6, Memory=2200MB) ...
# 🌐  Found network options:
#     ▪ NO_PROXY=192.168.49.2,192.168.49.3
# 🐳  Preparing Kubernetes v1.35.1 on Docker 29.2.1 ...
#    ▪ env NO_PROXY=192.168.49.2
#    ▪ env NO_PROXY=192.168.49.2,192.168.49.3
# 🔎  Verifying Kubernetes components...
# 🏄  Done! kubectl is now configured to use "minikube" cluster and "default" namespace by default
```

Check the nodes are up and running:
```bash
kubectl get nodes -o wide
# NAME           STATUS   ROLES           AGE     VERSION   INTERNAL-IP    EXTERNAL-IP   OS-IMAGE                KERNEL-VERSION     CONTAINER-RUNTIME
# minikube       Ready    control-plane   9m56s   v1.35.1   192.168.49.2   <none>        Debian GNU/Linux12 (bookworm)   6.12.76-linuxkit   docker://29.2.1
# minikube-m02   Ready    <none>          9m39s   v1.35.1   192.168.49.3   <none>        Debian GNU/Linux12 (bookworm)   6.12.76-linuxkit   docker://29.2.1
# minikube-m03   Ready    <none>          9m26s   v1.35.1   192.168.49.4   <none>        Debian GNU/Linux12 (bookworm)   6.12.76-linuxkit   docker://29.2.1
```

## Step 4 — Define and run your first Pod

A **Pod** is the smallest deployable unit in Kubernetes.

### Get the image into the cluster

The `docker` driver's nodes have their own separate image store, so the
`qless-cafe:v1` image built in Step 2 isn't visible to them yet:

```bash
minikube image load qless-cafe:v1
```

### Define the Pod

See [k8s/pod.yaml](k8s/pod.yaml) — one container running the same image and
command as Step 2's `docker run`, using SQLite (no `POSTGRES_*` env vars) so
it needs nothing else in the cluster to boot.

### Deploy it

```bash
kubectl apply -f k8s/pod.yaml
kubectl get pods -o wide      # STATUS should reach Running, NODE shows where it landed
```

Just like Step 2, the container needs migrating and seeding before it's
useful:

```bash
kubectl exec qless-cafe -- uv run manage.py migrate
kubectl exec qless-cafe -- uv run manage.py seed_demo_data
```

Then forward a local port to the Pod and visit it:

```bash
kubectl port-forward pod/qless-cafe 8000:8000
```

Now visit <http://localhost:8000/> — same app, same seeded credentials as
Step 1 and Step 2. `Ctrl+C` stops the port-forward (and, unlike Step 2's
`bash` shell, doesn't touch the Pod itself — it's still `Running` in the
cluster).

```bash
kubectl logs qless-cafe          # see the runserver output
kubectl delete -f k8s/pod.yaml   # tear the Pod down when you're done
```

---

## License

MIT — see [LICENSE](LICENSE).
