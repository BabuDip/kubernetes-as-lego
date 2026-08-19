from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from qless_cafe.identity.tests.factories import UserFactory

if TYPE_CHECKING:
    from qless_cafe.identity.models import User


@pytest.fixture(autouse=True)
def _media_storage(settings, tmpdir) -> None:
    settings.MEDIA_ROOT = tmpdir.strpath


@pytest.fixture
def user(db) -> User:
    return UserFactory.create()


@pytest.fixture(scope="session")
def celery_config():
    """Real in-memory broker/backend — never task_always_eager, so tests exercise
    the actual queue → worker → task path instead of calling task functions directly."""
    return {
        "broker_url": "memory://",
        "result_backend": "cache+memory://",
        "task_always_eager": False,
        "task_store_eager_result": True,
    }


@pytest.fixture(scope="session")
def celery_includes():
    # celery.contrib.testing.tasks registers the "celery.ping" task the test
    # worker uses for its startup health check.
    return ["celery.contrib.testing.tasks", "qless_cafe.orders.tasks"]


@pytest.fixture(scope="session")
def celery_worker_parameters():
    return {"queues": ("celery",), "without_heartbeat": True}
