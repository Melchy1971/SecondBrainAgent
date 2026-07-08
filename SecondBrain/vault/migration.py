"""Migrate existing plaintext secrets into the vault.

Sources:
- ``config/secrets.local.yaml`` (legacy ``secondbrain.secrets`` store)
- ``.env`` entries whose key looks like a secret (``*_KEY``, ``*_TOKEN``,
  ``*_SECRET``, ``*PASSWORD*``, or a known provider key)

The migration writes each value into the vault and returns a report mapping the
original location to a ``secret://`` reference. Values are never logged. With
``rewrite_env=True`` the ``.env`` value is replaced by its reference and a
timestamped backup of the original ``.env`` is kept.
"""

from __future__ import annotations

import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from secondbrain.secrets import load_secrets
from secondbrain.vault.store import SecretVault

_SECRET_KEY_RE = re.compile(r"(_KEY|_TOKEN|_SECRET|PASSWORD|PASSWD|_APIKEY)$", re.IGNORECASE)
_KNOWN_KEYS = {"OPENAI_API_KEY", "GEMINI_API_KEY", "GOOGLE_API_KEY", "ANTHROPIC_API_KEY", "GITHUB_TOKEN"}


def _looks_secret(key: str) -> bool:
    return key in _KNOWN_KEYS or bool(_SECRET_KEY_RE.search(key))


def migrate_yaml_secrets(vault: SecretVault, project_root: str | Path, *, workspace: str = "default") -> list[dict[str, str]]:
    migrated: list[dict[str, str]] = []
    data = load_secrets(Path(project_root))
    for group, kv in data.items():
        if not isinstance(kv, dict):
            continue
        for key, value in kv.items():
            if not value:
                continue
            name = f"{group}.{key}"
            ref = vault.put_secret(name, str(value), workspace=workspace, meta={"origin": "secrets.local.yaml", "group": group})
            migrated.append({"source": f"yaml:{group}.{key}", "reference": ref})
    return migrated


def migrate_env_secrets(
    vault: SecretVault,
    project_root: str | Path,
    *,
    workspace: str = "default",
    rewrite_env: bool = False,
) -> list[dict[str, str]]:
    env_path = Path(project_root) / ".env"
    if not env_path.exists():
        return []
    migrated: list[dict[str, str]] = []
    lines = env_path.read_text(encoding="utf-8", errors="ignore").splitlines()
    new_lines: list[str] = []
    changed = False
    for raw in lines:
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            new_lines.append(raw)
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"\'')
        if value and _looks_secret(key) and not value.startswith("secret://"):
            ref = vault.put_secret(key, value, workspace=workspace, meta={"origin": ".env"})
            migrated.append({"source": f"env:{key}", "reference": ref})
            if rewrite_env:
                new_lines.append(f"{key}={ref}")
                changed = True
            else:
                new_lines.append(raw)
        else:
            new_lines.append(raw)
    if rewrite_env and changed:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        shutil.copy2(env_path, env_path.parent / f".env.bak-{stamp}")
        env_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
    return migrated


def migrate_all(
    vault: SecretVault,
    project_root: str | Path,
    *,
    workspace: str = "default",
    rewrite_env: bool = False,
) -> dict[str, Any]:
    yaml_migrated = migrate_yaml_secrets(vault, project_root, workspace=workspace)
    env_migrated = migrate_env_secrets(vault, project_root, workspace=workspace, rewrite_env=rewrite_env)
    return {
        "schema": "secondbrain.vault.migration.v1",
        "workspace": workspace,
        "migrated": yaml_migrated + env_migrated,
        "count": len(yaml_migrated) + len(env_migrated),
        "env_rewritten": rewrite_env,
    }
