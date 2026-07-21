from __future__ import annotations

import argparse
import json
import os
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
from secondbrain.env_loader import load_env_file
from secondbrain.version import version_info as _version_info, get_version as _get_version
from secondbrain.voice.ports import (
    Audio, AudioClip, TranscriptSegment, Transcript,
    SttEngine, StreamingStt, TtsEngine, MicrophoneSource,
    WakeWordDetector, VoiceActivityDetector, StreamingTts,
)
from secondbrain.voice.transcribe import VoiceTranscriber, transcript_to_item
from secondbrain.voice.speaker import (
    SpeakerId, SpeakerEmbedder, SpeakerProfileStore, SpeakerMatcher,
    cosine as speaker_cosine,
)
from secondbrain.voice.memory import VoiceMemory, VoiceMemoryStore
from secondbrain.voice.streaming import StreamingSttSession
from secondbrain.voice.conversation import ConversationController, State as ConversationState
from secondbrain.voice.commands import (
    VoiceCommandRouter as RealtimeVoiceCommandRouter,
    Intent as RealtimeIntent,
)

__version__ = _get_version()
from secondbrain.p1_embedding_config import evaluate_embedding_config
from secondbrain.p1_provider_health import evaluate_embedding_provider_health
from secondbrain.p1_rag_migration import migrate_sqlite_to_selected_store
from secondbrain.p1_vector_provider_guard import repair_vector_index

try:
    __all__
except NameError:
    __all__ = []

__all__ += [
    "Audio", "AudioClip", "TranscriptSegment", "Transcript",
    "SttEngine", "StreamingStt", "TtsEngine", "MicrophoneSource",
    "WakeWordDetector", "VoiceActivityDetector", "StreamingTts",
    "VoiceTranscriber", "transcript_to_item",
    "SpeakerId", "SpeakerEmbedder", "SpeakerProfileStore", "SpeakerMatcher", "speaker_cosine",
    "VoiceMemory", "VoiceMemoryStore", "StreamingSttSession",
    "ConversationController", "ConversationState",
    "RealtimeVoiceCommandRouter", "RealtimeIntent",
]


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
    parser.add_argument("--timeout", type=int, default=60, help="timeout per runtime command in seconds")
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



def _rc_gate_main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="secondbrain", description="SecondBrain release-candidate gate")
    parser.add_argument("cmd")
    parser.add_argument("project_root", nargs="?", default=str(Path.cwd()))
    parser.add_argument("--project-root", dest="project_root_option", default=None)
    parser.add_argument("--target-version", default=None)
    parser.add_argument("--write-report", action="store_true")
    args, _ = parser.parse_known_args(argv)
    root = args.project_root_option or args.project_root
    from secondbrain.release.rc_gate import Verdict, run_rc_gate, write_artifacts
    report = run_rc_gate(root, target_version=args.target_version)
    if args.write_report:
        write_artifacts(report, root)
    out(report)
    return 0 if report["verdict"] != Verdict.BLOCKED.value else 2


def _review_approval_gate_main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="secondbrain", description="Review and approval end-to-end gate")
    parser.add_argument("cmd")
    parser.add_argument("project_root", nargs="?", default=str(Path.cwd()))
    parser.add_argument("--project-root", dest="project_root_option", default=None)
    args, _ = parser.parse_known_args(argv)
    from secondbrain.agent.review_approval_gate import BLOCKED, run_review_approval_gate

    report = run_review_approval_gate(args.project_root_option or args.project_root)
    out(report)
    return 2 if report["status"] == BLOCKED else 0


def _review_approval_release_gate_main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        prog="secondbrain",
        description="Production certification gate for review and approval governance",
    )
    parser.add_argument("cmd")
    parser.add_argument("project_root", nargs="?", default=str(Path.cwd()))
    parser.add_argument("--project-root", dest="project_root_option", default=None)
    parser.add_argument("--no-write-report", action="store_true")
    args, _ = parser.parse_known_args(argv)
    from secondbrain.agent.review_approval_gate import BLOCKED
    from secondbrain.agent.review_approval_release_gate import run_review_approval_release_gate

    report = run_review_approval_release_gate(
        args.project_root_option or args.project_root,
        write_report=not args.no_write_report,
    )
    out(report)
    return 2 if report["overall_status"] == BLOCKED else 0


def _connector_e2e_gate_main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="secondbrain", description="Safe mail and calendar E2E gate")
    parser.add_argument("cmd")
    parser.add_argument("project_root", nargs="?", default=str(Path.cwd()))
    parser.add_argument("--project-root", dest="project_root_option", default=None)
    parser.add_argument("--no-write-report", action="store_true")
    args, _ = parser.parse_known_args(argv)
    from secondbrain.release.connector_e2e_gate import BLOCKED, run_connector_e2e_gate
    report = run_connector_e2e_gate(args.project_root_option or args.project_root,
                                    write_report=not args.no_write_report)
    out(report)
    return 2 if report["status"] == BLOCKED else 0


def _provider_live_gate_main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="secondbrain", description="Opt-in AI provider live gate")
    parser.add_argument("cmd")
    parser.add_argument("project_root", nargs="?", default=str(Path.cwd()))
    parser.add_argument("--project-root", dest="project_root_option", default=None)
    parser.add_argument("--no-write-report", action="store_true")
    args, _ = parser.parse_known_args(argv)
    from secondbrain.release.provider_live_gate import BLOCKED, run_provider_live_gate
    report = run_provider_live_gate(args.project_root_option or args.project_root,
                                    write_report=not args.no_write_report)
    out(report)
    return 2 if report["status"] == BLOCKED else 0


def _postgres_live_gate_main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        prog="secondbrain",
        description="PostgreSQL and pgvector live gate (requires TEST_DATABASE_URL)",
    )
    parser.add_argument("cmd")
    parser.add_argument("project_root", nargs="?", default=str(Path.cwd()))
    parser.add_argument("--project-root", dest="project_root_option", default=None)
    parser.add_argument("--no-write-report", action="store_true")
    args, _ = parser.parse_known_args(argv)
    from secondbrain.release.postgres_live_gate import BLOCKED, run_postgres_live_gate
    report = run_postgres_live_gate(args.project_root_option or args.project_root,
                                    write_report=not args.no_write_report)
    out(report)
    return 2 if report["status"] == BLOCKED else 0


