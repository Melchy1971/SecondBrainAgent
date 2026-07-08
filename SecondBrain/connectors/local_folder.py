"""Local folder connector: incremental filesystem sync (mtime watermark).

Emits ConnectorItem for text-like files; integrates with IncrementalSyncRunner
and the ConnectorImportBridge like every other connector. No auth.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from secondbrain.connectors.incremental_runner import FetchBatch, FetchedItem
from secondbrain.connectors.adapter_contract import ConnectorItem

DEFAULT_EXTS = (".txt", ".md", ".markdown", ".rst", ".log", ".csv", ".json", ".yaml", ".yml", ".py")


class LocalFolderConnector:
    def __init__(self, root: str | Path, *, name: str = "local_folder",
                 extensions: tuple[str, ...] = DEFAULT_EXTS, max_bytes: int = 1_000_000) -> None:
        self.name = name
        self.root = Path(root)
        self.extensions = tuple(e.lower() for e in extensions)
        self.max_bytes = max_bytes

    def _iter_files(self):
        if not self.root.exists():
            return
        for p in sorted(self.root.rglob("*")):
            if p.is_file() and p.suffix.lower() in self.extensions:
                yield p

    def fetch_since(self, cursor: str | None, limit: int) -> FetchBatch:
        watermark = float(cursor) if cursor else 0.0
        newest = watermark
        items: list[FetchedItem] = []
        for path in self._iter_files():
            mtime = path.stat().st_mtime
            if mtime <= watermark:
                continue
            try:
                if path.stat().st_size > self.max_bytes:
                    content = f"(skipped: {path.stat().st_size} bytes > {self.max_bytes})"
                else:
                    content = path.read_text(encoding="utf-8", errors="replace")
            except Exception as exc:  # noqa: BLE001 - per-file isolation
                content = f"(read error: {exc})"
            rel = str(path.relative_to(self.root))
            item = ConnectorItem(
                external_id=rel, source=self.name, title=path.name, content=content or path.name,
                updated_at=datetime.fromtimestamp(mtime, tz=timezone.utc),
                uri=path.as_uri(),
                metadata={"size": path.stat().st_size, "ext": path.suffix.lower()})
            items.append(FetchedItem(id=rel, payload=item, cursor=str(mtime)))
            newest = max(newest, mtime)
            if len(items) >= limit:
                break
        return FetchBatch(items=items, next_cursor=str(newest) if newest > watermark else cursor, has_more=False)


def connector(root: str | Path, **kw) -> LocalFolderConnector:
    return LocalFolderConnector(root, **kw)
