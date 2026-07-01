from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from secondbrain.module_registry import ModuleRegistry
from secondbrain.p0_runtime import load_runtime_snapshot, p0_artifact_audit, p0_bootstrap, p0_contract, p0_doctor, p0_gate, p0_production_gate, p0_readiness, p0_report, p0_smoke
from secondbrain.p1_golden_retrieval import evaluate_golden_retrieval
from secondbrain.p1_production_gate import production_gate_with_golden
from secondbrain.p1_rag_runtime import P1RagRuntime
from secondbrain.p1_vector_provider_guard import audit_vector_provider
from secondbrain.p3_p1_store_bridge import mirror_project_p1_to_selected_store
from secondbrain.p3_pgvector_foundation import pgvector_readiness
from secondbrain.p3_rag_store import create_rag_store
from secondbrain.release.dependency_inventory import build_dependency_inventory
from secondbrain.release.repo_doctor import run_repo_doctor
from secondbrain.gui.launch import gui_command
from secondbrain.gui.bootstrap import write_bootstrap_report


def out(obj: Any) -> None:
    print(json.dumps(obj, indent=2, ensure_ascii=False, default=str))


def _first_command(argv: list[str]) -> str | None:
    skip_next = False
    for item in argv:
        if skip_next:
            skip_next = False
            continue
        if item in {"--project-root", "--profile", "--db-path"}:
            skip_next = True
            continue
        if item.startswith("--"):
            continue
        return item
    return None


def _strip_unhandled_global_options(argv: list[str], allowed: set[str]) -> list[str]:
    cleaned: list[str] = []
    i = 0
    while i < len(argv):
        item = argv[i]
        if item in {"--project-root", "--profile", "--db-path"} and item not in allowed:
            i += 2
            continue
        cleaned.append(item)
        i += 1
    return cleaned


def _repo_doctor_main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="secondbrain", description="SecondBrain repository doctor")
    parser.add_argument("cmd")
    parser.add_argument("--project-root", default=str(Path.cwd()))
    parser.add_argument("--execute-runtime-checks", action="store_true", help="execute lightweight launcher checks")
    parser.add_argument("--timeout", type=int, default=15, help="timeout per runtime command in seconds")
    parser.add_argument("--write-report", action="store_true")
    args, _ = parser.parse_known_args(argv)
    payload = run_repo_doctor(
        args.project_root,
        execute_runtime_checks=args.execute_runtime_checks,
        timeout_seconds=args.timeout,
        write_report=args.write_report,
    ).to_dict()
    out(payload)
    return 0 if payload.get("ok") else 1


def _dependency_inventory_main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="secondbrain", description="SecondBrain dependency inventory")
    parser.add_argument("cmd")
    parser.add_argument("--project-root", default=str(Path.cwd()))
    parser.add_argument("--write-report", action="store_true")
    args, _ = parser.parse_known_args(argv)
    payload = build_dependency_inventory(args.project_root, write_report=args.write_report).to_dict()
    out(payload)
    return 0 if payload.get("ok") else 1


