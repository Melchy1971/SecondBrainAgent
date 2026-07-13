from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

VERSION = "30.36"
REPORT_DIR = Path("runtime/native/installer")
DEFAULT_OUTPUT_DIR = Path("dist/native-installer")


@dataclass(frozen=True)
class InstallerCheck:
    key: str
    ok: bool
    severity: str
    message: str
    path: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class InstallerArtifact:
    name: str
    path: str
    kind: str
    purpose: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _root(project_root: str | Path = ".") -> Path:
    return Path(project_root).resolve()


def _exists(root: Path, rel: str) -> bool:
    return (root / rel).exists()


def _detect_native_modules(root: Path) -> list[str]:
    native = root / "secondbrain" / "native"
    if not native.exists():
        return []
    return sorted(p.stem for p in native.glob("*.py") if not p.name.startswith("__"))


def installer_status(project_root: str | Path = ".") -> dict[str, Any]:
    root = _root(project_root)
    native_modules = _detect_native_modules(root)
    checks = [
        InstallerCheck("project_root", root.exists(), "blocker", "Projektverzeichnis existiert", str(root)),
        InstallerCheck("launcher", _exists(root, "launcher.py"), "blocker", "launcher.py vorhanden", "launcher.py"),
        InstallerCheck("pyproject", _exists(root, "pyproject.toml"), "warning", "pyproject.toml vorhanden", "pyproject.toml"),
        InstallerCheck("requirements_runtime", _exists(root, "requirements-runtime.txt") or _exists(root, "requirements.txt"), "warning", "Runtime Requirements vorhanden", "requirements-runtime.txt"),
        InstallerCheck("requirements_voice", _exists(root, "requirements-voice.txt"), "warning", "Voice Requirements vorhanden", "requirements-voice.txt"),
        InstallerCheck("jarvis_bat", _exists(root, "Jarvis.bat"), "warning", "Jarvis.bat vorhanden", "Jarvis.bat"),
        InstallerCheck("native_package", (root / "secondbrain" / "native").exists(), "blocker", "Native Package vorhanden", "secondbrain/native"),
        InstallerCheck("native_workspace", "workspace_center" in native_modules or "native_app" in native_modules, "warning", "Native Workspace/App vorhanden", "secondbrain/native"),
        InstallerCheck("native_voice", any("voice" in m for m in native_modules), "warning", "Deutsche Sprachsteuerung vorhanden", "secondbrain/native"),
    ]
    blockers = [c for c in checks if not c.ok and c.severity == "blocker"]
    warnings = [c for c in checks if not c.ok and c.severity == "warning"]
    return {
        "ok": not blockers,
        "status": "ready" if not blockers else "blocked",
        "version": VERSION,
        "project_root": str(root),
        "python": sys.version.split()[0],
        "platform": sys.platform,
        "native_modules": native_modules,
        "checks": [c.to_dict() for c in checks],
        "blockers": [c.to_dict() for c in blockers],
        "warnings": [c.to_dict() for c in warnings],
        "timestamp": _now(),
    }


def installer_plan(project_root: str | Path = ".") -> dict[str, Any]:
    status = installer_status(project_root)
    root = _root(project_root)
    artifacts = [
        InstallerArtifact("Start-Jarvis-Native.bat", str(DEFAULT_OUTPUT_DIR / "Start-Jarvis-Native.bat"), "windows_start", "Startet Jarvis als native Desktop-Anwendung."),
        InstallerArtifact("Install-Jarvis-Native.ps1", str(DEFAULT_OUTPUT_DIR / "Install-Jarvis-Native.ps1"), "installer", "Erzeugt Desktop-/Startmenü-Verknüpfungen und prüft Python."),
        InstallerArtifact("Create-Jarvis-Shortcuts.ps1", str(DEFAULT_OUTPUT_DIR / "Create-Jarvis-Shortcuts.ps1"), "shortcuts", "Erstellt Desktop-, Startmenü- und optional Autostart-Verknüpfung."),
        InstallerArtifact("Uninstall-Jarvis-Native.ps1", str(DEFAULT_OUTPUT_DIR / "Uninstall-Jarvis-Native.ps1"), "uninstaller", "Entfernt erzeugte Verknüpfungen."),
        InstallerArtifact("README_NATIVE_INSTALLER.md", str(DEFAULT_OUTPUT_DIR / "README_NATIVE_INSTALLER.md"), "documentation", "Installations- und Startanleitung."),
    ]
    return {
        "ok": status["ok"],
        "status": status["status"],
        "version": VERSION,
        "project_root": str(root),
        "primary_start": "python launcher.py",
        "fallback_start": "python launcher.py native-gui",
        "web_start": "python launcher.py hud",
        "artifacts": [a.to_dict() for a in artifacts],
        "warnings": status["warnings"],
        "blockers": status["blockers"],
        "timestamp": _now(),
    }


def _bat_content() -> str:
    return r'''@echo off
setlocal
cd /d "%~dp0\..\.."
where python >nul 2>nul
if errorlevel 1 (
  echo Python wurde nicht gefunden. Bitte Python 3.11+ installieren.
  pause
  exit /b 1
)
python launcher.py
if errorlevel 1 (
  echo Jarvis konnte nicht gestartet werden.
  pause
  exit /b %errorlevel%
)
'''


