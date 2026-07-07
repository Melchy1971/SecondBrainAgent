"""CLI adopts the single project version (see secondbrain.version)."""
from secondbrain.version import get_version, get_build_number, version_info

CLI_VERSION = get_version()
CLI_BUILD = get_build_number()


def cli_version_info() -> dict:
    return {"component": "cli", **version_info()}
