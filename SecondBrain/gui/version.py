"""GUI adopts the single project version (see secondbrain.version)."""
from secondbrain.version import get_version, get_build_number, version_info

APP_VERSION = get_version()
APP_BUILD = get_build_number()


def gui_version_info() -> dict:
    return {"component": "gui", **version_info()}
