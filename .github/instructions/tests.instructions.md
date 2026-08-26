---
description: "Backend test conventions specific to QLess Cafe"
applyTo: "qless_cafe/**/tests/**/*.py"
---

# Python Test Instructions

- pytest + `pytest-django`. Run the exact command a human would (see
  `AGENTS.md`): `docker compose -f docker-compose.yaml run --rm django pytest`,
  or scope to one app with
  `docker compose -f docker-compose.yaml run --rm django pytest qless_cafe/<app>`.
- Tests are colocated per app: `qless_cafe/<app>/tests/test_*.py`, with
  shared `factory-boy` factories in `qless_cafe/<app>/tests/factories.py`.
- Follow the AAA pattern (Arrange, Act, Assert); write descriptive test
  names that describe the behavior under test, not the implementation.
- Use pytest-django's `mailoutbox` fixture for email assertions, not manual
  SMTP mocking.
- Celery tasks (e.g. `send_order_receipt_email`) must be exercised through a
  real dispatch using `celery.contrib.pytest`'s `celery_session_worker`
  fixture (configured in `qless_cafe/conftest.py`) — never call the task
  function directly and never rely on `task_always_eager`. Mark these tests
  `@pytest.mark.django_db(transaction=True)` since the worker runs on its own
  DB connection in a separate thread and needs to see committed data.
- Add or update tests whenever behavior changes — there's no separate
  coverage gate in CI beyond `pytest` passing, so don't skip tests for new
  logic just because nothing enforces it.