def _security_gate_main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        prog="secondbrain",
        description="Local prompt, RAG and document parser security gate",
    )
    parser.add_argument("cmd")
    parser.add_argument("project_root", nargs="?", default=str(Path.cwd()))
    parser.add_argument("--project-root", dest="project_root_option", default=None)
    parser.add_argument("--no-write-report", action="store_true")
    args, _ = parser.parse_known_args(argv)
    from secondbrain.security_gate_v3095 import PASS, run_security_gate

    report = run_security_gate(
        args.project_root_option or args.project_root,
        write_report=not args.no_write_report,
    )
    out(report)
    return 0 if report["status"] == PASS else 2


def _backup_gate_main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="secondbrain", description="Backup and restore release gate")
    parser.add_argument("cmd")
    parser.add_argument("--project-root", default=str(Path.cwd()))
    args, _ = parser.parse_known_args(argv)
    from secondbrain.backup_gate_v3096 import BLOCKED, run_backup_gate
    report = run_backup_gate(args.project_root)
    out(report)
    return 2 if report["status"] == BLOCKED else 0


def _rag_eval_main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="secondbrain", description="Production RAG evaluation")
    parser.add_argument("cmd")
    parser.add_argument("--project-root", default=str(Path.cwd()))
    args, _ = parser.parse_known_args(argv)
    runtime = P1RagRuntime(args.project_root)
    report = production_gate_with_golden(runtime, args.project_root, write_report=True)
    out(report)
    return 0 if report.get("ok") else 2


def _ga_readiness_gate_main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="secondbrain", description="General availability readiness gate")
    parser.add_argument("cmd")
    parser.add_argument("--project-root", default=str(Path.cwd()))
    args, _ = parser.parse_known_args(argv)
    from secondbrain.release.ga_readiness import BLOCKED, run_ga_readiness_gate
    report = run_ga_readiness_gate(args.project_root)
    out(report)
    return 2 if report["overall_status"] == BLOCKED else 0


def _mobile_main(argv: list[str] | None = None) -> int:
    from secondbrain.mobile_companion import MobileCompanionRuntime

    parser = argparse.ArgumentParser(prog="secondbrain", description="SecondBrain Mobile Companion launcher")
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--db-path", default=None)
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("mobile16-migrate")
    sub.add_parser("mobile16-status")
    sub.add_parser("mobile16-manifest")
    p = sub.add_parser("mobile16-pair-request")
    p.add_argument("device_name")
    p.add_argument("platform")
    p = sub.add_parser("mobile16-pair-approve")
    p.add_argument("request_id")
    sub.add_parser("mobile16-pairing-requests")
    sub.add_parser("mobile16-devices")
    p = sub.add_parser("mobile16-capture")
    p.add_argument("kind")
    p.add_argument("payload_json")
    p.add_argument("--device-id", default=None)
    p = sub.add_parser("mobile16-voice-note")
    p.add_argument("text")
    p.add_argument("--device-id", default=None)
    p = sub.add_parser("mobile16-camera-ocr")
    p.add_argument("image_ref")
    p.add_argument("--device-id", default=None)
    sub.add_parser("mobile16-offline-queue")
    sub.add_parser("mobile16-offline-replay")
    p = sub.add_parser("mobile16-push")
    p.add_argument("title")
    p.add_argument("body")
    p.add_argument("--device-id", default=None)
    p.add_argument("--priority", default="normal")
    sub.add_parser("mobile16-push-outbox")
    sub.add_parser("mobile16-push-deliver")
    sub.add_parser("mobile16-widgets")
    p = sub.add_parser("mobile16-widget-enable")
    p.add_argument("widget_id")
    p.add_argument("enabled", choices=["true", "false"])
    p = sub.add_parser("mobile16-sync")
    p.add_argument("--device-id", default=None)
    sub.add_parser("mobile16-sync-runs")
    p = sub.add_parser("mobile16-session-create")
    p.add_argument("title")
    p.add_argument("--device-id", default=None)
    sub.add_parser("mobile16-sessions")

    args = parser.parse_args(argv)
    rt = MobileCompanionRuntime(args.project_root, args.db_path)
    if args.cmd == "mobile16-migrate":
        out(rt.migrate())
    elif args.cmd == "mobile16-status":
        out(rt.status())
    elif args.cmd == "mobile16-manifest":
        out(rt.app_manifest())
    elif args.cmd == "mobile16-pair-request":
        out(rt.pair_request(args.device_name, args.platform))
    elif args.cmd == "mobile16-pair-approve":
        out(rt.approve_pairing(args.request_id))
    elif args.cmd == "mobile16-pairing-requests":
        out(rt.pairing_requests())
    elif args.cmd == "mobile16-devices":
        out(rt.devices())
    elif args.cmd == "mobile16-capture":
        out(rt.capture(args.kind, json.loads(args.payload_json), args.device_id))
    elif args.cmd == "mobile16-voice-note":
        out(rt.voice_note(args.text, args.device_id))
    elif args.cmd == "mobile16-camera-ocr":
        out(rt.camera_ocr(args.image_ref, args.device_id))
    elif args.cmd == "mobile16-offline-queue":
        out(rt.offline_queue())
    elif args.cmd == "mobile16-offline-replay":
        out(rt.replay_offline())
    elif args.cmd == "mobile16-push":
        out(rt.push(args.title, args.body, args.device_id, args.priority))
    elif args.cmd == "mobile16-push-outbox":
        out(rt.push_outbox())
    elif args.cmd == "mobile16-push-deliver":
        out(rt.deliver_push())
    elif args.cmd == "mobile16-widgets":
        out(rt.widgets())
    elif args.cmd == "mobile16-widget-enable":
        out(rt.widget_enable(args.widget_id, args.enabled == "true"))
    elif args.cmd == "mobile16-sync":
        out(rt.sync(args.device_id))
    elif args.cmd == "mobile16-sync-runs":
        out(rt.sync_runs())
    elif args.cmd == "mobile16-session-create":
        out(rt.session_create(args.title, args.device_id))
    elif args.cmd == "mobile16-sessions":
        out(rt.sessions())
    else:
        return 2
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



