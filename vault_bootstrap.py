from __future__ import annotations

import os


def _is_enabled(value: str | None) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def bootstrap_secrets_from_vault() -> None:
    if not _is_enabled(os.getenv("ENABLE_VAULT_BOOTSTRAP")):
        return

    vault_addr = os.getenv("VAULT_ADDR")
    vault_token = os.getenv("VAULT_TOKEN")
    vault_secret_path = os.getenv("VAULT_SECRET_PATH", "green-cloud-guardian")
    vault_mount_point = os.getenv("VAULT_KV_MOUNT", "secret")

    if not vault_addr or not vault_token:
        return

    try:
        import hvac
    except ImportError:
        return

    try:
        client = hvac.Client(url=vault_addr, token=vault_token)
        if not client.is_authenticated():
            return

        secret = client.secrets.kv.v2.read_secret_version(
            mount_point=vault_mount_point,
            path=vault_secret_path,
        )
        secret_data = secret.get("data", {}).get("data", {})

        for key in ("JWT_SECRET", "ELECTRICITY_MAPS_API_KEY"):
            value = secret_data.get(key)
            if value:
                os.environ.setdefault(key, str(value))
    except Exception:
        return
