# 1. Base image: Python 3.14, "slim" variant to keep the image small
FROM python:3.14-slim-bookworm

# 2. Grab the uv binary straight from its own image (faster than pip install uv)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# 3. build-essential + libpq-dev: needed to compile psycopg (Postgres driver)
RUN apt-get update && apt-get install --no-install-recommends -y build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 4. Sensible defaults for running Python in a container
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1

# 5. Everything below runs from /app inside the container
WORKDIR /app

# 6. Copy dependency files first so this layer is cached across rebuilds
COPY pyproject.toml uv.lock* ./
RUN uv sync --frozen --no-install-project

# 7. Copy the rest of the app code last (changes most often)
COPY . .

# 8. Document the port the app listens on (docker run -p still does the publishing)
EXPOSE 8000

# 9. Command that runs when the container starts
CMD ["uv", "run", "manage.py", "runserver", "0.0.0.0:8000"]