def _m365_main(argv: list[str]) -> int:
    from secondbrain.connectors.microsoft.config import GraphConfigError
    from secondbrain.connectors.microsoft.runtime import M365Runtime

    parser = argparse.ArgumentParser(prog="secondbrain")
    parser.add_argument("cmd")
    parser.add_argument("--project-root", default=str(Path.cwd()))
    parser.add_argument("--resources", default=None, help="comma list e.g. mail,calendar,todo")
    parser.add_argument("--no-wait", action="store_true", help="m365-login: return device code without polling")
    parser.add_argument("--approve", default=None, help="approve a pending write by request id")
    args, _ = parser.parse_known_args(argv)

    try:
        runtime = M365Runtime(args.project_root)
    except GraphConfigError as exc:
        out({"status": "config_error", "message": str(exc)})
        return 2

    resources = [r.strip() for r in args.resources.split(",") if r.strip()] if args.resources else None

    if args.cmd == "m365-login":
        result = runtime.login(printer=lambda m: print(m, file=sys.stderr), wait=not args.no_wait)
        out(result)
        return 0 if result.get("status") in {"ok", "pending"} else 1
    if args.cmd == "m365-sync":
        out(runtime.sync(resources))
        return 0
    if args.cmd == "m365-status":
        if args.approve:
            out(runtime.approve(args.approve))
            return 0
        out(runtime.status())
        return 0
    if args.cmd == "m365-disconnect":
        out(runtime.disconnect())
        return 0
    out({"status": "unknown_command", "cmd": args.cmd})
    return 2


def _google_main(argv: list[str]) -> int:
    from secondbrain.connectors.scaffold.cli import run_connector_cli
    from secondbrain.connectors.google.config import GoogleConfigError
    from secondbrain.connectors.google.runtime import GoogleRuntime
    return run_connector_cli("google", lambda root: GoogleRuntime(root), argv, out=out, config_error=GoogleConfigError)


def _vision_main(argv: list[str]) -> int:
    from secondbrain.vision.pipeline import VisionPipeline
    parser = argparse.ArgumentParser(prog="secondbrain")
    parser.add_argument("cmd")
    parser.add_argument("path", nargs="?", default=None)
    parser.add_argument("--lang", default="eng")
    args, _ = parser.parse_known_args(argv)
    if args.cmd == "vision-ocr":
        if not args.path:
            out({"status": "error", "message": "usage: vision-ocr <image-path> [--lang eng]"})
            return 2
        try:
            from secondbrain.vision.engines.tesseract_ocr import TesseractOcrEngine
            pipeline = VisionPipeline(TesseractOcrEngine())
            out({"status": "ok", **pipeline.process_path(args.path, lang=args.lang)})
            return 0
        except RuntimeError as exc:
            out({"status": "engine_unavailable", "message": str(exc)})
            return 2
    out({"status": "unknown_command", "cmd": args.cmd})
    return 2


def _desktop_main(argv: list[str]) -> int:
    from secondbrain.vision.desktop import DesktopAnalyzer
    from secondbrain.vision.classify import HeuristicTextClassifier
    from secondbrain.vision.ports import Image
    parser = argparse.ArgumentParser(prog="secondbrain")
    parser.add_argument("cmd")
    parser.add_argument("--image", default=None, help="analyze an image file instead of the live screen")
    parser.add_argument("--lang", default="eng")
    args, _ = parser.parse_known_args(argv)
    if args.cmd != "desktop-analyze":
        out({"status": "unknown_command", "cmd": args.cmd})
        return 2
    try:
        from secondbrain.vision.engines.tesseract_ocr import TesseractOcrEngine
        ocr = TesseractOcrEngine()
        analyzer = DesktopAnalyzer(ocr, text_classifier=HeuristicTextClassifier())
        if args.image:
            result = analyzer.analyze_image(Image.from_path(args.image), lang=args.lang)
        else:
            from secondbrain.vision.engines.screen_mss import MssScreenSource
            analyzer.screen = MssScreenSource()
            result = analyzer.analyze_screen(lang=args.lang)
        out({"status": "ok", **result})
        return 0
    except RuntimeError as exc:
        out({"status": "engine_unavailable", "message": str(exc)})
        return 2


def _diagram_main(argv: list[str]) -> int:
    from secondbrain.vision.diagram import DiagramAnalyzer
    from secondbrain.vision.ports import Image
    parser = argparse.ArgumentParser(prog="secondbrain")
    parser.add_argument("cmd")
    parser.add_argument("--image", required=False, default=None)
    parser.add_argument("--model", default=None, help="path to ONNX detection model")
    parser.add_argument("--labels", default="node,arrow", help="comma-separated class labels")
    parser.add_argument("--lang", default="eng")
    args, _ = parser.parse_known_args(argv)
    if args.cmd != "diagram-analyze":
        out({"status": "unknown_command", "cmd": args.cmd})
        return 2
    if not args.image or not args.model:
        out({"status": "error", "message": "usage: diagram-analyze --image <path> --model <onnx> [--labels node,arrow]"})
        return 2
    try:
        from secondbrain.vision.engines.onnx_detector import OnnxObjectDetector
        from secondbrain.vision.engines.tesseract_ocr import TesseractOcrEngine
        detector = OnnxObjectDetector(args.model, args.labels.split(","))
        analyzer = DiagramAnalyzer(detector, TesseractOcrEngine())
        out({"status": "ok", **analyzer.analyze_image(Image.from_path(args.image), lang=args.lang)})
        return 0
    except RuntimeError as exc:
        out({"status": "engine_unavailable", "message": str(exc)})
        return 2


