# Built from the repo root: docker build -f k8s/operators/cafe-tenant-operator/Dockerfile .
# (needs repo-root context to bake in ../../helm-charts below).
FROM python:3.14-slim-bookworm
WORKDIR /app

# helm itself — the operator shells out to it (see operator/handlers.py's
# run_helm()) to install/upgrade/uninstall each tenant's release.
ARG HELM_VERSION=v3.16.4
RUN apt-get update && apt-get install --no-install-recommends -y curl ca-certificates \
  && curl -fsSL "https://get.helm.sh/helm-${HELM_VERSION}-linux-$(dpkg --print-architecture).tar.gz" -o /tmp/helm.tar.gz \
  && tar -xzf /tmp/helm.tar.gz -C /tmp \
  && mv /tmp/linux-*/helm /usr/local/bin/helm \
  && rm -rf /tmp/helm.tar.gz /tmp/linux-* \
  && apt-get purge -y curl && apt-get autoremove -y && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
COPY k8s/operators/cafe-tenant-operator/pyproject.toml k8s/operators/cafe-tenant-operator/uv.lock ./
RUN uv sync --frozen --no-install-project

COPY k8s/operators/cafe-tenant-operator/operator ./operator
# The chart this operator installs per tenant, baked in so reconciling needs
# no registry access — a real deployment would instead `helm pull` the OCI
# chart Step 7 describes.
COPY k8s/helm-charts /chart

ENV PYTHONUNBUFFERED=1
CMD ["uv", "run", "kopf", "run", "--standalone", "operator/handlers.py"]
