# ruff: noqa: E501
from .base import *  # noqa: F403
from .base import DATABASES
from .base import INSTALLED_APPS
from .base import REDIS_URL
from .base import env

# GENERAL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#secret-key
SECRET_KEY = env("DJANGO_SECRET_KEY")
# https://docs.djangoproject.com/en/dev/ref/settings/#allowed-hosts
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["qless.cafe"])

# DATABASES
# ------------------------------------------------------------------------------
DATABASES["default"]["CONN_MAX_AGE"] = env.int("CONN_MAX_AGE", default=60)

# CACHES
# ------------------------------------------------------------------------------
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_URL,
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            # Mimicking memcache behavior.
            # https://github.com/jazzband/django-redis#memcached-exceptions-behavior
            "IGNORE_EXCEPTIONS": True,
        },
    },
}

# SECURITY
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#secure-proxy-ssl-header
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
# https://docs.djangoproject.com/en/dev/ref/settings/#secure-ssl-redirect
SECURE_SSL_REDIRECT = env.bool("DJANGO_SECURE_SSL_REDIRECT", default=True)
# https://docs.djangoproject.com/en/dev/ref/settings/#secure-redirect-exempt
# kubelet's probes and the GCE load balancer's health check (see
# k8s/base/django-backendconfig.yaml) hit /healthcheck/ on the Pod directly
# over plain HTTP and never send X-Forwarded-Proto, so without this narrow,
# explicit exemption they'd be 301/302'd and marked permanently unhealthy.
# Every other URL still gets the redirect — this does not weaken transport
# security for real traffic.
SECURE_REDIRECT_EXEMPT = [r"^healthcheck/$"]
# https://docs.djangoproject.com/en/dev/ref/settings/#session-cookie-secure
SESSION_COOKIE_SECURE = True
# https://docs.djangoproject.com/en/dev/ref/settings/#session-cookie-name
SESSION_COOKIE_NAME = "__Secure-sessionid"
# https://docs.djangoproject.com/en/dev/ref/settings/#csrf-cookie-secure
CSRF_COOKIE_SECURE = True
# https://docs.djangoproject.com/en/dev/ref/settings/#csrf-cookie-name
CSRF_COOKIE_NAME = "__Secure-csrftoken"
# https://docs.djangoproject.com/en/dev/topics/security/#ssl-https
# https://docs.djangoproject.com/en/dev/ref/settings/#secure-hsts-seconds
# TODO: set this to 60 seconds first and then to 518400 once you prove the former works
SECURE_HSTS_SECONDS = 60
# https://docs.djangoproject.com/en/dev/ref/settings/#secure-hsts-include-subdomains
SECURE_HSTS_INCLUDE_SUBDOMAINS = env.bool(
    "DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS",
    default=True,
)
# https://docs.djangoproject.com/en/dev/ref/settings/#secure-hsts-preload
SECURE_HSTS_PRELOAD = env.bool("DJANGO_SECURE_HSTS_PRELOAD", default=True)
# https://docs.djangoproject.com/en/dev/ref/middleware/#x-content-type-options-nosniff
SECURE_CONTENT_TYPE_NOSNIFF = env.bool(
    "DJANGO_SECURE_CONTENT_TYPE_NOSNIFF",
    default=True,
)


# Two buckets, not one: our org's `iam.managed.allowedPolicyMembers` policy
# blocks `allUsers`/`allAuthenticatedUsers` IAM bindings by default, so a
# single bucket can't mix a public STATIC_URL with private media. Static
# assets are content-hashed and non-sensitive -> public bucket, stable URL.
# Media (user/staff-uploaded product photos) stays private -> every
# FileField.url is a short-lived v4 signed URL instead of a fixed prefix.
# https://django-storages.readthedocs.io/en/latest/backends/gcloud.html
GS_STATIC_BUCKET_NAME = env("DJANGO_GCP_STATIC_BUCKET_NAME")
GS_MEDIA_BUCKET_NAME = env("DJANGO_GCP_MEDIA_BUCKET_NAME")
STORAGES = {
    "default": {
        "BACKEND": "storages.backends.gcloud.GoogleCloudStorage",
        "OPTIONS": {
            "bucket_name": GS_MEDIA_BUCKET_NAME,
            "location": "media",
            "file_overwrite": False,
            "querystring_auth": True,
        },
    },
    "staticfiles": {
        "BACKEND": "storages.backends.gcloud.GoogleCloudStorage",
        "OPTIONS": {
            "bucket_name": GS_STATIC_BUCKET_NAME,
            "location": "static",
            "querystring_auth": False,
            # Filenames aren't content-hashed (plain GoogleCloudStorage, not
            # ManifestStaticFilesStorage), so the same URL is reused across
            # deploys — without this, GCS's own default Cache-Control
            # (public, max-age=3600) plus browser caching serves a stale
            # bundle for up to an hour after every rollout.
            # https://django-storages.readthedocs.io/en/latest/backends/gcloud.html
            "object_parameters": {
                "cache_control": "no-cache, max-age=0, must-revalidate",
            },
        },
    },
}
# No MEDIA_URL override here on purpose: leaving it unset means every
# ImageField/FileField.url() call goes through GoogleCloudStorage.url(),
# which mints a signed URL against GS_MEDIA_BUCKET_NAME on demand.
COLLECTFASTA_STRATEGY = "collectfasta.strategies.gcloud.GoogleCloudStrategy"
STATIC_URL = f"https://storage.googleapis.com/{GS_STATIC_BUCKET_NAME}/static/"

# EMAIL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#default-from-email
DEFAULT_FROM_EMAIL = env(
    "DJANGO_DEFAULT_FROM_EMAIL",
    default="QLess Cafe <noreply@qless.cafe>",
)
# https://docs.djangoproject.com/en/dev/ref/settings/#server-email
SERVER_EMAIL = env("DJANGO_SERVER_EMAIL", default=DEFAULT_FROM_EMAIL)
# https://docs.djangoproject.com/en/dev/ref/settings/#email-subject-prefix
EMAIL_SUBJECT_PREFIX = env(
    "DJANGO_EMAIL_SUBJECT_PREFIX",
    default="[QLess Cafe] ",
)

# ADMIN
# ------------------------------------------------------------------------------
# Django Admin URL regex.
ADMIN_URL = env("DJANGO_ADMIN_URL")

# Collectfasta
# ------------------------------------------------------------------------------
# https://github.com/jasongi/collectfasta#installation
INSTALLED_APPS = ["collectfasta", *INSTALLED_APPS]

# LOGGING
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#logging
# See https://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {"require_debug_false": {"()": "django.utils.log.RequireDebugFalse"}},
    "formatters": {
        "verbose": {
            "format": "%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s",
        },
    },
    "handlers": {
        "mail_admins": {
            "level": "ERROR",
            "filters": ["require_debug_false"],
            "class": "django.utils.log.AdminEmailHandler",
        },
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {"level": "INFO", "handlers": ["console"]},
    "loggers": {
        "django.request": {
            "handlers": ["mail_admins"],
            "level": "ERROR",
            "propagate": True,
        },
        "django.security.DisallowedHost": {
            "level": "ERROR",
            "handlers": ["console", "mail_admins"],
            "propagate": True,
        },
    },
}


# Your stuff...
# ------------------------------------------------------------------------------
