"""Fail-closed certification gate for signed Windows installer artifacts."""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping, Protocol
from uuid import uuid4

PASS, BLOCKED, SKIPPED = "PASS", "BLOCKED", "SKIPPED"
REPORT_PATH = Path("runtime/reports/windows_installer_gate.json")
PHASES = (
    "preflight", "clean_build", "artifact_inventory", "hash_generation",
    "signature_verification", "silent_install", "desktop_shortcut",
    "application_start", "health_check", "upgrade", "rollback", "uninstall",
    "residue_check", "report",
)
_TARGET_PHASES = PHASES[5:13]
_SENSITIVE = re.compile(
    r"(?i)(?:[a-z]:\\(?:users\\[^\\]+|[^\\\s]+)|\\\\[^\\\s]+\\[^\\\s]+|"
    r"[\w.+-]+:[^@\s]+@|password|secret|token|credential)"
)


class GateSteps(Protocol):
    def run_phase(self, phase: str, context: dict[str, Any]) -> dict[str, Any]: ...
    def cleanup(self) -> None: ...


def _safe_detail(value: Any) -> str:
    text = str(value or "")
    return "redacted" if _SENSITIVE.search(text) else text[:240]


def _phase(name: str, status: str, detail: str = "", **evidence: Any) -> dict[str, Any]:
    return {
        "name": name,
        "status": status if status in {PASS, BLOCKED, SKIPPED} else BLOCKED,
        "detail": _safe_detail(detail),
        "evidence": evidence,
    }


def _atomic_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as stream:
        json.dump(payload, stream, indent=2, ensure_ascii=False, sort_keys=True)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


class LiveWindowsInstallerSteps:
    """Host build plus standalone PowerShell certification on a clean VM."""

    def __init__(
        self,
        root: Path,
        *,
        env: Mapping[str, str],
        run: Callable[..., Any] = subprocess.run,
    ) -> None:
        self.root = root
        self.env = dict(env)
        self.run = run
        self.release = root / "dist" / "release"
        self.target_evidence = root / "runtime" / "reports" / "windows_installer_target.json"
        self.artifacts: list[Path] = []
        self._target_results: dict[str, dict[str, Any]] | None = None

    def _exec(self, args: list[str], *, check: bool = True) -> Any:
        return self.run(
            args, cwd=self.root, env={**os.environ, **self.env}, check=check,
            capture_output=True, text=True,
        )

    def run_phase(self, phase: str, context: dict[str, Any]) -> dict[str, Any]:
        handler = getattr(self, f"_phase_{phase}", None)
        if handler:
            return handler()
        if phase in _TARGET_PHASES:
            return self._target_phase(phase)
        if phase == "report":
            return _phase(phase, PASS, "atomic report prepared")
        return _phase(phase, BLOCKED, "phase_not_implemented")

    def _phase_preflight(self) -> dict[str, Any]:
        if sys.platform != "win32":
            return _phase("preflight", SKIPPED, "Windows host unavailable")
        if not self.env.get("WINDOWS_SIGNING_CERT_THUMBPRINT"):
            return _phase("preflight", BLOCKED, "code-signing certificate missing")
        isolation = self.env.get("WINDOWS_INSTALLER_GATE_ISOLATION", "").lower()
        if isolation not in {"windows-sandbox", "clean-vm"}:
            return _phase("preflight", SKIPPED, "clean Windows isolation unavailable")
        required = (
            self.root / "packaging/windows/build.ps1",
            self.root / "packaging/windows/installer_certification.ps1",
        )
        if not all(path.is_file() for path in required):
            return _phase("preflight", BLOCKED, "required packaging assets missing")
        if not self.env.get("WINDOWS_INSTALLER_PREVIOUS_SETUP"):
            return _phase("preflight", BLOCKED, "previous signed installer missing")
        return _phase("preflight", PASS, "clean Windows target configured",
                      isolation=isolation, standard_user=True)

    def _phase_clean_build(self) -> dict[str, Any]:
        try:
            self._exec([
                "powershell.exe", "-NoProfile", "-NonInteractive",
                "-ExecutionPolicy", "Bypass", "-File",
                str(self.root / "packaging/windows/build.ps1"),
                "-SkipInstallerSmoke",
            ])
            return _phase("clean_build", PASS, "reproducible build completed")
        except Exception as exc:
            return _phase("clean_build", BLOCKED, type(exc).__name__)

    def _phase_artifact_inventory(self) -> dict[str, Any]:
        patterns = ("*.exe", "*.msi", "*.zip")
        self.artifacts = sorted(
            {path for pattern in patterns for path in self.release.glob(pattern)}
        )
        installers = [p for p in self.artifacts if p.suffix.lower() in {".exe", ".msi"}]
        status = PASS if self.artifacts and installers else BLOCKED
        inventory = [{"name": p.name, "bytes": p.stat().st_size} for p in self.artifacts]
        return _phase("artifact_inventory", status, "release artifacts inventoried",
                      artifacts=inventory)

    def _phase_hash_generation(self) -> dict[str, Any]:
        if not self.artifacts:
            return _phase("hash_generation", BLOCKED, "artifact inventory empty")
        hashes = []
        for artifact in self.artifacts:
            digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
            checksum_file = artifact.with_suffix(artifact.suffix + ".sha256")
            checksum_file.write_text(f"{digest}  {artifact.name}\n", encoding="ascii")
            hashes.append({"name": artifact.name, "sha256": digest})
        return _phase("hash_generation", PASS, "SHA-256 generated", hashes=hashes)

    def _phase_signature_verification(self) -> dict[str, Any]:
        signed = [p for p in self.artifacts if p.suffix.lower() in {".exe", ".msi"}]
        previous_value = self.env.get("WINDOWS_INSTALLER_PREVIOUS_SETUP", "")
        if previous_value:
            previous = Path(previous_value)
            if previous.is_file():
                signed.append(previous)
        if not signed or not self.env.get("WINDOWS_SIGNING_CERT_THUMBPRINT"):
            return _phase("signature_verification", BLOCKED, "code-signing certificate missing")
        statuses = []
        expected = re.sub(r"\s", "", self.env["WINDOWS_SIGNING_CERT_THUMBPRINT"]).upper()
        for artifact in signed:
            script = (
                "$s=Get-AuthenticodeSignature -LiteralPath $args[0];"
                "[Console]::WriteLine(($s.Status.ToString())+'|'+$s.SignerCertificate.Thumbprint)"
            )
            try:
                output = self._exec(
                    ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command",
                     script, str(artifact)]
                ).stdout.strip()
                status, _, thumbprint = output.partition("|")
                valid = status == "Valid" and thumbprint.upper() == expected
            except Exception:
                valid = False
                status = "Error"
            role = "rollback" if previous_value and artifact == Path(previous_value) else "release"
            statuses.append({
                "name": artifact.name, "role": role, "valid": valid, "status": status,
            })
        return _phase("signature_verification",
                      PASS if all(row["valid"] for row in statuses) else BLOCKED,
                      "Authenticode signatures verified", signatures=statuses)

    def _load_target_results(self) -> dict[str, dict[str, Any]]:
        if self._target_results is not None:
            return self._target_results
        previous = Path(self.env["WINDOWS_INSTALLER_PREVIOUS_SETUP"])
        setup = next(
            (p for p in self.artifacts if p.name.lower().startswith("jarvis-setup-")),
            None,
        )
        if setup is None or not previous.is_file():
            raise RuntimeError("installer_pair_missing")
        self.target_evidence.unlink(missing_ok=True)
        self._exec([
            "powershell.exe", "-NoProfile", "-NonInteractive",
            "-ExecutionPolicy", "Bypass", "-File",
            str(self.root / "packaging/windows/installer_certification.ps1"),
            "-CurrentSetup", str(setup), "-PreviousSetup", str(previous),
            "-EvidencePath", str(self.target_evidence),
        ])
        raw = json.loads(self.target_evidence.read_text(encoding="utf-8-sig"))
        self._target_results = {
            str(row["name"]): row for row in raw.get("phases", [])
            if isinstance(row, dict) and row.get("name")
        }
        return self._target_results

    def _target_phase(self, phase: str) -> dict[str, Any]:
        try:
            row = self._load_target_results().get(phase)
            if not row:
                return _phase(phase, BLOCKED, "target evidence missing")
            return _phase(phase, row.get("status", BLOCKED), row.get("detail", ""))
        except Exception as exc:
            return _phase(phase, BLOCKED, type(exc).__name__)

    def cleanup(self) -> None:
        self.target_evidence.unlink(missing_ok=True)


