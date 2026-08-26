# Every Docker image boils down to 4 steps: get a base image, install your
# dependencies, copy in your source code, then declare how to run it.
# This is the minimal image used in the README's Step 2 (containerize) — the
# production image (compose/production/django/Dockerfile) does more, but the
# same 4 steps are still in there.

# 1. BASE IMAGE — a Python version matching pyproject.toml's requires-python.
#    "slim" keeps the image small; WORKDIR sets where the next steps run from.
FROM python:3.14-slim-bookworm
WORKDIR /app

# 2. INSTALL DEPENDENCIES — done before copying the app code so Docker can
#    cache this (slow) layer and skip it on rebuilds where only source changed.
#      a) uv: the package manager this project uses (see uv.lock)
#      b) build-essential/libpq-dev: system libraries uv needs to compile
#         psycopg, the Postgres driver
#      c) uv sync: installs the exact versions pinned in uv.lock
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
RUN apt-get update && apt-get install --no-install-recommends -y build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*
COPY pyproject.toml uv.lock* ./
RUN uv sync --frozen --no-install-project

# 3. COPY SOURCE CODE — last, since it changes the most often.
COPY . .

# 4. RUN THE APPLICATION — the port the app listens on, and the command
#    that starts it when a container is run from this image.
#    PYTHONUNBUFFERED so `docker logs`/`kubectl logs` show output immediately.
ENV PYTHONUNBUFFERED=1
EXPOSE 8000
CMD ["uv", "run", "manage.py", "runserver", "0.0.0.0:8000"]