def _voice_main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="secondbrain")
    parser.add_argument("cmd")
    parser.add_argument("--audio", default=None)
    parser.add_argument("--text", default=None)
    parser.add_argument("--model", default="base")
    parser.add_argument("--voice-model", default=None)
    parser.add_argument("--out", default="out.wav")
    parser.add_argument("--lang", default=None)
    parser.add_argument("--speaker", default=None)
    parser.add_argument("--label", default=None)
    parser.add_argument("--project-root", default=str(Path.cwd()))
    args, _ = parser.parse_known_args(argv)
    if args.cmd == "voice-transcribe":
        if not args.audio:
            out({"status": "error", "message": "usage: voice-transcribe --audio <path> [--model base] [--lang de]"})
            return 2
        try:
            from secondbrain.voice.engines.whisper_stt import WhisperSttEngine
            from secondbrain.voice.transcribe import VoiceTranscriber
            tr = VoiceTranscriber(WhisperSttEngine(args.model))
            out({"status": "ok", **tr.transcribe_path(args.audio, lang=args.lang)})
            return 0
        except RuntimeError as exc:
            out({"status": "engine_unavailable", "message": str(exc)})
            return 2
    if args.cmd == "voice-say":
        if not args.text or not args.voice_model:
            out({"status": "error", "message": "usage: voice-say --text <t> --voice-model <onnx> [--out out.wav]"})
            return 2
        try:
            from secondbrain.voice.engines.piper_tts import PiperTtsEngine
            clip = PiperTtsEngine(args.voice_model).synthesize(args.text)
            path = clip.write(args.out)
            out({"status": "ok", "out": path, "bytes": len(clip.data), "sample_rate": clip.sample_rate})
            return 0
        except RuntimeError as exc:
            out({"status": "engine_unavailable", "message": str(exc)})
            return 2
    if args.cmd in {"voice-enroll", "voice-identify"}:
        from secondbrain.voice.speaker import SpeakerProfileStore, SpeakerMatcher
        from secondbrain.voice.ports import Audio
        store = SpeakerProfileStore(str(Path(args.project_root) / "runtime/voice/speakers.json"))
        try:
            from secondbrain.voice.engines.resemblyzer_embedder import ResemblyzerEmbedder
            matcher = SpeakerMatcher(ResemblyzerEmbedder(), store)
        except RuntimeError as exc:
            out({"status": "engine_unavailable", "message": str(exc)})
            return 2
        if args.cmd == "voice-enroll":
            if not args.speaker or not args.audio:
                out({"status": "error", "message": "usage: voice-enroll --speaker <id> --label <name> --audio <path>"})
                return 2
            emb = matcher.enroll(args.speaker, args.label or args.speaker, [Audio.from_path(args.audio)])
            out({"status": "ok", "speaker": args.speaker, "embedding_dim": len(emb)})
            return 0
        sid = matcher.identify(Audio.from_path(args.audio))
        out({"status": "ok", "speaker": sid.id, "label": sid.label, "score": sid.score})
        return 0
    if args.cmd == "voice-command":
        from secondbrain.voice.commands import VoiceCommandRouter
        if not args.text:
            out({"status": "error", "message": "usage: voice-command --text <utterance>"})
            return 2
        router = VoiceCommandRouter(agent=lambda t: f"agent received: {t}")
        out({"status": "ok", **router.handle(args.text)})
        return 0
    if args.cmd == "voice-converse":
        missing = []
        try:
            from secondbrain.voice.engines.openwakeword_detector import OpenWakeWordDetector  # noqa: F401
        except Exception:
            missing.append("openwakeword")
        for mod in ("webrtcvad", "faster_whisper", "piper"):
            try:
                __import__(mod)
            except Exception:
                missing.append(mod)
        if missing:
            out({"status": "engine_unavailable", "missing": missing,
                 "message": "install requirements-voice.txt; the live duplex loop also needs a microphone stack"})
            return 2
        out({"status": "ready", "message": "conversation stack available; start the live loop on a machine with a microphone"})
        return 0
    out({"status": "unknown_command", "cmd": args.cmd})
    return 2


def _first_project_root(argv: list[str]) -> str:
    for i, item in enumerate(argv):
        if item == "--project-root" and i + 1 < len(argv):
            return argv[i + 1]
    return str(Path.cwd())


def _db_main(argv: list[str]) -> int:
    from secondbrain.storage.db_policy import DatabaseStartupError
    from secondbrain.storage.db_provider import DatabaseProvider
    parser = argparse.ArgumentParser(prog="secondbrain")
    parser.add_argument("cmd")
    args, _ = parser.parse_known_args(argv)
    try:
        provider = DatabaseProvider.start()
    except DatabaseStartupError as exc:
        out({"status": "db_unavailable", "message": str(exc)})
        return 3
    if args.cmd == "db-validate":
        out({"status": "ok", **provider.runtime.health()})
        return 0
    if args.cmd == "db-status":
        out({"status": "ok", **provider.health()})
        return 0
    if args.cmd == "db-migrate":
        out({"status": "ok", "migrate": provider.migrate()})
        return 0
    out({"status": "unknown_command", "cmd": args.cmd})
    return 2


def _vector_store_from_env():
    from secondbrain.storage.db_provider import DatabaseProvider
    from secondbrain.storage.vector_store import SqliteVectorStore, PgVectorStore
    provider = DatabaseProvider.start()
    rt = provider.runtime
    if rt.backend == "postgresql":
        return PgVectorStore(rt.executor.database), rt
    return SqliteVectorStore(rt.url), rt


