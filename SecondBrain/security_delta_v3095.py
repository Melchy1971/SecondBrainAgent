"""v30.95 security delta - guards closing the attack-surface gaps that the
existing ``security_gate_v3095`` does not yet cover.

The existing gate already covers prompt-injection, RAG trust boundaries and
parser/archive hardening. This module adds the remaining input- and
boundary-level guards found in the delta audit and exposes them as additional
deterministic gate checks. Every guard returns a :class:`SecurityDecision` with
the full decision record required by the security policy (rule_id, risk_level,
reason, source, correlation_id, action, blocked, sanitized, audit_reference) so
each verdict is auditable without leaking the inspected value.

The module is dependency-free (standard library only) so it runs in the gate,
in tests and on a machine without the full application runtime.
"""

from __future__ import annotations

import hmac
import ipaddress
import os
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from hashlib import sha256
from typing import Any, Iterable, Sequence
from urllib.parse import urlsplit
from uuid import uuid4

__all__ = [
    "TrustLevel", "RiskLevel", "SecurityDecision",
    "classify_fetch_target", "is_safe_redirect", "resolve_within_root",
    "sanitize_log_value", "tabular_within_limits", "ReplayGuard",
    "assert_same_workspace", "verify_manifest_signature", "safe_sql_identifier",
    "contains_shell_metacharacters", "run_security_delta_checks",
    "ACTION_ALLOW", "ACTION_SANITIZE", "ACTION_BLOCK",
]


class TrustLevel(StrEnum):
    TRUSTED = "trusted"
    UNTRUSTED = "untrusted"
    SANITIZED = "sanitized"
    BLOCKED = "blocked"


class RiskLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


ACTION_ALLOW = "allow"
ACTION_SANITIZE = "sanitize"
ACTION_BLOCK = "block"

