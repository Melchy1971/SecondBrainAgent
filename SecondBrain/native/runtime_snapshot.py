from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from secondbrain.gui.bootstrap import bootstrap_status
from secondbrain.gui.p1_control_panel import P1ControlPanel
from secondbrain.runtime_config import RuntimeConfig
from secondbrain.native.voice_de import GermanVoiceCommandParser
from secondbrain.native.approval import native_audit_status
from secondbrain.native.chat import native_chat_status


def _safe_call(fn, fallback: dict[str, Any]) -> dict[str, Any]:
    try:
        value = fn()
        return value if isinstance(value, dict) else {"ok": True, "value": value}
    except Exception as exc:  # pragma: no cover - defensive runtime boundary
        result = dict(fallback)
        result.update({"ok": False, "error": type(exc).__name__, "detail": str(exc)})
        return result


def _latest_report(root: Path, name: str) -> dict[str, Any]:
    path = root / "runtime" / "reports" / name
    if not path.exists():
        return {"ok": False, "status": "missing", "path": str(path)}
    try:
        return {"ok": True, "path": str(path), "data": json.loads(path.read_text(encoding="utf-8"))}
    except Exception as exc:
        return {"ok": False, "status": "invalid", "path": str(path), "error": str(exc)}


def _rag_status(root: Path) -> dict[str, Any]:
    def call() -> dict[str, Any]:
        from secondbrain.p1_rag_runtime import P1RagRuntime
        rt = P1RagRuntime(root)
        return rt.status()
    return _safe_call(call, {"status": "unavailable"})


def _provider_status(root: Path) -> dict[str, Any]:
    def call() -> dict[str, Any]:
        from secondbrain.p1_rag_runtime import P1RagRuntime
        from secondbrain.p1_provider_health import evaluate_embedding_provider_health
        rt = P1RagRuntime(root)
        return evaluate_embedding_provider_health(rt, production=True, write_report=False)
    return _safe_call(call, {"status": "unavailable"})


def _memory_status(root: Path) -> dict[str, Any]:
    candidates = [
        root / "runtime" / "reports" / "memory_center_latest.json",
        root / "runtime" / "reports" / "memory_status_latest.json",
    ]
    for path in candidates:
        if path.exists():
            try:
                return {"ok": True, "status": "report", "path": str(path), "data": json.loads(path.read_text(encoding="utf-8"))}
            except Exception as exc:
                return {"ok": False, "status": "invalid", "path": str(path), "error": str(exc)}
    return {
        "ok": False,
        "status": "not_initialized",
        "privacy_mode_visible": True,
        "secret_encryption_visible": True,
        "data_classification_visible": True,
        "blockers": ["memory_runtime_report_missing"],
    }


def _production_status(root: Path) -> dict[str, Any]:
    return _latest_report(root, "p1_production_latest.json")


def _review_inbox_status(root: Path) -> dict[str, Any]:
    from secondbrain.agent.review_service import UnifiedReviewInbox

    inbox = UnifiedReviewInbox(root)
    items = inbox.list_all()
    pending = inbox.list_pending()
    deferred = inbox.list_deferred()
    completed = inbox.list_completed()
    critical = [
        item
        for item in items
        if item["category"] in {"delete_request", "connector_permission_change", "sensitive_document"}
        or item["risk_level"] in {"high", "critical", "destructive"}
    ]
    categories: dict[str, int] = {}
    for item in items:
        categories[item["category"]] = categories.get(item["category"], 0) + 1
    from secondbrain.notifications.review_notifications import TimeRules

    now = datetime.now(timezone.utc)
    rules = TimeRules()
    enriched = inbox.notification_items()

    def _age_seconds(value: str) -> float:
        try:
            parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except ValueError:
            return 0.0
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return max(0.0, (now - parsed).total_seconds())

    pending_enriched = [row for row in enriched if row.get("status") == "pending"]
    overdue = [row for row in pending_enriched if _age_seconds(row.get("created_at", "")) >= rules.overdue_after.total_seconds()]
    expiring_threshold = (rules.approval_expiration - rules.expiring_window).total_seconds()
    expiring = [
        row
        for row in pending_enriched
        if row.get("item_type") == "approval"
        and expiring_threshold <= _age_seconds(row.get("created_at", "")) < rules.approval_expiration.total_seconds()
    ]
    oldest_pending_age = int(max((_age_seconds(row.get("created_at", "")) for row in pending_enriched), default=0.0))
    notification_service = inbox.notification_service()
    notification_service.evaluate(enriched, now=now)
    open_notifications = notification_service.list_open(now=now)
    critical_notifications = [
        row for row in open_notifications if row.priority.value == "critical"
    ]
    overdue_notifications = notification_service.list_overdue(now=now)
    notification_count = len(open_notifications)
    return {
        "pending_reviews": len(inbox.reviews.list(status="pending")),
        "pending_approvals": len(inbox.approvals.list(status="pending")),
        "deferred_items": len(deferred),
        "critical_items": len(critical),
        "open_items": len(pending),
        "overdue_items": len(overdue),
        "expiring_items": len(expiring),
        "expiring_approvals": len(expiring),
        "notification_count": notification_count,
        "open_notifications": notification_count,
        "critical_notifications": len(critical_notifications),
        "overdue_notifications": len(overdue_notifications),
        "oldest_pending_age": oldest_pending_age,
        "inbox_summary": {
            "total": len(items),
            "pending": len(pending),
            "deferred": len(deferred),
            "completed": len(completed),
            "critical": len(critical),
            "categories": categories,
        },
    }