def _vector_main(argv: list[str]) -> int:
    from secondbrain.storage.db_policy import DatabaseStartupError
    parser = argparse.ArgumentParser(prog="secondbrain")
    parser.add_argument("cmd")
    parser.add_argument("--count", type=int, default=1000)
    parser.add_argument("--dim", type=int, default=64)
    parser.add_argument("--queries", type=int, default=20)
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--method", default="hnsw")
    parser.add_argument("--metric", default="cosine")
    parser.add_argument("--from", dest="source_url", default=None)
    args, _ = parser.parse_known_args(argv)
    try:
        store, rt = _vector_store_from_env()
    except DatabaseStartupError as exc:
        out({"status": "db_unavailable", "message": str(exc)})
        return 3
    if args.cmd == "vector-benchmark":
        from secondbrain.storage.vector_benchmark import run_benchmark
        out({"status": "ok", **run_benchmark(store, count=args.count, dim=args.dim,
                                             queries=args.queries, limit=args.limit)})
        return 0
    if args.cmd == "vector-reindex":
        out({"status": "ok", **store.reindex(method=args.method, metric=args.metric)})
        return 0
    if args.cmd == "vector-explain":
        sample = [0.0] * args.dim
        out({"status": "ok", **store.explain(sample, limit=args.limit, metric=args.metric)})
        return 0
    if args.cmd == "vector-migrate":
        from secondbrain.storage.vector_store import SqliteVectorStore
        from secondbrain.storage.vector_migrate import migrate_vectors
        if not args.source_url:
            out({"status": "error", "message": "usage: vector-migrate --from sqlite:///path (target = current DATABASE_URL)"})
            return 2
        source = SqliteVectorStore(args.source_url)
        out({"status": "ok", **migrate_vectors(source, store)})
        return 0
    out({"status": "unknown_command", "cmd": args.cmd})
    return 2


def _embed_main(argv: list[str]) -> int:
    from secondbrain.embeddings.base import EmbeddingConfig, EmbeddingProviderError
    from secondbrain.embeddings.factory import build_provider
    from secondbrain.embeddings.gate import embedding_production_gate
    parser = argparse.ArgumentParser(prog="secondbrain")
    parser.add_argument("cmd")
    parser.add_argument("--provider", default=os.environ.get("EMBEDDING_PROVIDER", "openai"))
    parser.add_argument("--model", default=os.environ.get("EMBEDDING_MODEL", "text-embedding-3-small"))
    parser.add_argument("--dimensions", type=int, default=int(os.environ.get("EMBEDDING_DIMENSIONS", "1536")))
    parser.add_argument("--environment", default=os.environ.get("SECOND_BRAIN_ENV", "production"))
    args, _ = parser.parse_known_args(argv)
    cfg = EmbeddingConfig(provider=args.provider, model=args.model, dimensions=args.dimensions)
    try:
        provider = build_provider(cfg)
    except EmbeddingProviderError as exc:
        out({"status": "provider_error", "message": str(exc)})
        return 3
    if args.cmd == "embed-health":
        out({"status": "ok", **provider.health().to_dict()})
        return 0
    if args.cmd == "embed-validate":
        h = provider.health()
        out({"status": "ok", "dimensions_ok": h.dimensions == args.dimensions, **h.to_dict()})
        return 0
    if args.cmd == "embed-gate":
        report = embedding_production_gate(provider, environment=args.environment)
        out(report)
        return 0 if report["status"] == "PASS" else 4
    out({"status": "unknown_command", "cmd": args.cmd})
    return 2


def _doc_main(argv: list[str]) -> int:
    from pathlib import Path as _P
    from secondbrain.documents.preview import resolve, markdown_to_html, highlight
    from secondbrain.documents.compare import diff_documents
    parser = argparse.ArgumentParser(prog="secondbrain")
    parser.add_argument("cmd")
    parser.add_argument("path", nargs="?", default=None)
    parser.add_argument("--against", default=None)
    args, _ = parser.parse_known_args(argv)
    if args.cmd == "doc-preview":
        if not args.path:
            out({"status": "error", "message": "usage: doc-preview <file>"}); return 2
        kind = resolve(args.path)
        payload = {"status": "ok", "kind": kind.kind, "renderer": kind.renderer, "mime": kind.mime}
        if kind.kind == "markdown" and _P(args.path).exists():
            payload["html"] = markdown_to_html(_P(args.path).read_text(encoding="utf-8", errors="replace"))
        out(payload); return 0
    if args.cmd == "doc-diff":
        if not args.path or not args.against:
            out({"status": "error", "message": "usage: doc-diff <a> --against <b>"}); return 2
        a = _P(args.path).read_text(encoding="utf-8", errors="replace")
        b = _P(args.against).read_text(encoding="utf-8", errors="replace")
        result = diff_documents(a, b, left_label=args.path, right_label=args.against)
        out({"status": "ok", "added": result["added"], "removed": result["removed"],
             "similarity": result["similarity"], "identical": result["identical"]})
        return 0
    out({"status": "unknown_command", "cmd": args.cmd}); return 2


def _secret_main(argv: list[str]) -> int:
    import json as _json
    from secondbrain.secret_manager.vault import SecretVault, VaultError, VaultLockedError
    from secondbrain.secret_manager.health import vault_health
    parser = argparse.ArgumentParser(prog="secondbrain")
    parser.add_argument("cmd")
    parser.add_argument("--path", default=os.environ.get("SECOND_BRAIN_VAULT", "runtime/secrets/vault.json"))
    parser.add_argument("--name", default=None)
    parser.add_argument("--type", default="workspace_secret")
    parser.add_argument("--file", default=None)
    args, _ = parser.parse_known_args(argv)
    pw = os.environ.get("SECOND_BRAIN_VAULT_PASSWORD", "")      # never via CLI arg
    value = os.environ.get("SECRET_VALUE", "")
    exp_pw = os.environ.get("SECRET_EXPORT_PASSWORD", "")
    try:
        if args.cmd == "secret-init":
            SecretVault.create(args.path, pw)
            out({"status": "ok", "initialized": True, "path": args.path})
            return 0
        vault = SecretVault(args.path)
        if args.cmd == "secret-health":
            out({"status": "ok", **vault_health(vault)}); return 0
        vault.unlock(pw)
        if args.cmd == "secret-set":
            if not args.name or not value:
                out({"status": "error", "message": "set SECRET_VALUE env and --name"}); return 2
            vault.set_secret(args.name, value, secret_type=args.type)
            out({"status": "ok", "name": args.name, "type": args.type})   # value never echoed
            return 0
        if args.cmd == "secret-list":
            out({"status": "ok", "secrets": vault.list_secrets()}); return 0
        if args.cmd == "secret-rotate":
            out({"status": "ok", **vault.rotate_master_key(pw)}); return 0
        if args.cmd == "secret-export":
            if not args.file or not exp_pw:
                out({"status": "error", "message": "need --file and SECRET_EXPORT_PASSWORD"}); return 2
            Path(args.file).write_text(_json.dumps(vault.export_bundle(exp_pw)), encoding="utf-8")
            out({"status": "ok", "exported_to": args.file}); return 0
        if args.cmd == "secret-import":
            if not args.file or not exp_pw:
                out({"status": "error", "message": "need --file and SECRET_EXPORT_PASSWORD"}); return 2
            bundle = _json.loads(Path(args.file).read_text(encoding="utf-8"))
            out({"status": "ok", **vault.import_bundle(bundle, exp_pw)}); return 0
        out({"status": "unknown_command", "cmd": args.cmd}); return 2
    except (VaultError, VaultLockedError) as exc:
        out({"status": "vault_error", "message": str(exc)}); return 3


