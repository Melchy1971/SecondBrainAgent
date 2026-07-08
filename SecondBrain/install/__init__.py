"""Install-time helpers for the Windows package: AppData home resolution, local
data migration, and the post-install smoke test. Importable by the frozen
bootstrap and unit-testable without a display or admin rights.
"""

from secondbrain.install.app_home import (
    APP_NAME,
    DATA_SUBDIRS,
    ENV_HOME,
    ensure_layout,
    project_root,
    resolve_home,
)
from secondbrain.install.migrate import MIGRATE_DIRS, migrate_local_data
from secondbrain.install.smoke import run_smoke_test

__all__ = [
    "APP_NAME",
    "DATA_SUBDIRS",
    "ENV_HOME",
    "MIGRATE_DIRS",
    "ensure_layout",
    "migrate_local_data",
    "project_root",
    "resolve_home",
    "run_smoke_test",
]
