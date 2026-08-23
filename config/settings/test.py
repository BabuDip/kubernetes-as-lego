"""
With these settings, tests run faster.
"""

from .base import *  # noqa: F403
from .base import DATABASES
from .base import TEMPLATES
from .base import env

# GENERAL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#secret-key
SECRET_KEY = env(
    "DJANGO_SECRET_KEY",
    default="fSJtPypM1dohxv89LDagQZPtRV3k6mRvyFsS8iRTtI6x4eG5AD14AKViBhEJKpZU",
)
# https://docs.djangoproject.com/en/dev/ref/settings/#test-runner
TEST_RUNNER = "django.test.runner.DiscoverRunner"

# PASSWORDS
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#password-hashers
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# EMAIL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#email-backend
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# DEBUGGING FOR TEMPLATES
# ------------------------------------------------------------------------------
TEMPLATES[0]["OPTIONS"]["debug"] = True  # type: ignore[index]

# MEDIA
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#media-url
MEDIA_URL = "http://media.testserver/"
# CHANNEL LAYERS
# ------------------------------------------------------------------------------
# In-memory layer: no live Redis dependency in tests, and it's fast.
CHANNEL_LAYERS = {"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}}
# CELERY
# ------------------------------------------------------------------------------
# Bare local pytest (SQLite, no Redis running) has no broker for an unmocked
# `.delay()` (e.g. via transaction.on_commit) to connect to — run those tasks
# inline instead. The Dockerized suite has a real Redis broker available, so it
# keeps dispatching for real, unchanged. Either way, tests that specifically
# exercise real dispatch use the `celery_session_worker` fixture, which runs on
# its own in-memory-broker app regardless of this setting.
if DATABASES["default"]["ENGINE"] == "django.db.backends.sqlite3":
    CELERY_TASK_ALWAYS_EAGER = True
# Your stuff...
# ------------------------------------------------------------------------------
