"""Kopf operator: provisions an isolated QLess Cafe tenant per CafeTenant CR.

The business problem this solves (and why no existing tool does it): running
one shared instance per *cafe* isn't good multi-tenant isolation, but hand-
running `helm install` + secret generation + demo-data seeding per new
customer doesn't scale past a handful of tenants either. This closes that
gap: create a CafeTenant object, get a fully provisioned namespace back.
"""

from __future__ import annotations

import logging
import os
import secrets
import subprocess
import tempfile
from pathlib import Path
from typing import Any

import kopf
import yaml
from kubernetes import client
from kubernetes import config as k8s_config

CHART_PATH = Path(os.environ.get("QLESS_CAFE_CHART_PATH", "/chart"))
IMAGE_REPOSITORY = os.environ.get("QLESS_CAFE_IMAGE_REPOSITORY", "qless-cafe")

# starter/growth sizing presets — see the CRD schema's spec.plan description.
PLAN_SIZES = {
    "starter": {"django": 1, "celery_worker": 1},
    "growth": {"django": 2, "celery_worker": 2},
}


def release_name(tenant_name: str) -> str:
    return f"cafe-{tenant_name}"


def tenant_namespace(tenant_name: str) -> str:
    return f"cafe-{tenant_name}"


def run_helm(*args: str) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["helm", *args], capture_output=True, text=True, check=False
    )
    if result.returncode != 0:
        raise kopf.PermanentError(
            f"helm {' '.join(args)} failed: {result.stderr.strip()}"
        )
    return result


