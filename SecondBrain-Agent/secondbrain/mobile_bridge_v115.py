
from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any
import json
import time
import uuid


@dataclass
class MobileDevice:
    device_id: str
    name: str
    platform: str
    capabilities: list[str]
    registered_at: float
    last_seen_at: float
    trusted: bool = False
    status: str = "active"


@dataclass
class MobileMessage:
    message_id: str
    device_id: str
    kind: str
    title: str
    body: str
    payload: dict[str, Any]
    created_at: float
    status: str = "queued"
    delivered_at: float | None = None


@dataclass
class MobileApproval:
    approval_id: str
    device_id: str
    action: str
    payload: dict[str, Any]
    reason: str
    risk_level: int
    created_at: float
    status: str = "pending"
    decided_at: float | None = None
    decision_note: str = ""


@dataclass
class MobileCapture:
    capture_id: str
    device_id: str
    capture_type: str
    title: str
    content: str
    metadata: dict[str, Any]
    created_at: float
    processed: bool = False


class MobileBridgeStore:
    def __init__(self, runtime_dir: str | Path):
        self.base = Path(runtime_dir) / "mobile"
        self.base.mkdir(parents=True, exist_ok=True)
        self.devices_file = self.base / "devices.json"
        self.outbox_file = self.base / "push_outbox.json"
        self.approvals_file = self.base / "approval_inbox.json"
        self.captures_file = self.base / "captures.json"
        self.settings_file = self.base / "settings.json"
        self._ensure()

    def _ensure(self) -> None:
        defaults = {
            self.devices_file: {},
            self.outbox_file: [],
            self.approvals_file: [],
            self.captures_file: [],
            self.settings_file: {
                "version": "11.5",
                "mode": "local_bridge",
                "require_trusted_device_for_approvals": True,
                "max_pending_push": 250,
                "allowed_platforms": ["ios", "android", "web", "desktop"],
            },
        }
        for path, value in defaults.items():
            if not path.exists():
                path.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")

    def load(self, path: Path) -> Any:
        return json.loads(path.read_text(encoding="utf-8"))

    def save(self, path: Path, value: Any) -> None:
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")
        tmp.replace(path)


