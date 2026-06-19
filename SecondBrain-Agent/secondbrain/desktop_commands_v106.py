from pathlib import Path
from .utils import now_date, slugify, ensure_unique_path

class DesktopCommandService:
    def __init__(self, vault_path: str | Path):
        self.vault = Path(vault_path)

    def quick_capture(self, text: str, title: str = "Quick Capture") -> Path:
        folder = self.vault / "154_QuickCapture"
        folder.mkdir(parents=True, exist_ok=True)
        target = ensure_unique_path(folder / f"{now_date()}_{slugify(title)}.md")
        target.write_text(f"---\ntype: quick_capture\ncreated: {now_date()}\n---\n\n# {title}\n\n{text.strip()}\n", encoding="utf-8")
        return target

    def notification(self, message: str, severity: str = "info") -> Path:
        folder = self.vault / "155_Notifications"
        folder.mkdir(parents=True, exist_ok=True)
        target = folder / f"{now_date()}_notifications.md"
        with target.open("a", encoding="utf-8") as f:
            f.write(f"- **{severity}**: {message.strip()}\n")
        return target