def _connectors_ext_main(argv: list[str]) -> int:
    from secondbrain.connectors.import_bridge import ConnectorImportBridge, InMemoryImportJobSink
    from secondbrain.connectors.cursor_store import InMemoryCursorStore
    from secondbrain.connectors.incremental_runner import IncrementalSyncRunner
    parser = argparse.ArgumentParser(prog="secondbrain")
    parser.add_argument("cmd")
    parser.add_argument("--path", default=None)
    parser.add_argument("--owner", default=None)
    parser.add_argument("--repo", default=None)
    args, _ = parser.parse_known_args(argv)

    def _run(connector):
        sink = InMemoryImportJobSink()
        bridge = ConnectorImportBridge(sink=sink)
        result = IncrementalSyncRunner(InMemoryCursorStore()).run(connector, lambda fi: bridge.process_item(fi.payload))
        return {"connector": connector.name, "fetched": result.fetched,
                "processed": result.processed, "import": bridge.snapshot()["imported"]}

    if args.cmd == "local-folder-sync":
        if not args.path:
            out({"status": "error", "message": "usage: local-folder-sync --path <dir>"}); return 2
        from secondbrain.connectors.local_folder import LocalFolderConnector
        out({"status": "ok", **_run(LocalFolderConnector(args.path))}); return 0
    if args.cmd == "github-issues":
        from secondbrain.connectors.github.config import GitHubConfig, GitHubConfigError
        from secondbrain.connectors.github.auth import token_provider_from_config
        from secondbrain.connectors.github.client import GitHubClient
        from secondbrain.connectors.github.connector import GitHubIssuesConnector
        if not args.owner or not args.repo:
            out({"status": "error", "message": "usage: github-issues --owner <o> --repo <r> (env GITHUB_TOKEN)"}); return 2
        try:
            cfg = GitHubConfig.from_env()
        except GitHubConfigError as exc:
            out({"status": "config_error", "message": str(exc)}); return 3
        client = GitHubClient(cfg, token_provider_from_config(cfg))
        out({"status": "ok", **_run(GitHubIssuesConnector(client, args.owner, args.repo))}); return 0
    out({"status": "unknown_command", "cmd": args.cmd}); return 2


def _ui_main(argv: list[str]) -> int:
    from secondbrain.ui import tokens
    from secondbrain.ui.contrast import audit_pairs
    parser = argparse.ArgumentParser(prog="secondbrain")
    parser.add_argument("cmd")
    parser.add_argument("--theme", default="dark")
    args, _ = parser.parse_known_args(argv)
    if args.cmd == "ui-theme":
        out({"status": "ok", "theme": args.theme, "palette": tokens.palette(args.theme),
             "spacing": tokens.SPACING, "font_sizes": tokens.FONT_SIZES})
        return 0
    if args.cmd == "ui-contrast-check":
        report = {}
        overall = True
        for name in tokens.PALETTES:
            p = tokens.palette(name)
            audit = audit_pairs([
                ("fg/bg", p["fg"], p["bg"]),
                ("muted/bg", p["fg_muted"], p["bg"]),
                ("on_primary/primary", p["on_primary"], p["primary"]),
                ("error/bg", p["error"], p["bg"]),
            ])
            report[name] = audit
            overall = overall and audit["passes_aa"]
        out({"status": "PASS" if overall else "FAIL", "themes": report})
        return 0 if overall else 4
    out({"status": "unknown_command", "cmd": args.cmd}); return 2