# Tabular / structured input ceilings (bytes unless noted).
_LIMITS = {
    "json_bytes": 25 * 1024 * 1024,
    "json_depth": 64,
    "csv_bytes": 100 * 1024 * 1024,
    "csv_rows": 5_000_000,
    "xml_bytes": 25 * 1024 * 1024,
    "xml_depth": 100,
}
_SHELL_META = re.compile(r"[;&|`$><\n\r\\!*?(){}\[\]]")
_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_SQL_IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,62}$")
_INTERNAL_HOST_SUFFIXES = (".internal", ".local", ".localdomain", ".cluster", ".svc")
_INTERNAL_HOST_NAMES = {"localhost", "metadata", "metadata.google.internal"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass(frozen=True)
class SecurityDecision:
    rule_id: str
    risk_level: str
    reason: str
    source: str
    action: str                       # allow | sanitize | block
    blocked: bool
    sanitized: bool
    correlation_id: str = field(default_factory=lambda: uuid4().hex)
    audit_reference: str = ""
    detail: str = ""                  # never contains the raw inspected value

    def __post_init__(self) -> None:
        if not self.audit_reference:
            digest = sha256(
                f"{self.rule_id}|{self.risk_level}|{self.action}|{self.correlation_id}".encode("utf-8")
            ).hexdigest()[:24]
            object.__setattr__(self, "audit_reference", digest)

    @property
    def allowed(self) -> bool:
        return self.action == ACTION_ALLOW

    def to_dict(self) -> dict[str, Any]:
        return {
            "rule_id": self.rule_id, "risk_level": self.risk_level, "reason": self.reason,
            "source": self.source, "action": self.action, "blocked": self.blocked,
            "sanitized": self.sanitized, "correlation_id": self.correlation_id,
            "audit_reference": self.audit_reference, "detail": self.detail, "at": _now(),
        }


def _decision(rule_id: str, risk: RiskLevel, reason: str, source: str, action: str,
              *, correlation_id: str | None = None, detail: str = "") -> SecurityDecision:
    return SecurityDecision(
        rule_id=rule_id, risk_level=risk.value, reason=reason, source=source, action=action,
        blocked=action == ACTION_BLOCK, sanitized=action == ACTION_SANITIZE,
        correlation_id=correlation_id or uuid4().hex, detail=detail,
    )


# --- SSRF / redirects -------------------------------------------------------

def _host_is_internal(host: str) -> tuple[bool, str]:
    h = (host or "").strip().strip("[]").lower()
    if not h:
        return True, "empty_host"
    if h in _INTERNAL_HOST_NAMES or any(h.endswith(s) for s in _INTERNAL_HOST_SUFFIXES):
        return True, "internal_name"
    try:
        ip = ipaddress.ip_address(h)
    except ValueError:
        return False, "public_name"   # a resolvable name; DNS-time re-check is runtime's job
    if (ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved
            or ip.is_multicast or ip.is_unspecified):
        return True, "private_ip"
    if str(ip) == "169.254.169.254":
        return True, "cloud_metadata"
    return False, "public_ip"


def classify_fetch_target(url: str, *, source: str = "connector_fetch",
                          correlation_id: str | None = None) -> SecurityDecision:
    """Classify an outbound fetch URL. Blocks non-http(s), embedded credentials
    and private/internal/metadata targets (SSRF)."""
    parts = urlsplit((url or "").strip())
    if parts.scheme.lower() not in ("http", "https"):
        return _decision("ssrf.scheme", RiskLevel.HIGH, "non_http_scheme", source, ACTION_BLOCK,
                         correlation_id=correlation_id, detail=f"scheme={parts.scheme or 'none'}")
    if parts.username or parts.password:
        return _decision("ssrf.credentials", RiskLevel.HIGH, "embedded_credentials", source, ACTION_BLOCK,
                         correlation_id=correlation_id)
    internal, why = _host_is_internal(parts.hostname or "")
    if internal:
        return _decision("ssrf.internal_target", RiskLevel.CRITICAL, why, source, ACTION_BLOCK,
                         correlation_id=correlation_id, detail=why)
    return _decision("ssrf.allow", RiskLevel.LOW, "public_target", source, ACTION_ALLOW,
                     correlation_id=correlation_id, detail=why)


def is_safe_redirect(location: str, *, source: str = "connector_redirect",
                     correlation_id: str | None = None) -> SecurityDecision:
    return classify_fetch_target(location, source=source, correlation_id=correlation_id)


# --- path / symlink containment --------------------------------------------

def resolve_within_root(root: str | os.PathLike[str], candidate: str | os.PathLike[str],
                        *, source: str = "filesystem", correlation_id: str | None = None) -> SecurityDecision:
    """Resolve ``candidate`` and ensure it stays within ``root`` after following
    symlinks (blocks traversal and symlink escape)."""
    real_root = os.path.realpath(str(root))
    real_target = os.path.realpath(os.path.join(real_root, str(candidate)))
    contained = real_target == real_root or real_target.startswith(real_root + os.sep)
    if not contained:
        return _decision("path.escape", RiskLevel.HIGH, "path_outside_root", source, ACTION_BLOCK,
                         correlation_id=correlation_id, detail="escaped")
    return _decision("path.allow", RiskLevel.LOW, "within_root", source, ACTION_ALLOW,
                     correlation_id=correlation_id)


# --- log forging ------------------------------------------------------------

def sanitize_log_value(value: Any, *, max_length: int = 2000, source: str = "logging") -> tuple[str, SecurityDecision]:
    """Neutralize CR/LF and control characters so an attacker-controlled value
    cannot forge additional log lines. Returns (safe_value, decision)."""
    text = str(value)
    replaced = _CONTROL.sub("�", text.replace("\r", "\\r").replace("\n", "\\n"))
    truncated = replaced[:max_length]
    changed = truncated != text
    action = ACTION_SANITIZE if changed else ACTION_ALLOW
    risk = RiskLevel.MEDIUM if changed else RiskLevel.LOW
    return truncated, _decision("log.forging", risk, "control_chars_neutralized" if changed else "clean",
                                source, action, detail=f"changed={changed}")


# --- oversized structured input --------------------------------------------

def tabular_within_limits(kind: str, *, size_bytes: int, depth: int | None = None, rows: int | None = None,
                          source: str = "document_parser", correlation_id: str | None = None) -> SecurityDecision:
    k = kind.lower()
    byte_key = f"{k}_bytes"
    if byte_key in _LIMITS and size_bytes > _LIMITS[byte_key]:
        return _decision(f"{k}.oversize", RiskLevel.MEDIUM, "size_limit_exceeded", source, ACTION_BLOCK,
                         correlation_id=correlation_id, detail=f"{size_bytes}>{_LIMITS[byte_key]}")
    if depth is not None and f"{k}_depth" in _LIMITS and depth > _LIMITS[f"{k}_depth"]:
        return _decision(f"{k}.depth", RiskLevel.MEDIUM, "depth_limit_exceeded", source, ACTION_BLOCK,
                         correlation_id=correlation_id, detail=f"{depth}>{_LIMITS[f'{k}_depth']}")
    if rows is not None and f"{k}_rows" in _LIMITS and rows > _LIMITS[f"{k}_rows"]:
        return _decision(f"{k}.rows", RiskLevel.MEDIUM, "row_limit_exceeded", source, ACTION_BLOCK,
                         correlation_id=correlation_id, detail=f"{rows}>{_LIMITS[f'{k}_rows']}")
    return _decision(f"{k}.allow", RiskLevel.LOW, "within_limits", source, ACTION_ALLOW,
                     correlation_id=correlation_id)


# --- approval replay --------------------------------------------------------

class ReplayGuard:
    """Exactly-once guard for approval commits. A (approval_id, payload_hash)
    pair may be consumed once; a second attempt is a replay and is blocked."""

    def __init__(self) -> None:
        self._used: set[str] = set()

    @staticmethod
    def _key(approval_id: str, payload_hash: str) -> str:
        return sha256(f"{approval_id}|{payload_hash}".encode("utf-8")).hexdigest()

    def check(self, approval_id: str, payload_hash: str, *, source: str = "approval_commit",
              correlation_id: str | None = None) -> SecurityDecision:
        key = self._key(approval_id, payload_hash)
        if key in self._used:
            return _decision("approval.replay", RiskLevel.CRITICAL, "replayed_approval", source, ACTION_BLOCK,
                             correlation_id=correlation_id)
        self._used.add(key)
        return _decision("approval.fresh", RiskLevel.LOW, "first_use", source, ACTION_ALLOW,
                         correlation_id=correlation_id)


# --- workspace crossing -----------------------------------------------------

def assert_same_workspace(actor_workspace: str, resource_workspace: str, *, source: str = "workspace",
                          correlation_id: str | None = None) -> SecurityDecision:
    if (actor_workspace or "") != (resource_workspace or "") or not actor_workspace:
        return _decision("workspace.crossing", RiskLevel.HIGH, "workspace_mismatch", source, ACTION_BLOCK,
                         correlation_id=correlation_id)
    return _decision("workspace.same", RiskLevel.LOW, "same_workspace", source, ACTION_ALLOW,
                     correlation_id=correlation_id)


# --- manifest signature (plugin / update) ----------------------------------

def verify_manifest_signature(payload: bytes, *, signature_hex: str, signing_key_id: str,
                              trusted_keys: dict[str, bytes], source: str = "manifest",
                              correlation_id: str | None = None) -> SecurityDecision:
    """Require a valid signature from a trusted key. Unsigned, unknown-key or
    mismatched signatures are blocked (plugin manifest / update manifest)."""
    if not signature_hex or not signing_key_id:
        return _decision("manifest.unsigned", RiskLevel.CRITICAL, "missing_signature", source, ACTION_BLOCK,
                         correlation_id=correlation_id)
    key = trusted_keys.get(signing_key_id)
    if key is None:
        return _decision("manifest.untrusted_key", RiskLevel.CRITICAL, "unknown_signing_key", source, ACTION_BLOCK,
                         correlation_id=correlation_id, detail=f"key_id={signing_key_id}")
    expected = hmac.new(key, payload, sha256).hexdigest()
    if not hmac.compare_digest(expected, signature_hex.lower()):
        return _decision("manifest.bad_signature", RiskLevel.CRITICAL, "signature_mismatch", source, ACTION_BLOCK,
                         correlation_id=correlation_id)
    return _decision("manifest.trusted", RiskLevel.LOW, "valid_signature", source, ACTION_ALLOW,
                     correlation_id=correlation_id)


# --- command / SQL identifier safety ---------------------------------------

def contains_shell_metacharacters(value: str) -> bool:
    return bool(_SHELL_META.search(value or ""))


def safe_sql_identifier(name: str, *, source: str = "sql", correlation_id: str | None = None) -> SecurityDecision:
    """Validate a dynamic SQL identifier (table/column). Values must be simple
    identifiers - anything else is blocked to prevent identifier-level injection."""
    if _SQL_IDENT.match(name or ""):
        return _decision("sql.identifier_ok", RiskLevel.LOW, "valid_identifier", source, ACTION_ALLOW,
                         correlation_id=correlation_id)
    return _decision("sql.identifier_blocked", RiskLevel.HIGH, "invalid_identifier", source, ACTION_BLOCK,
                     correlation_id=correlation_id)


# --- gate integration -------------------------------------------------------

def run_security_delta_checks() -> list[dict[str, Any]]:
    """Positive+negative probes for each delta guard, shaped like the existing
    gate's ``SecurityCheck.to_dict()`` so they append into ``run_security_gate``."""
    results: list[dict[str, Any]] = []

    def record(check_id: str, title: str, passed: bool, detail: str) -> None:
        results.append({"check_id": check_id, "title": title,
                        "status": "PASS" if passed else "FAIL", "passed": passed, "detail": detail})

    # SSRF
    blocked = classify_fetch_target("http://169.254.169.254/latest/meta-data/").blocked
    blocked2 = classify_fetch_target("http://127.0.0.1:5432/").blocked
    allowed = classify_fetch_target("https://api.github.com/repos").allowed
    record("ssrf", "Internal and metadata fetch targets are blocked",
           blocked and blocked2 and allowed, f"metadata={blocked}; loopback={blocked2}; public_ok={allowed}")

    # symlink / traversal
    esc = resolve_within_root("/srv/data", "../../etc/passwd").blocked
    ok = resolve_within_root("/srv/data", "sub/file.txt").allowed
    record("path_escape", "Path traversal and symlink escape are blocked", esc and ok, f"escape_blocked={esc}")

    # log forging
    _, dec = sanitize_log_value("user\r\nADMIN logged in")
    record("log_forging", "Log values with CR/LF are neutralized", dec.sanitized, f"action={dec.action}")

    # oversized tabular
    big = tabular_within_limits("csv", size_bytes=_LIMITS["csv_bytes"] + 1).blocked
    xml = tabular_within_limits("xml", size_bytes=1, depth=_LIMITS["xml_depth"] + 5).blocked
    record("tabular_limits", "Oversized CSV and deep XML are blocked", big and xml, f"csv={big}; xml={xml}")

    # approval replay
    guard = ReplayGuard()
    first = guard.check("a-1", "hash-1").allowed
    replay = guard.check("a-1", "hash-1").blocked
    record("approval_replay", "Approval replay is blocked", first and replay, f"first={first}; replay_blocked={replay}")

    # workspace crossing
    cross = assert_same_workspace("ws-1", "ws-2").blocked
    same = assert_same_workspace("ws-1", "ws-1").allowed
    record("workspace_crossing", "Cross-workspace access is blocked", cross and same, f"cross_blocked={cross}")

    # manifest signature
    keys = {"k1": b"secret-key"}
    payload = b'{"version":"1.2.3"}'
    good = hmac.new(keys["k1"], payload, sha256).hexdigest()
    valid = verify_manifest_signature(payload, signature_hex=good, signing_key_id="k1", trusted_keys=keys).allowed
    unsigned = verify_manifest_signature(payload, signature_hex="", signing_key_id="", trusted_keys=keys).blocked
    untrusted = verify_manifest_signature(payload, signature_hex=good, signing_key_id="kX", trusted_keys=keys).blocked
    record("manifest_signature", "Unsigned or untrusted manifests are blocked",
           valid and unsigned and untrusted, f"valid={valid}; unsigned_blocked={unsigned}; untrusted_blocked={untrusted}")

    # sql identifier / shell
    sql_ok = safe_sql_identifier("user_events").allowed
    sql_bad = safe_sql_identifier("users; DROP TABLE x").blocked
    shell = contains_shell_metacharacters("rm -rf / ; echo pwned")
    record("injection_identifiers", "SQL identifiers and shell metacharacters are validated",
           sql_ok and sql_bad and shell, f"sql_ok={sql_ok}; sql_bad_blocked={sql_bad}; shell={shell}")

    return results