def _install_ps1() -> str:
    return r'''param(
  [switch]$Autostart
)
$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Resolve-Path (Join-Path $ScriptDir "..\..")
$StartBat = Join-Path $ScriptDir "Start-Jarvis-Native.bat"
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
  throw "Python wurde nicht gefunden. Installiere Python 3.11+ und starte dieses Script erneut."
}
python --version
$Desktop = [Environment]::GetFolderPath("Desktop")
$StartMenu = Join-Path ([Environment]::GetFolderPath("Programs")) "Jarvis"
New-Item -ItemType Directory -Force -Path $StartMenu | Out-Null
$Wsh = New-Object -ComObject WScript.Shell
foreach ($Target in @((Join-Path $Desktop "Jarvis.lnk"), (Join-Path $StartMenu "Jarvis.lnk"))) {
  $Shortcut = $Wsh.CreateShortcut($Target)
  $Shortcut.TargetPath = $StartBat
  $Shortcut.WorkingDirectory = $ProjectRoot
  $Shortcut.Description = "Jarvis Native Desktop"
  $Shortcut.Save()
}
if ($Autostart) {
  $Startup = [Environment]::GetFolderPath("Startup")
  $Shortcut = $Wsh.CreateShortcut((Join-Path $Startup "Jarvis.lnk"))
  $Shortcut.TargetPath = $StartBat
  $Shortcut.WorkingDirectory = $ProjectRoot
  $Shortcut.Description = "Jarvis Native Desktop Autostart"
  $Shortcut.Save()
}
Write-Host "Jarvis Native Desktop wurde eingerichtet."
'''


def _shortcuts_ps1() -> str:
    return r'''param([switch]$Autostart)
& "$PSScriptRoot\Install-Jarvis-Native.ps1" @PSBoundParameters
'''


def _uninstall_ps1() -> str:
    return r'''$DesktopLink = Join-Path ([Environment]::GetFolderPath("Desktop")) "Jarvis.lnk"
$StartMenuDir = Join-Path ([Environment]::GetFolderPath("Programs")) "Jarvis"
$StartupLink = Join-Path ([Environment]::GetFolderPath("Startup")) "Jarvis.lnk"
foreach ($Path in @($DesktopLink, $StartupLink)) {
  if (Test-Path $Path) { Remove-Item $Path -Force }
}
if (Test-Path $StartMenuDir) { Remove-Item $StartMenuDir -Recurse -Force }
Write-Host "Jarvis Verknüpfungen wurden entfernt."
'''


def _readme() -> str:
    return """# Jarvis Native Installer v30.36\n\nPrimärstart:\n\n```bash\npython launcher.py\n```\n\nWindows-Start per Doppelklick:\n\n```text\ndist/native-installer/Start-Jarvis-Native.bat\n```\n\nVerknüpfungen erzeugen:\n\n```powershell\npowershell -ExecutionPolicy Bypass -File dist/native-installer/Install-Jarvis-Native.ps1\n```\n\nMit Autostart:\n\n```powershell\npowershell -ExecutionPolicy Bypass -File dist/native-installer/Install-Jarvis-Native.ps1 -Autostart\n```\n\nEntfernen:\n\n```powershell\npowershell -ExecutionPolicy Bypass -File dist/native-installer/Uninstall-Jarvis-Native.ps1\n```\n"""


def write_installer_artifacts(project_root: str | Path = ".", output_dir: str | Path | None = None) -> dict[str, Any]:
    root = _root(project_root)
    status = installer_status(root)
    out_dir = root / (Path(output_dir) if output_dir else DEFAULT_OUTPUT_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)
    files = {
        "Start-Jarvis-Native.bat": _bat_content(),
        "Install-Jarvis-Native.ps1": _install_ps1(),
        "Create-Jarvis-Shortcuts.ps1": _shortcuts_ps1(),
        "Uninstall-Jarvis-Native.ps1": _uninstall_ps1(),
        "README_NATIVE_INSTALLER.md": _readme(),
    }
    written = []
    for name, content in files.items():
        path = out_dir / name
        path.write_text(content, encoding="utf-8", newline="\n")
        written.append(path.relative_to(root).as_posix())
    report = {
        "ok": status["ok"],
        "status": "written" if status["ok"] else "written_with_blockers",
        "version": VERSION,
        "project_root": str(root),
        "output_dir": str(out_dir),
        "written": written,
        "blockers": status["blockers"],
        "warnings": status["warnings"],
        "timestamp": _now(),
    }
    report_dir = root / REPORT_DIR
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / "installer_v30_36.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return report


def print_json(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Jarvis Native Installer Center")
    parser.add_argument("cmd", choices=["status", "plan", "write"])
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--output-dir", default=None)
    args = parser.parse_args()
    if args.cmd == "status":
        print_json(installer_status(args.project_root))
    elif args.cmd == "plan":
        print_json(installer_plan(args.project_root))
    else:
        print_json(write_installer_artifacts(args.project_root, args.output_dir))