class MobileBridge:
    """Local-first mobile bridge.

    It intentionally writes JSON queues instead of sending real push traffic. A later
    iOS/Android/Web companion can poll these files through a small API server.
    """

    VALID_PLATFORMS = {"ios", "android", "web", "desktop"}
    SAFE_CAPTURE_TYPES = {"note", "voice_note", "photo_note", "url", "task"}

    def __init__(self, runtime_dir: str | Path):
        self.store = MobileBridgeStore(runtime_dir)

    def status(self) -> dict[str, Any]:
        devices = self.store.load(self.store.devices_file)
        outbox = self.store.load(self.store.outbox_file)
        approvals = self.store.load(self.store.approvals_file)
        captures = self.store.load(self.store.captures_file)
        return {
            "version": "11.5",
            "devices": len(devices),
            "trusted_devices": len([d for d in devices.values() if d.get("trusted")]),
            "queued_push": len([m for m in outbox if m.get("status") == "queued"]),
            "pending_approvals": len([a for a in approvals if a.get("status") == "pending"]),
            "captures": len(captures),
            "unprocessed_captures": len([c for c in captures if not c.get("processed")]),
        }

    def register_device(self, name: str, platform: str, capabilities: list[str] | None = None, trusted: bool = False) -> dict[str, Any]:
        platform = platform.lower().strip()
        if platform not in self.VALID_PLATFORMS:
            raise ValueError(f"unsupported platform: {platform}")
        devices = self.store.load(self.store.devices_file)
        now = time.time()
        device = MobileDevice(
            device_id=str(uuid.uuid4()),
            name=name.strip() or "Unnamed Device",
            platform=platform,
            capabilities=capabilities or ["capture", "push", "approval"],
            registered_at=now,
            last_seen_at=now,
            trusted=trusted,
        )
        devices[device.device_id] = asdict(device)
        self.store.save(self.store.devices_file, devices)
        return asdict(device)

    def list_devices(self) -> list[dict[str, Any]]:
        return list(self.store.load(self.store.devices_file).values())

    def trust_device(self, device_id: str, trusted: bool = True) -> dict[str, Any]:
        devices = self.store.load(self.store.devices_file)
        if device_id not in devices:
            raise KeyError(f"unknown mobile device: {device_id}")
        devices[device_id]["trusted"] = trusted
        devices[device_id]["last_seen_at"] = time.time()
        self.store.save(self.store.devices_file, devices)
        return devices[device_id]

    def enqueue_push(self, device_id: str, title: str, body: str, kind: str = "notification", payload: dict[str, Any] | None = None) -> dict[str, Any]:
        self._require_device(device_id)
        outbox = self.store.load(self.store.outbox_file)
        settings = self.store.load(self.store.settings_file)
        queued = [m for m in outbox if m.get("status") == "queued"]
        if len(queued) >= int(settings.get("max_pending_push", 250)):
            raise RuntimeError("push outbox limit reached")
        msg = MobileMessage(str(uuid.uuid4()), device_id, kind, title, body, payload or {}, time.time())
        outbox.append(asdict(msg))
        self.store.save(self.store.outbox_file, outbox)
        return asdict(msg)

    def list_push(self, device_id: str | None = None, status: str | None = None) -> list[dict[str, Any]]:
        outbox = self.store.load(self.store.outbox_file)
        if device_id:
            outbox = [m for m in outbox if m.get("device_id") == device_id]
        if status:
            outbox = [m for m in outbox if m.get("status") == status]
        return outbox

    def mark_push_delivered(self, message_id: str) -> dict[str, Any]:
        outbox = self.store.load(self.store.outbox_file)
        for msg in outbox:
            if msg.get("message_id") == message_id:
                msg["status"] = "delivered"
                msg["delivered_at"] = time.time()
                self.store.save(self.store.outbox_file, outbox)
                return msg
        raise KeyError(f"unknown push message: {message_id}")

    def submit_capture(self, device_id: str, capture_type: str, title: str, content: str, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
        self._require_device(device_id)
        capture_type = capture_type.lower().strip()
        if capture_type not in self.SAFE_CAPTURE_TYPES:
            raise ValueError(f"unsupported capture type: {capture_type}")
        captures = self.store.load(self.store.captures_file)
        capture = MobileCapture(str(uuid.uuid4()), device_id, capture_type, title, content, metadata or {}, time.time())
        captures.append(asdict(capture))
        self.store.save(self.store.captures_file, captures)
        return asdict(capture)

    def list_captures(self, unprocessed_only: bool = False) -> list[dict[str, Any]]:
        captures = self.store.load(self.store.captures_file)
        if unprocessed_only:
            captures = [c for c in captures if not c.get("processed")]
        return captures

    def request_approval(self, device_id: str, action: str, payload: dict[str, Any], reason: str, risk_level: int = 3) -> dict[str, Any]:
        device = self._require_device(device_id)
        settings = self.store.load(self.store.settings_file)
        if settings.get("require_trusted_device_for_approvals", True) and not device.get("trusted"):
            raise PermissionError("device must be trusted for approval requests")
        approvals = self.store.load(self.store.approvals_file)
        approval = MobileApproval(str(uuid.uuid4()), device_id, action, payload, reason, int(risk_level), time.time())
        approvals.append(asdict(approval))
        self.store.save(self.store.approvals_file, approvals)
        self.enqueue_push(device_id, "Approval required", reason, kind="approval", payload={"approval_id": approval.approval_id, "action": action, "risk_level": risk_level})
        return asdict(approval)

    def list_approvals(self, status: str | None = "pending") -> list[dict[str, Any]]:
        approvals = self.store.load(self.store.approvals_file)
        if status:
            approvals = [a for a in approvals if a.get("status") == status]
        return approvals

    def decide_approval(self, approval_id: str, decision: str, note: str = "") -> dict[str, Any]:
        if decision not in {"approved", "rejected"}:
            raise ValueError("decision must be approved or rejected")
        approvals = self.store.load(self.store.approvals_file)
        for approval in approvals:
            if approval.get("approval_id") == approval_id:
                if approval.get("status") != "pending":
                    raise RuntimeError("approval already decided")
                approval["status"] = decision
                approval["decided_at"] = time.time()
                approval["decision_note"] = note
                self.store.save(self.store.approvals_file, approvals)
                return approval
        raise KeyError(f"unknown approval: {approval_id}")

    def _require_device(self, device_id: str) -> dict[str, Any]:
        devices = self.store.load(self.store.devices_file)
        if device_id not in devices:
            raise KeyError(f"unknown mobile device: {device_id}")
        devices[device_id]["last_seen_at"] = time.time()
        self.store.save(self.store.devices_file, devices)
        return devices[device_id]