def main(argv: list[str] | None = None) -> int:
    raw = list(sys.argv[1:] if argv is None else argv)
    cmd = _first_command(raw)
    if cmd in {"version", "--version"} or "--version" in raw or "-V" in raw:
        out(_version_info())
        return 0
    if cmd == "version-sync":
        from secondbrain.version_sync import sync_version
        out(sync_version(_first_project_root(raw)))
        return 0
    if cmd is None:
        load_env_file()
        return gui_command(["gui", "--project-root", str(Path.cwd())])
    if cmd == "bootstrap":
        out(write_bootstrap_report(Path.cwd(), repair=True))
        return 0
    if cmd in {"m365-login", "m365-sync", "m365-status", "m365-disconnect"}:
        return _m365_main(raw)
    if cmd in {"google-login", "google-sync", "google-status", "google-disconnect"}:
        return _google_main(raw)
    if cmd == "vision-ocr":
        return _vision_main(raw)
    if cmd in {"db-validate", "db-status", "db-migrate"}:
        return _db_main(raw)
    if cmd in {"vector-benchmark", "vector-reindex", "vector-explain", "vector-migrate"}:
        return _vector_main(raw)
    if cmd in {"embed-health", "embed-validate", "embed-gate"}:
        return _embed_main(raw)
    if cmd in {"doc-preview", "doc-diff"}:
        return _doc_main(raw)
    if cmd in {"secret-init", "secret-set", "secret-list", "secret-health", "secret-rotate", "secret-export", "secret-import"}:
        return _secret_main(raw)
    if cmd in {"local-folder-sync", "github-issues"}:
        return _connectors_ext_main(raw)
    if cmd in {"ui-theme", "ui-contrast-check"}:
        return _ui_main(raw)
    if cmd == "desktop-analyze":
        return _desktop_main(raw)
    if cmd == "diagram-analyze":
        return _diagram_main(raw)
    if cmd in {"voice-transcribe", "voice-say", "voice-converse", "voice-enroll", "voice-identify", "voice-command"}:
        return _voice_main(raw)
    if cmd == "repo-doctor":
        return _repo_doctor_main(raw)
    if cmd == "dependency-inventory":
        return _dependency_inventory_main(raw)
    if cmd == "rc-gate":
        return _rc_gate_main(raw)
    if cmd == "review-approval-gate":
        return _review_approval_gate_main(raw)
    if cmd == "review-approval-release-gate":
        return _review_approval_release_gate_main(raw)
    if cmd == "connector-e2e-gate":
        return _connector_e2e_gate_main(raw)
    if cmd == "provider-live-gate":
        return _provider_live_gate_main(raw)
    if cmd == "postgres-live-gate":
        return _postgres_live_gate_main(raw)
    if cmd == "security-gate":
        return _security_gate_main(raw)
    if cmd == "backup-gate":
        return _backup_gate_main(raw)
    if cmd == "native-voice-app-gate":
        from secondbrain.desktop_native.native_voice_app_gate import run_native_voice_app_gate
        report = run_native_voice_app_gate(_first_project_root(raw))
        out(report)
        return 0 if report["status"] != "BLOCKED" else 4
    if cmd in {"native-startup-status", "native-startup-enable", "native-startup-disable"}:
        from secondbrain.desktop_native.windows_startup import WindowsStartupManager
        manager = WindowsStartupManager(_first_project_root(raw))
        try:
            if cmd == "native-startup-enable":
                payload = manager.enable()
            elif cmd == "native-startup-disable":
                payload = manager.disable()
            else:
                payload = manager.status()
        except (RuntimeError, OSError) as exc:
            out({"status": "BLOCKED", "error": str(exc), **manager.status()})
            return 4
        out({"status": "PASS", **payload})
        return 0
    if cmd == "system-rc-gate":
        return _rc_gate_main(["rc-gate", *raw[1:]])
    if cmd == "rag-eval":
        return _rag_eval_main(raw)
    if cmd == "ga-readiness-gate":
        return _ga_readiness_gate_main(raw)
    if cmd in {
        "ops-status",
        "ops-backup",
        "ops-backups",
        "ops-backup-verify",
        "ops-backup-health",
        "ops-backup-report",
        "ops-backup-schedule-configure",
        "ops-backup-schedule-run",
        "ops-restore-plan",
        "ops-restore",
        "ops-restore-rollback",
    }:
        from secondbrain.launcher_runtime_v119 import main as operations_main

        return operations_main(raw)
    if cmd == "p3-pgvector-readiness":
        return _p3_pgvector_main(raw)
    if cmd == "p3-rag-store-status":
        return _p3_rag_store_main(raw)
    if cmd == "p3-p1-store-bridge":
        return _p3_p1_store_bridge_main(raw)
    if cmd in {"p1-rag-status", "p1-rag-ingest-text", "p1-rag-ingest-file", "p1-rag-ingest-dir", "p1-rag-search", "p1-rag-vector-search", "p1-rag-hybrid-search", "p1-rag-answer", "p1-rag-sources", "p1-rag-explain", "p1-rag-validate", "p1-rag-quality", "p1-rag-reindex", "p1-rag-migrate-postgres", "p1-embedding-status", "p1-vector-provider-audit", "p1-vector-index-repair", "p1-provider-health", "p1-embedding-config", "p1-retrieval-benchmark", "p1-retrieval-metrics", "p1-golden-eval", "p1-production", "p1-gate"}:
        parser = argparse.ArgumentParser(prog="secondbrain")
        parser.add_argument("--project-root", default=str(Path.cwd()))
        parser.add_argument("--profile", default=None)
        parser.add_argument("cmd")
        parser.add_argument("args", nargs="*")
        parser.add_argument("--source", default="manual")
        parser.add_argument("--title", default=None)
        parser.add_argument("--limit", type=int, default=5)
        parser.add_argument("--write-report", action="store_true")
        parser.add_argument("--allow-non-pgvector", action="store_true")
        args, _ = parser.parse_known_args(raw)
        rt = P1RagRuntime(args.project_root, args.profile)
        if cmd == "p1-rag-status":
            payload = rt.status()
        elif cmd == "p1-rag-ingest-text":
            payload = rt.ingest_text(" ".join(args.args), args.source, args.title)
        elif cmd == "p1-rag-ingest-file":
            source_path = args.args[0] if args.args else ""
            if Path(source_path).suffix.lower() in {".json", ".jsonl", ".ndjson", ".md", ".markdown", ".zip"}:
                from secondbrain.importing import StreamingImportService
                session = StreamingImportService(args.project_root).import_file(source_path, source=args.source)
                payload = {"ok": session.status == "completed", **session.to_dict()}
            else:
                payload = rt.ingest_file(source_path, args.source, args.title)
        elif cmd == "p1-rag-ingest-dir":
            payload = rt.ingest_directory(args.args[0] if args.args else "")
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
        elif cmd == "p1-vector-index-repair":
            payload = repair_vector_index(rt, write_report=args.write_report)
        elif cmd == "p1-provider-health":
            payload = evaluate_embedding_provider_health(rt, production=True, write_report=args.write_report)
        elif cmd == "p1-embedding-config":
            payload = evaluate_embedding_config(args.project_root, production=True, write_report=args.write_report)
        elif cmd == "p1-rag-migrate-postgres":
            payload = migrate_sqlite_to_selected_store(
                args.project_root,
                dry_run=False,
                write_report=args.write_report,
                require_pgvector=not args.allow_non_pgvector,
            )
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
    if cmd in {"document-center-status", "memory-center-status"}:
        parser = argparse.ArgumentParser(prog="secondbrain")
        parser.add_argument("cmd")
        parser.add_argument("--project-root", default=str(Path.cwd()))
        parser.add_argument("--profile", default=None)
        args, _ = parser.parse_known_args(raw)
        if cmd == "document-center-status":
            from secondbrain.gui.document_center_runtime import document_center_status
            payload = document_center_status(args.project_root, args.profile)
        else:
            from secondbrain.gui.memory_center_runtime import memory_center_status
            payload = memory_center_status(args.project_root, args.profile)
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
    if cmd in {"theme-center", "theme-center-gui", "theme-status", "theme-list", "theme-current", "theme-activate", "theme-preview", "theme-export", "theme-import", "theme-reset", "theme-history"}:
        from secondbrain.native.theme_center.cli import main as theme_center_main
        return theme_center_main(raw)
    if cmd in {"notification-center", "notification-center-gui", "notification-center-status", "notification-list", "notification-send", "notification-read", "notification-read-all", "notification-clear"}:
        from secondbrain.native.notification_center.cli import main as notification_center_main
        return notification_center_main(raw)
    if cmd in {"job-queue-status", "job-queue-add", "job-queue-list", "job-queue-run", "job-queue-approve", "job-queue-cancel", "job-queue-clear-finished", "job-queue-center-gui"}:
        from secondbrain.native.job_queue_center.cli import launcher_main as job_queue_main
        return job_queue_main(raw)
    if cmd in {"native-desktop-health", "native-desktop-doctor", "native-desktop-report"}:
        from secondbrain.native.desktop_health.cli import main as desktop_health_main
        return desktop_health_main(raw)
    if cmd in {"settings-center", "settings-center-gui", "settings-center-status", "settings-center-snapshot", "settings-center-write-defaults", "settings-center-set", "settings-center-history"}:
        from secondbrain.native.settings_center.cli import main as settings_center_main
        return settings_center_main(raw)
    if cmd in {"config-status", "config-snapshot", "config-set", "config-doctor"}:
        load_env_file()
        from secondbrain.runtime_config.cli import main as runtime_config_main
        return runtime_config_main(raw)
    if cmd in {"ai-workspace", "ai-workspace-gui", "ai-workspace-status", "ai-workspace-snapshot", "ai-workspace-navigation", "ai-workspace-activity", "ai-workspace-record"}:
        from secondbrain.native.ai_workspace.cli import main as ai_workspace_main
        return ai_workspace_main(raw)
    if cmd in {"import-center", "import-status", "import-history"}:
        from secondbrain.native.import_center_cli import main as import_center_main
        return import_center_main(raw)
    if cmd in {"agent-plan-create", "agent-plan-show", "agent-plan-list", "agent-plan-cancel", "agent-plan-resume"}:
        from secondbrain.agent.planner_cli import main as agent_plan_main
        return agent_plan_main(raw)
    if cmd in {"tool-list", "tool-show", "tool-health", "tool-run", "tool-disable", "tool-enable"}:
        from secondbrain.agent.tool_cli import main as tool_main
        return tool_main(raw)
    if cmd in {"document-preview", "document-preview-gui", "document-preview-status", "document-preview-open", "document-preview-metadata", "document-preview-search", "document-preview-ocr", "document-preview-annotate", "document-preview-annotations", "document-preview-version-snapshot", "document-preview-versions"}:
        from secondbrain.native.document_preview.cli import main as document_preview_main
        return document_preview_main(raw)
    if cmd in {"ai-chat", "conversation-list", "conversation-open", "conversation-export", "conversation-delete", "conversation-pin", "conversation-search", "conversation-gui"}:
        from secondbrain.native.chat import conversation_cli_main
        return conversation_cli_main(raw)
    if cmd in {"gui", "gui-start", "gui-open", "gui-status", "gui-doctor", "gui-shortcuts", "gui-bootstrap", "jarvis", "desktop", "desktop-gui", "desktop16-gui", "native-gui", "hud", "gui-web", "web-hud"}:
        load_env_file()
        return gui_command(raw)
    if cmd == "command-index":
        out(ModuleRegistry().command_index())
        return 0
    if cmd in {"status", "health", "module-status", "module-health", "modules"}:
        return _local_status(raw)
    if cmd in {"approval-list", "approval-show", "approval-approve", "approval-reject", "approval-audit", "approval-expire"}:
        from secondbrain.agent.safety.cli import main as approval_main
        return approval_main(raw)
    if cmd in {"workflow-create", "workflow-run", "workflow-status", "workflow-list", "workflow-cancel", "workflow-resume", "workflow-audit", "workflow-rollback"}:
        from secondbrain.agent.workflow.cli import main as workflow_main
        return workflow_main(raw)
    if cmd in {"background-agent-list", "background-agent-register", "background-agent-start", "background-agent-stop", "background-agent-pause", "background-agent-status", "background-agent-run", "background-agent-run-due", "background-agent-runs"}:
        from secondbrain.agent.background_agents.cli import main as background_agent_main
        return background_agent_main(raw)
    if cmd in {"agent-memory-preview", "agent-memory-inject", "agent-memory-audit"}:
        from secondbrain.agent.memory_injection.cli import main as agent_memory_main
        return agent_memory_main(raw)
    if cmd in {"goal-create", "goal-list", "goal-show", "goal-update", "goal-report", "goal-close"}:
        from secondbrain.agent.goals.cli import main as goal_main
        return goal_main(raw)
    if cmd in {"agent-control-center", "agent-control-center-gui", "agent-control-center-status", "agent-control-area", "agent-control-plan-create", "agent-control-plan-inspect", "agent-control-plan-start", "agent-control-approve", "agent-control-reject", "agent-control-workflow", "agent-control-goal-report", "agent-control-bg"}:
        from secondbrain.native.agent_control.cli import main as agent_control_main
        return agent_control_main(raw)
    if cmd.startswith("mobile16-"):
        return _mobile_main(raw)
    try:
        from secondbrain.launcher_runtime_v126 import main as runtime_main
        return runtime_main(_strip_unhandled_global_options(raw, {"--project-root", "--profile"}))
    except SystemExit as exc:
        return int(exc.code or 0)


if __name__ == "__main__":
    raise SystemExit(main())