def existing_tenant_secrets(release: str, namespace: str) -> dict[str, Any] | None:
    """Reuse a previously-generated Secret block, if this release already exists.

    Without this, `on.update` (e.g. bumping imageTag) would regenerate
    djangoSecretKey/postgresPassword on every reconcile — Postgres already
    has the old password initialized, so a rotated Secret would silently
    break the tenant instead of updating it.
    """
    result = subprocess.run(
        ["helm", "get", "values", release, "--namespace", namespace, "-o", "yaml"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return None
    return (yaml.safe_load(result.stdout) or {}).get("secrets")


def build_values(spec: dict[str, Any], tenant_name: str) -> dict[str, Any]:
    """Translate a CafeTenant spec into k8s/helm-charts values."""
    sizing = PLAN_SIZES[spec.get("plan", "starter")]
    release, namespace = release_name(tenant_name), tenant_namespace(tenant_name)
    tenant_secrets = existing_tenant_secrets(release, namespace) or {
        "djangoSecretKey": secrets.token_urlsafe(50),
        "postgresUser": "qless_cafe",
        "postgresPassword": secrets.token_urlsafe(24),
    }
    return {
        "environment": f"tenant-{tenant_name}",
        "ingress": {"enabled": False},
        "gke": {"enabled": False},
        "image": {
            "repository": IMAGE_REPOSITORY,
            "tag": spec["imageTag"],
            "pullPolicy": "IfNotPresent",
        },
        "django": {"replicaCount": sizing["django"], "healthCheckHost": "localhost"},
        "celeryWorker": {"replicaCount": sizing["celery_worker"]},
        "postgres": {"storageClassName": spec.get("storageClassName", "standard")},
        "config": {"allowedHosts": "localhost,127.0.0.1"},
        "secrets": tenant_secrets,
    }


def apply_release(
    spec: dict[str, Any], tenant_name: str, logger: Any
) -> tuple[str, str]:
    namespace, release = tenant_namespace(tenant_name), release_name(tenant_name)
    values = build_values(spec, tenant_name)

    with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as handle:
        yaml.safe_dump(values, handle)
        values_path = handle.name
    try:
        logger.info("helm upgrade --install %s (namespace=%s)", release, namespace)
        run_helm(
            "upgrade",
            "--install",
            release,
            str(CHART_PATH),
            "--namespace",
            namespace,
            "--create-namespace",
            "-f",
            values_path,
            "--timeout",
            "3m",
        )
    finally:
        Path(values_path).unlink(missing_ok=True)
    return namespace, release


def seed_demo_data_job(namespace: str, image_tag: str) -> client.V1Job:
    container = client.V1Container(
        name="seed-demo-data",
        image=f"{IMAGE_REPOSITORY}:{image_tag}",
        args=["python", "/app/manage.py", "seed_demo_data"],
        env_from=[
            client.V1EnvFromSource(
                config_map_ref=client.V1ConfigMapEnvSource(name="qless-cafe-config")
            ),
            client.V1EnvFromSource(
                secret_ref=client.V1SecretEnvSource(name="qless-cafe-secrets")
            ),
        ],
    )
    template = client.V1PodTemplateSpec(
        metadata=client.V1ObjectMeta(labels={"app": "seed-demo-data"}),
        spec=client.V1PodSpec(restart_policy="Never", containers=[container]),
    )
    return client.V1Job(
        metadata=client.V1ObjectMeta(name="seed-demo-data", namespace=namespace),
        spec=client.V1JobSpec(
            template=template, backoff_limit=1, ttl_seconds_after_finished=300
        ),
    )


@kopf.on.startup()
def configure(settings: kopf.OperatorSettings, **_: Any) -> None:
    # In-cluster config when running as the Deployment; local kubeconfig when
    # running via `kopf run` for development — see README.md.
    try:
        k8s_config.load_incluster_config()
    except k8s_config.ConfigException:
        k8s_config.load_kube_config()
    settings.posting.level = logging.INFO


@kopf.on.create("platform.qless.cafe", "v1alpha1", "cafetenants")
def on_create(
    spec: dict[str, Any], name: str, patch: kopf.Patch, logger: Any, **_: Any
) -> None:
    namespace, release = apply_release(spec, name, logger)
    patch.status["phase"] = "Provisioning"
    patch.status["namespace"] = namespace
    patch.status["releaseName"] = release
    patch.status["message"] = "Helm release installed; waiting for rollout."


@kopf.on.update("platform.qless.cafe", "v1alpha1", "cafetenants")
def on_update(
    spec: dict[str, Any], name: str, patch: kopf.Patch, logger: Any, **_: Any
) -> None:
    apply_release(spec, name, logger)
    patch.status["phase"] = "Provisioning"
    patch.status["message"] = "Helm release upgraded; waiting for rollout."


@kopf.on.delete("platform.qless.cafe", "v1alpha1", "cafetenants")
def on_delete(name: str, logger: Any, **_: Any) -> None:
    namespace, release = tenant_namespace(name), release_name(name)
    logger.info("helm uninstall %s (namespace=%s)", release, namespace)
    subprocess.run(
        ["helm", "uninstall", release, "--namespace", namespace],
        capture_output=True,
        text=True,
        check=False,
    )
    try:
        client.CoreV1Api().delete_namespace(namespace)
    except client.ApiException as exc:
        if exc.status != 404:
            raise kopf.PermanentError(
                f"failed to delete namespace {namespace}: {exc.reason}"
            ) from exc


@kopf.timer(
    "platform.qless.cafe", "v1alpha1", "cafetenants", interval=30, initial_delay=15
)
def check_readiness(
    spec: dict[str, Any],
    status: dict[str, Any],
    name: str,
    patch: kopf.Patch,
    logger: Any,
    **_: Any,
) -> None:
    """Reconciliation loop: reflect the tenant's actual rollout state, and
    fire the one-off demo-data seed job once (and only once) it's Ready.
    """
    namespace = tenant_namespace(name)
    apps_v1 = client.AppsV1Api()
    try:
        deployment = apps_v1.read_namespaced_deployment("django", namespace)
    except client.ApiException as exc:
        if exc.status == 404:
            return  # helm hasn't created it yet
        raise

    wanted = deployment.spec.replicas or 1
    got = deployment.status.ready_replicas or 0
    ready = got >= wanted
    patch.status["phase"] = "Ready" if ready else "Provisioning"
    patch.status["message"] = (
        "django Deployment is Ready."
        if ready
        else f"Waiting for django rollout ({got}/{wanted} ready)."
    )

    if ready and spec.get("seedDemoData") and not status.get("seeded"):
        try:
            client.BatchV1Api().create_namespaced_job(
                namespace, seed_demo_data_job(namespace, spec["imageTag"])
            )
            logger.info("Created seed-demo-data Job in %s", namespace)
        except client.ApiException as exc:
            if exc.status != 409:  # already exists — fine, don't crash the timer
                raise
        patch.status["seeded"] = True
