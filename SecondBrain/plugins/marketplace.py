"""Offline marketplace metadata preparation; installation is intentionally out of scope."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from secondbrain.plugins.models import PluginManifest


@dataclass(frozen=True, slots=True)
class MarketplaceEntry:
    plugin_id: str
    name: str
    version: str
    description: str
    publisher: str
    license: str
    homepage: str
    tags: tuple[str, ...]
    package_url: str
    sha256: str
    ready: bool
    issues: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "plugin_id": self.plugin_id, "name": self.name, "version": self.version,
            "description": self.description, "publisher": self.publisher, "license": self.license,
            "homepage": self.homepage, "tags": list(self.tags), "package_url": self.package_url,
            "sha256": self.sha256, "ready": self.ready, "issues": list(self.issues),
        }


class PluginMarketplace:
    SCHEMA = "secondbrain.plugin_marketplace.v30_76"

    def prepare(self, manifests: Iterable[PluginManifest]) -> dict[str, Any]:
        entries = [self.entry(manifest) for manifest in manifests]
        return {
            "schema": self.SCHEMA,
            "mode": "metadata_only",
            "install_supported": False,
            "count": len(entries),
            "ready": sum(1 for entry in entries if entry.ready),
            "plugins": [entry.to_dict() for entry in sorted(entries, key=lambda row: row.plugin_id)],
        }

    def entry(self, manifest: PluginManifest) -> MarketplaceEntry:
        data = dict(manifest.marketplace)
        values = {
            "publisher": str(data.get("publisher") or "").strip(),
            "license": str(data.get("license") or "").strip(),
            "homepage": str(data.get("homepage") or "").strip(),
            "package_url": str(data.get("package_url") or "").strip(),
            "sha256": str(data.get("sha256") or "").strip().lower(),
        }
        issues = [f"missing_{key}" for key in ("publisher", "license", "homepage") if not values[key]]
        raw_tags = data.get("tags") or ()
        if not isinstance(raw_tags, (list, tuple)):
            issues.append("invalid_tags")
            raw_tags = ()
        if values["package_url"] and not re.fullmatch(r"[a-f0-9]{64}", values["sha256"]):
            issues.append("package_checksum_required")
        return MarketplaceEntry(
            manifest.id, manifest.name, manifest.version, manifest.description,
            values["publisher"], values["license"], values["homepage"],
            tuple(str(item) for item in raw_tags), values["package_url"], values["sha256"],
            not issues, tuple(issues),
        )

    def export(self, catalog: dict[str, Any], path: str | Path) -> Path:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(catalog, indent=2, ensure_ascii=False), encoding="utf-8")
        return target
