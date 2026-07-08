from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path

DEFAULT_VAULT_DIRNAME = "SecondBrain"
DEFAULT_INCOMING_DIRNAME = "SecondBrain-Inbox"
VAULT_SETTING_KEY = "paths.vault"
INCOMING_SETTING_KEY = "paths.incoming"

@dataclass(frozen=True)
class AppPaths:
    vault: Path
    incoming: Path
    def to_dict(self) -> dict:
        return {"vault_path": str(self.vault), "incoming_path": str(self.incoming)}

def _resolve(value, project_root: Path, default_name: str) -> Path:
    if value and str(value).strip():
        p = Path(str(value)).expanduser()
        return p if p.is_absolute() else (project_root / p)
    return project_root / default_name

def resolve_paths(project_root, *, vault_setting="", incoming_setting="") -> AppPaths:
    root = Path(project_root)
    return AppPaths(_resolve(vault_setting, root, DEFAULT_VAULT_DIRNAME),
                    _resolve(incoming_setting, root, DEFAULT_INCOMING_DIRNAME))

def from_settings_service(service, project_root) -> AppPaths:
    def _get(k):
        try: return service.get(k) or ""
        except Exception: return ""
    return resolve_paths(project_root, vault_setting=_get(VAULT_SETTING_KEY),
                         incoming_setting=_get(INCOMING_SETTING_KEY))

def ensure_dirs(paths: AppPaths) -> AppPaths:
    paths.vault.mkdir(parents=True, exist_ok=True)
    paths.incoming.mkdir(parents=True, exist_ok=True)
    return paths