def _governance_metrics_status(root: Path) -> dict[str, Any]:
    from secondbrain.metrics.review_approval_metrics import ReviewApprovalMetrics

    return ReviewApprovalMetrics(root).dashboard_view()


def _action_surface() -> dict[str, Any]:
    return {
        "schema": "secondbrain.native.actions.v30_29",
        "mode": "voice_button_dispatch_with_audit_and_approval_queue",
        "confirmation_required_for": ["p1-rag-ingest-file", "p1-vector-index-repair", "memory-note"],
        "direct_actions": ["native-status", "native-chat-ask", "native-chat-search", "p1-rag-hybrid-search", "p1-rag-answer", "p1-production", "open-tab"],
        "audit_log": "runtime/native/action_audit.jsonl",
        "approval_queue": "runtime/native/approval_queue.jsonl",
        "german_examples": [
            "Jarvis Status",
            "Öffne Dokumente",
            "Suche Rechnung Telekom",
            "Frage was fehlt noch",
            "Repariere Index",
            "Merke Projektstand prüfen",
        ],
    }


def build_native_view_model(root: str | Path | None = None) -> dict[str, Any]:
    base = Path(root or Path.cwd()).resolve()
    bootstrap = bootstrap_status(base, repair=False)
    rag = _rag_status(base)
    provider = _provider_status(base)
    production = _production_status(base)
    memory = _memory_status(base)
    p1_panel = P1ControlPanel().render(provider if isinstance(provider, dict) else {})
    settings = _safe_call(lambda: RuntimeConfig(base).snapshot(), {"schema": "secondbrain.runtime_config.v1", "sections": []})
    voice_examples = _action_surface()["german_examples"]
    parser = GermanVoiceCommandParser()
    audit = native_audit_status(base, limit=10)
    chat = native_chat_status(base, limit=12)
    review_inbox = _safe_call(
        lambda: _review_inbox_status(base),
        {
            "pending_reviews": 0,
            "pending_approvals": 0,
            "deferred_items": 0,
            "critical_items": 0,
            "open_items": 0,
            "overdue_items": 0,
            "expiring_items": 0,
            "expiring_approvals": 0,
            "notification_count": 0,
            "open_notifications": 0,
            "critical_notifications": 0,
            "overdue_notifications": 0,
            "oldest_pending_age": 0,
            "inbox_summary": {"total": 0, "pending": 0, "deferred": 0, "completed": 0, "critical": 0},
        },
    )
    governance_metrics = _safe_call(
        lambda: _governance_metrics_status(base),
        {
            "open_items": 0,
            "critical_items": 0,
            "overdue_items": 0,
            "blocked_unsafe_actions": 0,
            "open_approvals": 0,
            "critical_approvals": 0,
            "overdue_reviews": 0,
            "average_decision_time": 0.0,
            "blocked_unsafe_executions": 0,
            "most_common_category": "",
            "trend_7d": 0,
            "trend_30d": 0,
        },
    )
    return {
        "schema": "secondbrain.native.view_model.v30_29",
        "ok": bool(bootstrap.get("ok")),
        "version": "30.29",
        "project_root": str(base),
        "python": sys.version.split()[0],
        "mode": "native_desktop_primary",
        "web_hud": "secondary_only",
        "bootstrap": bootstrap,
        "rag": rag,
        "provider": provider,
        "production": production,
        "memory": memory,
        "p1_control": p1_panel,
        "settings": settings,
        "config_status": settings.get("status", {"status": "unknown"}),
        "actions": _action_surface(),
        "audit": audit,
        "chat": chat,
        "pending_reviews": review_inbox["pending_reviews"],
        "pending_approvals": review_inbox["pending_approvals"],
        "deferred_items": review_inbox["deferred_items"],
        "critical_items": review_inbox["critical_items"],
        "inbox_summary": review_inbox["inbox_summary"],
        "open_items": review_inbox.get("open_items", 0),
        "overdue_items": review_inbox.get("overdue_items", 0),
        "expiring_items": review_inbox.get("expiring_items", 0),
        "notification_count": review_inbox.get("notification_count", 0),
        "open_notifications": review_inbox.get("open_notifications", 0),
        "critical_notifications": review_inbox.get("critical_notifications", 0),
        "overdue_notifications": review_inbox.get("overdue_notifications", 0),
        "oldest_pending_age": review_inbox.get("oldest_pending_age", 0),
        "expiring_approvals": review_inbox.get("expiring_approvals", 0),
        "governance_metrics": governance_metrics,
        "voice": {
            "language": "de-DE",
            "offline_intent_parser": True,
            "stt_tts_optional": True,
            "action_dispatcher": True,
            "examples": voice_examples,
            "sample_intents": [parser.parse(item).to_dict() for item in voice_examples],
        },
        "environment": {
            "DATABASE_URL": bool(os.environ.get("DATABASE_URL")),
            "SECONDBRAIN_EMBEDDING_PROVIDER": os.environ.get("SECONDBRAIN_EMBEDDING_PROVIDER", ""),
            "OPENAI_API_KEY": bool(os.environ.get("OPENAI_API_KEY")),
        },
    }