def run_windows_installer_gate(
    project_root: str | Path = ".",
    *,
    env: Mapping[str, str] | None = None,
    steps: GateSteps | None = None,
    write_report: bool = True,
) -> dict[str, Any]:
    root = Path(project_root).resolve()
    values = dict(os.environ if env is None else env)
    executor = steps or LiveWindowsInstallerSteps(root, env=values)
    rows: list[dict[str, Any]] = []
    context: dict[str, Any] = {}
    halted = False
    try:
        for name in PHASES:
            if halted and name != "report":
                row = _phase(name, SKIPPED, "blocked by earlier phase")
            else:
                try:
                    row = executor.run_phase(name, context)
                except Exception as exc:
                    row = _phase(name, BLOCKED, type(exc).__name__)
            rows.append(row)
            context[name] = row
            halted = halted or row["status"] in {BLOCKED, SKIPPED}
    finally:
        executor.cleanup()

    statuses = {row["status"] for row in rows if row["name"] != "report"}
    overall = BLOCKED if BLOCKED in statuses else (SKIPPED if SKIPPED in statuses else PASS)
    report = {
        "schema": "secondbrain.windows-installer-gate.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": overall,
        "ok": overall == PASS,
        "phases": rows,
        "artifacts": context.get("artifact_inventory", {}).get("evidence", {}).get("artifacts", []),
        "test_environment": context.get("preflight", {}).get("evidence", {}),
        "signature_status": (
            BLOCKED
            if context.get("preflight", {}).get("detail") == "code-signing certificate missing"
            else context.get("signature_verification", {}).get("status", SKIPPED)
        ),
        "blockers": [row["name"] for row in rows if row["status"] == BLOCKED],
        "skipped": [row["name"] for row in rows if row["status"] == SKIPPED],
    }
    if write_report:
        target = root / REPORT_PATH
        try:
            _atomic_json(target, report)
            report["report"] = REPORT_PATH.as_posix()
        except Exception:
            report["status"] = BLOCKED
            report["ok"] = False
            report["blockers"].append("report")
            report["phases"][-1] = _phase("report", BLOCKED, "atomic report write failed")
    return report


__all__ = [
    "BLOCKED", "PASS", "PHASES", "REPORT_PATH", "SKIPPED",
    "LiveWindowsInstallerSteps", "run_windows_installer_gate",
]