def _mobile_main(argv: list[str] | None = None) -> int:
    from secondbrain.mobile_companion import MobileCompanionRuntime

    parser = argparse.ArgumentParser(prog="secondbrain", description="SecondBrain Mobile Companion launcher")
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--db-path", default=None)
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("mobile16-migrate")
    sub.add_parser("mobile16-status")
    sub.add_parser("mobile16-manifest")
    p = sub.add_parser("mobile16-pair-request"); p.add_argument("device_name"); p.add_argument("platform")
    p = sub.add_parser("mobile16-pair-approve"); p.add_argument("request_id")
    sub.add_parser("mobile16-pairing-requests")
    sub.add_parser("mobile16-devices")
    p = sub.add_parser("mobile16-capture"); p.add_argument("kind"); p.add_argument("payload_json"); p.add_argument("--device-id", default=None)
    p = sub.add_parser("mobile16-voice-note"); p.add_argument("text"); p.add_argument("--device-id", default=None)
    p = sub.add_parser("mobile16-camera-ocr"); p.add_argument("image_ref"); p.add_argument("--device-id", default=None)
    sub.add_parser("mobile16-offline-queue")
    sub.add_parser("mobile16-offline-replay")
    p = sub.add_parser("mobile16-push"); p.add_argument("title"); p.add_argument("body"); p.add_argument("--device-id", default=None); p.add_argument("--priority", default="normal")
    sub.add_parser("mobile16-push-outbox")
    sub.add_parser("mobile16-push-deliver")
    sub.add_parser("mobile16-widgets")
    p = sub.add_parser("mobile16-widget-enable"); p.add_argument("widget_id"); p.add_argument("enabled", choices=["true", "false"])
    p = sub.add_parser("mobile16-sync"); p.add_argument("--device-id", default=None)
    sub.add_parser("mobile16-sync-runs")
    p = sub.add_parser("mobile16-session-create"); p.add_argument("title"); p.add_argument("--device-id", default=None)
    sub.add_parser("mobile16-sessions")

    args = parser.parse_args(argv)
    rt = MobileCompanionRuntime(args.project_root, args.db_path)
    if args.cmd == "mobile16-migrate": out(rt.migrate())
    elif args.cmd == "mobile16-status": out(rt.status())
    elif args.cmd == "mobile16-manifest": out(rt.app_manifest())
    elif args.cmd == "mobile16-pair-request": out(rt.pair_request(args.device_name, args.platform))
    elif args.cmd == "mobile16-pair-approve": out(rt.approve_pairing(args.request_id))
    elif args.cmd == "mobile16-pairing-requests": out(rt.pairing_requests())
    elif args.cmd == "mobile16-devices": out(rt.devices())
    elif args.cmd == "mobile16-capture": out(rt.capture(args.kind, json.loads(args.payload_json), args.device_id))
    elif args.cmd == "mobile16-voice-note": out(rt.voice_note(args.text, args.device_id))
    elif args.cmd == "mobile16-camera-ocr": out(rt.camera_ocr(args.image_ref, args.device_id))
    elif args.cmd == "mobile16-offline-queue": out(rt.offline_queue())
    elif args.cmd == "mobile16-offline-replay": out(rt.replay_offline())
    elif args.cmd == "mobile16-push": out(rt.push(args.title, args.body, args.device_id, args.priority))
    elif args.cmd == "mobile16-push-outbox": out(rt.push_outbox())
    elif args.cmd == "mobile16-push-deliver": out(rt.deliver_push())
    elif args.cmd == "mobile16-widgets": out(rt.widgets())
    elif args.cmd == "mobile16-widget-enable": out(rt.widget_enable(args.widget_id, args.enabled == "true"))
    elif args.cmd == "mobile16-sync": out(rt.sync(args.device_id))
    elif args.cmd == "mobile16-sync-runs": out(rt.sync_runs())
    elif args.cmd == "mobile16-session-create": out(rt.session_create(args.title, args.device_id))
    elif args.cmd == "mobile16-sessions": out(rt.sessions())
    else: return 2
    return 0


def _local_status(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="secondbrain")
    parser.add_argument("--project-root", default=str(Path.cwd()))
    parser.add_argument("--profile", default=None)
    parser.add_argument("cmd", nargs="?")
    parser.add_argument("module", nargs="?")
    parser.add_argument("--runtime", action="store_true", help="execute lightweight runtime status checks")
    args, _ = parser.parse_known_args(argv)
    registry = ModuleRegistry()
    project_root = Path(args.project_root).resolve()
    import_health = registry.import_health()
    runtime_health = registry.runtime_health(project_root, args.profile) if args.runtime or args.cmd in {"health", "module-health"} else None
    selected = None
    if args.module:
        try:
            selected = registry.get(args.module).to_dict()
        except KeyError:
            out({"status": "error", "error": f"unknown module: {args.module}", "known_modules": registry.keys()})
            return 2
    effective_ok = import_health["ok"] and (runtime_health is None or runtime_health["ok"])
    payload = {
        "status": "ok" if effective_ok else "degraded",
        "project_root": str(project_root),
        "profile": args.profile or "default",
        "command_index": registry.command_index(),
        "config": load_runtime_snapshot(project_root, args.profile).to_dict(),
        "registry": registry.list(),
        "selected_module": selected,
        "import_health": import_health,
    }
    if runtime_health is not None:
        payload["runtime_health"] = runtime_health
    out(payload)
    return 0 if effective_ok else 1


def _p3_pgvector_main(raw: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="secondbrain")
    parser.add_argument("--project-root", default=str(Path.cwd()))
    parser.add_argument("cmd")
    parser.add_argument("--write-report", action="store_true")
    parser.add_argument("--live", action="store_true", help="check live PostgreSQL/pgvector connectivity")
    parser.add_argument("--apply", action="store_true", help="apply the pgvector schema SQL to the configured DSN")
    args, _ = parser.parse_known_args(raw)
    payload = pgvector_readiness(args.project_root, write_report=args.write_report, live=args.live, apply=args.apply)
    out(payload)
    return 0 if payload.get("ok") else 1


