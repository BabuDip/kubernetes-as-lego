# Built from the repo root: docker build -f k8s/operators/cafe-tenant-operator/Dockerfile .
# (needs repo-root context to bake in ../../helm-charts below).
FROM python:3.14-slim-bookworm
WORKDIR /app

# helm itself — the operator shells out to it (see operator/handlers.py's
# run_helm()) to install/upgrade/uninstall each tenant's release. Checksums
# below are the published amd64/arm64 sha256sums for this exact version
# (https://get.helm.sh/helm-${HELM_VERSION}-linux-<arch>.tar.gz.sha256sum) —
# verified before extracting so a compromised CDN/MITM can't swap in a
# malicious binary that the operator would then trust and execute.
ARG HELM_VERSION=v3.16.4
ARG HELM_SHA256_AMD64=fc307327959aa38ed8f9f7e66d45492bb022a66c3e5da6063958254b9767d179
ARG HELM_SHA256_ARM64=d3f8f15b3d9ec8c8678fbf3280c3e5902efabe5912e2f9fcf29107efbc8ead69
RUN apt-get update && apt-get install --no-install-recommends -y curl ca-certificates \
  && arch="$(dpkg --print-architecture)" \
  && case "$arch" in \
       amd64) expected="$HELM_SHA256_AMD64" ;; \
       arm64) expected="$HELM_SHA256_ARM64" ;; \
       *) echo "unsupported architecture: $arch" >&2; exit 1 ;; \
     esac \
  && curl -fsSL "https://get.helm.sh/helm-${HELM_VERSION}-linux-${arch}.tar.gz" -o /tmp/helm.tar.gz \
  && echo "${expected}  /tmp/helm.tar.gz" | sha256sum -c - \
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