def _p3_rag_store_main(raw: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="secondbrain")
    parser.add_argument("--project-root", default=str(Path.cwd()))
    parser.add_argument("cmd")
    args, _ = parser.parse_known_args(raw)
    store = create_rag_store(args.project_root)
    payload = store.status()
    out(payload)
    return 0 if payload.get("ok") else 1


def _p3_p1_store_bridge_main(raw: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="secondbrain")
    parser.add_argument("--project-root", default=str(Path.cwd()))
    parser.add_argument("cmd")
    parser.add_argument("--write-report", action="store_true")
    args, _ = parser.parse_known_args(raw)
    payload = mirror_project_p1_to_selected_store(args.project_root, write_report=args.write_report)
    out(payload)
    return 0 if payload.get("ok") else 1


def main(argv: list[str] | None = None) -> int:
    raw = list(sys.argv[1:] if argv is None else argv)
    cmd = _first_command(raw)
    if cmd is None:
        return gui_command(["gui", "--project-root", str(Path.cwd())])
    if cmd == "bootstrap":
        out(write_bootstrap_report(Path.cwd(), repair=True))
        return 0
    if cmd == "repo-doctor":
        return _repo_doctor_main(raw)
    if cmd == "dependency-inventory":
        return _dependency_inventory_main(raw)
    if cmd == "p3-pgvector-readiness":
        return _p3_pgvector_main(raw)
    if cmd == "p3-rag-store-status":
        return _p3_rag_store_main(raw)
    if cmd == "p3-p1-store-bridge":
        return _p3_p1_store_bridge_main(raw)
    if cmd in {"p1-rag-status", "p1-rag-ingest-text", "p1-rag-ingest-file", "p1-rag-search", "p1-rag-vector-search", "p1-rag-hybrid-search", "p1-rag-answer", "p1-rag-sources", "p1-rag-explain", "p1-rag-validate", "p1-rag-quality", "p1-rag-reindex", "p1-embedding-status", "p1-vector-provider-audit", "p1-retrieval-benchmark", "p1-retrieval-metrics", "p1-golden-eval", "p1-production", "p1-gate"}:
        parser = argparse.ArgumentParser(prog="secondbrain")
        parser.add_argument("--project-root", default=str(Path.cwd()))
        parser.add_argument("--profile", default=None)
        parser.add_argument("cmd")
        parser.add_argument("args", nargs="*")
        parser.add_argument("--source", default="manual")
        parser.add_argument("--title", default=None)
        parser.add_argument("--limit", type=int, default=5)
        parser.add_argument("--write-report", action="store_true")
        args, _ = parser.parse_known_args(raw)
        rt = P1RagRuntime(args.project_root, args.profile)
        if cmd == "p1-rag-status":
            payload = rt.status()
        elif cmd == "p1-rag-ingest-text":
            payload = rt.ingest_text(" ".join(args.args), args.source, args.title)
        elif cmd == "p1-rag-ingest-file":
            payload = rt.ingest_file(args.args[0] if args.args else "", args.source, args.title)
        elif cmd == "p1-rag-search":
            payload = rt.search(" ".join(args.args), args.limit)
        elif cmd == "p1-rag-vector-search":
            payload = rt.vector_search(" ".join(args.args), args.limit)
        elif cmd == "p1-rag-hybrid-search":
            payload = rt.hybrid_search(" ".join(args.args), args.limit)
        elif cmd == "p1-rag-reindex":
            payload = rt.reindex_vectors(write_report=args.write_report)
        elif cmd == "p1-embedding-status":
            payload = rt.embedding_status()
        elif cmd == "p1-vector-provider-audit":
            payload = audit_vector_provider(rt, write_report=args.write_report)
        elif cmd == "p1-retrieval-benchmark":
            payload = rt.retrieval_benchmark(write_report=args.write_report)
        elif cmd == "p1-retrieval-metrics":
            payload = rt.retrieval_metrics(write_report=args.write_report)
        elif cmd == "p1-golden-eval":
            payload = evaluate_golden_retrieval(rt, args.project_root, write_report=args.write_report)
        elif cmd == "p1-production":
            payload = production_gate_with_golden(rt, args.project_root, write_report=args.write_report)
        elif cmd == "p1-rag-answer":
            payload = rt.answer(" ".join(args.args), args.limit)
        elif cmd == "p1-rag-sources":
            payload = rt.sources()
        elif cmd == "p1-rag-explain":
            payload = rt.explain(" ".join(args.args), args.limit)
        elif cmd == "p1-rag-validate":
            payload = rt.validate_index(write_report=args.write_report)
        elif cmd == "p1-rag-quality":
            payload = rt.quality_report(" ".join(args.args) or "Jarvis RAG Quellen", args.limit, write_report=args.write_report)
        else:
            payload = rt.gate(write_report=args.write_report)
        out(payload)
        return 0 if payload.get("ok") else 1
    if cmd in {"p0-doctor", "p0-gate", "p0-report", "p0-smoke", "p0-contract", "p0-readiness", "p0-bootstrap", "p0-production", "p0-audit"}:
        parser = argparse.ArgumentParser(prog="secondbrain")
        parser.add_argument("--project-root", default=str(Path.cwd()))
        parser.add_argument("--profile", default=None)
        parser.add_argument("cmd")
        parser.add_argument("--write-report", action="store_true")
        args, _ = parser.parse_known_args(raw)
        if cmd == "p0-gate":
            payload = p0_gate(args.project_root, args.profile, write_report=args.write_report)
        elif cmd == "p0-report":
            payload = p0_report(args.project_root, args.profile)
        elif cmd == "p0-smoke":
            payload = p0_smoke(args.project_root, args.profile, write_report=args.write_report)
        elif cmd == "p0-contract":
            payload = p0_contract(args.project_root, args.profile, write_report=args.write_report)
        elif cmd == "p0-readiness":
            payload = p0_readiness(args.project_root, args.profile, write_report=args.write_report)
        elif cmd == "p0-bootstrap":
            payload = p0_bootstrap(args.project_root, args.profile, write_report=args.write_report)
        elif cmd == "p0-production":
            payload = p0_production_gate(args.project_root, args.profile, write_report=args.write_report)
        elif cmd == "p0-audit":
            payload = p0_artifact_audit(args.project_root, args.profile, write_report=args.write_report)
        else:
            payload = p0_doctor(args.project_root, args.profile)
        out(payload)
        return 0 if payload.get("ok") else 1
    if cmd in {"dashboard-center", "dashboard-center-gui", "dashboard-center-status", "dashboard-center-snapshot", "dashboard-center-activity", "dashboard-center-record"}:
        from secondbrain.native.dashboard_center.cli import main as dashboard_center_main
        return dashboard_center_main(raw)
    if cmd in {"layout-center", "layout-center-gui", "layout-status", "layout-list", "layout-load", "layout-activate", "layout-save", "layout-reset", "layout-export", "layout-import", "layout-history"}:
        from secondbrain.native.layout_center.cli import main as layout_center_main
        return layout_center_main(raw)
    if cmd in {"settings-center", "settings-center-gui", "settings-center-status", "settings-center-snapshot", "settings-center-write-defaults", "settings-center-set", "settings-center-history"}:
        from secondbrain.native.settings_center.cli import main as settings_center_main
        return settings_center_main(raw)
    if cmd in {"ai-workspace", "ai-workspace-gui", "ai-workspace-status", "ai-workspace-snapshot", "ai-workspace-navigation", "ai-workspace-activity", "ai-workspace-record"}:
        from secondbrain.native.ai_workspace.cli import main as ai_workspace_main
        return ai_workspace_main(raw)
    if cmd in {"gui", "gui-start", "gui-open", "gui-status", "gui-doctor", "gui-shortcuts", "gui-bootstrap", "jarvis", "desktop-gui", "desktop16-gui"}:
        return gui_command(raw)
    if cmd == "command-index":
        out(ModuleRegistry().command_index())
        return 0
    if cmd in {"status", "health", "module-status", "module-health", "modules"}:
        return _local_status(raw)
    if cmd.startswith("mobile16-"):
        return _mobile_main(raw)
    try:
        from secondbrain.launcher_runtime_v126 import main as runtime_main
        return runtime_main(_strip_unhandled_global_options(raw, {"--project-root", "--profile"}))
    except SystemExit as exc:
        return int(exc.code or 0)


if __name__ == "__main__":
    raise SystemExit(main())
