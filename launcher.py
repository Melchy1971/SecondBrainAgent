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


def _approval_postgres_live_gate_main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="secondbrain", description="PostgreSQL approval live certification")
    parser.add_argument("cmd")
    parser.add_argument("project_root", nargs="?", default=str(Path.cwd()))
    parser.add_argument("--project-root", dest="project_root_option", default=None)
    parser.add_argument("--no-write-report", action="store_true")
    args, _ = parser.parse_known_args(argv)
    from secondbrain.release.approval_postgres_live_gate import BLOCKED, run_approval_postgres_live_gate

    report = run_approval_postgres_live_gate(
        args.project_root_option or args.project_root, write_report=not args.no_write_report,
    )
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
    elif args.cmd == "mobi÷Ÿ4¶‰žËkºwµç}…Ñ•}µ…¥¸¡É…Ü¤(€€€¥˜µ€ôô€‰½¹¹•Ñ½Èµ”É”µ…Ñ”ˆè(€€€€€€€É•ÑÕÉ¸}½¹¹•Ñ½É}”É•}…Ñ•}µ…¥¸¡É…Ü¤(€€€¥˜µ€ôô€‰…ÁÁÉ½Ù…°µÁ½ÍÑÉ•Ìµ±¥Ù”µ…Ñ”ˆè(€€€€€€€É•ÑÕÉ¸}…ÁÁÉ½Ù…±}Á½ÍÑÉ•Í}±¥Ù•}…Ñ•}µ…¥¸¡É…Ü¤(€€€¥˜µ€ôô€‰Í•ÕÉ¥Ñäµ…Ñ”ˆè(€€€€€€€É•ÑÕÉ¸}Í•ÕÉ¥Ñå}…Ñ•}µ…¥¸¡É…Ü¤(€€€¥˜µ€ôô€‰‰…­ÕÀµ…Ñ”ˆè(€€€€€€€É•ÑÕÉ¸}‰…­ÕÁ}…Ñ•}µ…¥¸¡É…Ü¤(€€€¥˜µ€ôô€‰ÍåÍÑ•´µÉŒµ…Ñ”ˆè(€€€€€€€É•ÑÕÉ¸}É}…Ñ•}µ…¥¸¡l‰ÉŒµ…Ñ”ˆ°€©É…ÝlÄéut¤(€€€¥˜µ€ôô€‰É…œµ•Ù…°ˆè(€€€€€€€É•ÑÕÉ¸}É…}•Ù…±}µ…¥¸¡É…Ü¤(€€€¥˜µ€ôô€‰„µÉ•…‘¥¹•ÍÌµ…Ñ”ˆè(€€€€€€€É•ÑÕÉ¸}…}É•…‘¥¹•ÍÍ}…Ñ•}µ…¥¸¡É…Ü¤(€€€¥˜µ¥¸ì(€€€€€€€€‰½ÁÌµÍÑ…ÑÕÌˆ°(€€€€€€€€‰½ÁÌµ‰…­ÕÀˆ°(€€€€€€€€‰½ÁÌµ‰…­ÕÁÌˆ°(€€€€€€€€‰½ÁÌµ‰…­ÕÀµÙ•É¥™äˆ°(€€€€€€€€‰½ÁÌµ‰…­ÕÀµ¡•…±Ñ ˆ°(€€€€€€€€‰½ÁÌµ‰…­ÕÀµÉ•Á½ÉÐˆ°(€€€€€€€€‰½ÁÌµ‰…­ÕÀµÍ¡•‘Õ±”µ½¹™¥ÕÉ”ˆ°(€€€€€€€€‰½ÁÌµ‰…­ÕÀµÍ¡•‘Õ±”µÉÕ¸ˆ°(€€€€€€€€‰½ÁÌµÉ•ÍÑ½É”µÁ±…¸ˆ°(€€€€€€€€‰½ÁÌµÉ•ÍÑ½É”ˆ°(€€€€€€€€‰½ÁÌµÉ•ÍÑ½É”µÉ½±±‰…¬ˆ°(€€€ôè(€€€€€€€™É½´Í•½¹‘‰É…¥¸¹±…Õ¹¡•É}ÉÕ¹Ñ¥µ•}ØÄÄä¥µÁ½ÉÐµ…¥¸…Ì½Á•É…Ñ¥½¹Í}µ…¥¸((€€€€€€€É•ÑÕÉ¸½Á•É…Ñ¥½¹Í}µ…¥¸¡É…Ü¤(€€€¥˜µ€ôô€‰ÀÌµÁÙ•Ñ½ÈµÉ•…‘¥¹•ÍÌˆè(€€€€€€€É•ÑÕÉ¸}ÀÍ}ÁÙ•Ñ½É}µ…¥¸¡É…Ü¤(€€€¥˜µ€ôô€‰ÀÌµÉ…œµÍÑ½É”µÍÑ…ÑÕÌˆè(€€€€€€€É•ÑÕÉ¸}ÀÍ}É…}ÍÑ½É•}µ…¥¸¡É…Ü¤(€€€¥˜µ€ôô€‰ÀÌµÀÄµÍÑ½É”µ‰É¥‘”ˆè(€€€€€€€É•ÑÕÉ¸}ÀÍ}ÀÅ}ÍÑ½É•}‰É¥‘•}µ…¥¸¡É…Ü¤(€€€¥˜µ¥¸ì‰ÀÄµÉ…œµÍÑ…ÑÕÌˆ°€‰ÀÄµÉ…œµ¥¹•ÍÐµÑ•áÐˆ°€‰ÀÄµÉ…œµ¥¹•ÍÐµ™¥±”ˆ°€‰ÀÄµÉ…œµ¥¹•ÍÐµ‘¥Èˆ°€‰ÀÄµÉ…œµÍ•…É ˆ°€‰ÀÄµÉ…œµÙ•Ñ½ÈµÍ•…É ˆ°€‰ÀÄµÉ…œµ¡å‰É¥µÍ•…É ˆ°€‰ÀÄµÉ…œµ…¹ÍÝ•Èˆ°€‰ÀÄµÉ…œµÍ½ÕÉ•Ìˆ°€‰ÀÄµÉ…œµ•áÁ±…¥¸ˆ°€‰ÀÄµÉ…œµÙ…±¥‘…Ñ”ˆ°€‰ÀÄµÉ…œµÅÕ…±¥Ñäˆ°€‰ÀÄµÉ…œµÉ•¥¹‘•àˆ°€‰ÀÄµÉ…œµµ¥É…Ñ”µÁ½ÍÑÉ•Ìˆ°€‰ÀÄµ•µ‰•‘‘¥¹œµÍÑ…ÑÕÌˆ°€‰ÀÄµÙ•Ñ½ÈµÁÉ½Ù¥‘•Èµ…Õ‘¥Ðˆ°€‰ÀÄµÙ•Ñ½Èµ¥¹‘•àµÉ•Á…¥Èˆ°€‰ÀÄµÁÉ½Ù¥‘•Èµ¡•…±Ñ ˆ°€‰ÀÄµ•µ‰•‘‘¥¹œµ½¹™¥œˆ°€‰ÀÄµÉ•ÑÉ¥•Ù…°µ‰•¹¡µ…É¬ˆ°€‰ÀÄµÉ•ÑÉ¥•Ù…°µµ•ÑÉ¥Ìˆ°€‰ÀÄµ½±‘•¸µ•Ù…°ˆ°€‰ÀÄµÁÉ½‘ÕÑ¥½¸ˆ°€‰ÀÄµ…Ñ”‰ôè(€€€€€€€Á…ÉÍ•È€ô…ÉÁ…ÉÍ”¹ÉÕµ•¹ÑA…ÉÍ•È¡ÁÉ½œô‰Í•½¹‘‰É…¥¸ˆ¤(€€€€€€€Á…ÉÍ•È¹…‘‘}…ÉÕµ•¹Ð ˆ´µÁÉ½©•ÐµÉ½½Ðˆ°‘•™…Õ±ÐõÍÑÈ¡A…Ñ ¹Ý ¤¤¤(€€€€€€€Á…ÉÍ•È¹…‘‘}…ÉÕµ•¹Ð ˆ´µÁÉ½™¥±”ˆ°‘•™…Õ±Ðõ9½¹”¤(€€€€€€€Á…ÉÍ•È¹…‘‘}…ÉÕµ•¹Ð ‰µˆ¤(€€€€€€€Á…ÉÍ•È¹…‘‘}…ÉÕµ•¹Ð ‰…ÉÌˆ°¹…ÉÌôˆ¨ˆ¤(€€€€€€€Á…ÉÍ•È¹…‘‘}…ÉÕµ•¹Ð ˆ´µÍ½ÕÉ”ˆ°‘•™…Õ±Ðô‰µ…¹Õ…°ˆ¤(€€€€€€€Á…ÉÍ•È¹…‘‘}…ÉÕµ•¹Ð ˆ´µÑ¥Ñ±”ˆ°‘•™…Õ±Ðõ9½¹”¤(€€€€€€€Á…ÉÍ•È¹…‘‘}…ÉÕµ•¹Ð ˆ´µ±¥µ¥Ðˆ°ÑåÁ”õ¥¹Ð°‘•™…Õ±ÐôÔ¤(€€€€€€€Á…ÉÍ•È¹…‘‘}…ÉÕµ•¹Ð ˆ´µÝÉ¥Ñ”µÉ•Á½ÉÐˆ°…Ñ¥½¸ô‰ÍÑ½É•}ÑÉÕ”ˆ¤(€€€€€€€Á…ÉÍ•È¹…‘‘}…ÉÕµ•¹Ð ˆ´µ…±±½Üµ¹½¸µÁÙ•Ñ½Èˆ°…Ñ¥½¸ô‰ÍÑ½É•}ÑÉÕ”ˆ¤(€€€€€€€…ÉÌ°|€ôÁ…ÉÍ•È¹Á…ÉÍ•}­¹½Ý¹}…ÉÌ¡É…Ü¤(€€€€€€€ÉÐ€ô@ÅI…IÕ¹Ñ¥µ”¡…ÉÌ¹ÁÉ½©•Ñ}É½½Ð°…ÉÌ¹ÁÉ½™¥±”¤(€€€€€€€¥˜µ€ôô€‰ÀÄµÉ…œµÍÑ…ÑÕÌˆè(€€€€€€€€€€€Á…å±½…€ôÉÐ¹ÍÑ…ÑÕÌ ¤(€€€€€€€•±¥˜µ€ôô€‰ÀÄµÉ…œµ¥¹•ÍÐµÑ•áÐˆè(€€€€€€€€€€€Á…å±½…€ôÉÐ¹¥¹•ÍÑ}Ñ•áÐ ˆ€ˆ¹©½¥¸¡…ÉÌ¹…ÉÌ¤°…ÉÌ¹Í½ÕÉ”°…ÉÌ¹Ñ¥Ñ±”¤(€€€€€€€•±¥˜µ€ôô€‰ÀÄµÉ…œµ¥¹•ÍÐµ™¥±”ˆè(€€€€€€€€€€€Í½ÕÉ•}Á…Ñ €ô…ÉÌ¹…ÉÍlÁt¥˜…ÉÌ¹…ÉÌ•±Í”€ˆˆ(€€€€€€€€€€€¥˜A…Ñ ¡Í½ÕÉ•}Á…Ñ ¤¹ÍÕ™™¥à¹±½Ý•È ¤¥¸ìˆ¹©Í½¸ˆ°€ˆ¹©Í½¹°ˆ°€ˆ¹¹‘©Í½¸ˆ°€ˆ¹µˆ°€ˆ¹µ…É­‘½Ý¸ˆ°€ˆ¹é¥À‰ôè(€€€€€€€€€€€€€€€™É½´Í•½¹‘‰É…¥¸¹¥µÁ½ÉÑ¥¹œ¥µÁ½ÉÐMÑÉ•…µ¥¹%µÁ½ÉÑM•ÉÙ¥”(€€€€€€€€€€€€€€€Í•ÍÍ¥½¸€ôMÑÉ•…µ¥¹%µÁ½ÉÑM•ÉÙ¥”¡…ÉÌ¹ÁÉ½©•Ñ}É½½Ð¤¹¥µÁ½ÉÑ}™¥±”¡Í½ÕÉ•}Á…Ñ °Í½ÕÉ”õ…ÉÌ¹Í½ÕÉ”¤(€€€€€€€€€€€€€€€Á…å±½…€ôì‰½¬ˆèÍ•ÍÍ¥½¸¹ÍÑ…ÑÕÌ€ôô€‰½µÁ±•Ñ•ˆ°€¨©Í•ÍÍ¥½¸¹Ñ½}‘¥Ð ¥ô(€€€€€€€€€€€•±Í”è(€€€€€€€€€€€€€€€Á…å±½…€ôÉÐ¹¥¹•ÍÑ}™¥±”¡Í½ÕÉ•}Á…Ñ °…ÉÌ¹Í½ÕÉ”°…ÉÌ¹Ñ¥Ñ±”¤(€€€€€€€•±¥˜µ€ôô€‰ÀÄµÉ…œµ¥¹•ÍÐµ‘¥Èˆè(€€€€€€€€€€€Á…å±½…€ôÉÐ¹¥¹•ÍÑ}‘¥É•Ñ½Éä¡…ÉÌ¹…ÉÍlÁt¥˜…ÉÌ¹…ÉÌ•±Í”€ˆˆ¤(€€€€€€€•±¥˜µ€ôô€‰ÀÄµÉ…œµÍ•…É ˆè(€€€€€€€€€€€Á…å±½…€ôÉÐ¹Í•…É  ˆ€ˆ¹©½¥¸¡…ÉÌ¹…ÉÌ¤°…ÉÌ¹±¥µ¥Ð¤(€€€€€€€•±¥˜µ€ôô€‰ÀÄµÉ…œµÙ•Ñ½ÈµÍ•…É ˆè(€€€€€€€€€€€Á…å±½…€ôÉÐ¹Ù•Ñ½É}Í•…É  ˆ€ˆ¹©½¥¸¡…ÉÌ¹…ÉÌ¤°…ÉÌ¹±¥µ¥Ð¤(€€€€€€€•±¥˜µ€ôô€‰ÀÄµÉ…œµ¡å‰É¥µÍ•…É ˆè(€€€€€€€€€€€Á…å±½…€ôÉÐ¹¡å‰É¥‘}Í•…É  ˆ€ˆ¹©½¥¸¡…ÉÌ¹…ÉÌ¤°…ÉÌ¹±¥µ¥Ð¤(€€€€€€€•±¥˜µ€ôô€‰ÀÄµÉ…œµÉ•¥¹‘•àˆè(€€€€€€€€€€€Á…å±½…€ôÉÐ¹É•¥¹‘•á}Ù•Ñ½ÉÌ¡ÝÉ¥Ñ•}É•Á½ÉÐõ…ÉÌ¹ÝÉ¥Ñ•}É•Á½ÉÐ¤(€€€€€€€•±¥˜µ€ôô€‰ÀÄµ•µ‰•‘‘¥¹œµÍÑ…ÑÕÌˆè(€€€€€€€€€€€Á…å±½…€ôÉÐ¹•µ‰•‘‘¥¹}ÍÑ…ÑÕÌ ¤(€€€€€€€•±¥˜µ€ôô€‰ÀÄµÙ•Ñ½ÈµÁÉ½Ù¥‘•Èµ…Õ‘¥Ðˆè(€€€€€€€€€€€Á…å±½…€ô…Õ‘¥Ñ}Ù•Ñ½É}ÁÉ½Ù¥‘•È¡ÉÐ°ÝÉ¥Ñ•}É•Á½ÉÐõ…ÉÌ¹ÝÉ¥Ñ•}É•Á½ÉÐ¤(€€€€€€€•±¥˜µ€ôô€‰ÀÄµÙ•Ñ½Èµ¥¹‘•àµÉ•Á…¥Èˆè(€€€€€€€€€€€Á…å±½…€ôÉ•Á…¥É}Ù•Ñ½É}¥¹‘•à¡ÉÐ°ÝÉ¥Ñ•}É•Á½ÉÐõ…ÉÌ¹ÝÉ¥Ñ•}É•Á½ÉÐ¤(€€€€€€€•±¥˜µ€ôô€‰ÀÄµÁÉ½Ù¥‘•Èµ¡•…±Ñ ˆè(€€€€€€€€€€€Á…å±½…€ô•Ù…±Õ…Ñ•}•µ‰•‘‘¥¹}ÁÉ½Ù¥‘•É}¡•…±Ñ ¡ÉÐ°ÁÉ½‘ÕÑ¥½¸õQÉÕ”°ÝÉ¥Ñ•}É•Á½ÉÐõ…ÉÌ¹ÝÉ¥Ñ•}É•Á½ÉÐ¤(€€€€€€€•±¥˜µ€ôô€‰ÀÄµ•µ‰•‘‘¥¹œµ½¹™¥œˆè(€€€€€€€€€€€Á…å±½…€ô•Ù…±Õ…Ñ•}•µ‰•‘‘¥¹}½¹™¥œ¡…ÉÌ¹ÁÉ½©•Ñ}É½½Ð°ÁÉ½‘ÕÑ¥½¸õQÉÕ”°ÝÉ¥Ñ•}É•Á½ÉÐõ…ÉÌ¹ÝÉ¥Ñ•}É•Á½ÉÐ¤(€€€€€€€•±¥˜µ€ôô€‰ÀÄµÉ…œµµ¥É…Ñ”µÁ½ÍÑÉ•Ìˆè(€€€€€€€€€€€Á…å±½…€ôµ¥É…Ñ•}ÍÅ±¥Ñ•}Ñ½}Í•±•Ñ•‘}ÍÑ½É” (€€€€€€€€€€€€€€€…ÉÌ¹ÁÉ½©•Ñ}É½½Ð°(€€€€€€€€€€€€€€€‘Éå}ÉÕ¸õ…±Í”°(€€€€€€€€€€€€€€€ÝÉ¥Ñ•}É•Á½ÉÐõ…ÉÌ¹ÝÉ¥Ñ•}É•Á½ÉÐ°(€€€€€€€€€€€€€€€É•ÅÕ¥É•}ÁÙ•Ñ½Èõ¹½Ð…ÉÌ¹…±±½Ý}¹½¹}ÁÙ•Ñ½È°(€€€€€€€€€€€€¤(€€€€€€€•±¥˜µ€ôô€‰ÀÄµÉ•ÑÉ¥•Ù…°µ‰•¹¡µ…É¬ˆè(€€€€€€€€€€€Á…å±½…€ôÉÐ¹É•ÑÉ¥•Ù…±}‰•¹¡µ…É¬¡ÝÉ¥Ñ•}É•Á½ÉÐõ…ÉÌ¹ÝÉ¥Ñ•}É•Á½ÉÐ¤(€€€€€€€•±¥˜µ€ôô€‰ÀÄµÉ•ÑÉ¥•Ù…°µµ•ÑÉ¥Ìˆè(€€€€€€€€€€€Á…å±½…€ôÉÐ¹É•ÑÉ¥•Ù…±}µ•ÑÉ¥Ì¡ÝÉ¥Ñ•}É•Á½ÉÐõ…ÉÌ¹ÝÉ¥Ñ•}É•Á½ÉÐ¤(€€€€€€€•±¥˜µ€ôô€‰ÀÄµ½±‘•¸µ•Ù…°ˆè(€€€€€€€€€€€Á…å±½…€ô•Ù…±Õ…Ñ•}½±‘•¹}É•ÑÉ¥•Ù…°¡ÉÐ°…ÉÌ¹ÁÉ½©•Ñ}É½½Ð°ÝÉ¥Ñ•}É•Á½ÉÐõ…ÉÌ¹ÝÉ¥Ñ•}É•Á½ÉÐ¤(€€€€€€€•±¥˜µ€ôô€‰ÀÄµÁÉ½‘ÕÑ¥½¸ˆè(€€€€€€€€€€€Á…å±½…€ôÁÉ½‘ÕÑ¥½¹}…Ñ•}Ý¥Ñ¡}½±‘•¸¡ÉÐ°…ÉÌ¹ÁÉ½©•Ñ}É½½Ð°ÝÉ¥Ñ•}É•Á½ÉÐõ…ÉÌ¹ÝÉ¥Ñ•}É•Á½ÉÐ¤(€€€€€€€•±¥˜µ€ôô€‰ÀÄµÉ…œµ…¹ÍÝ•Èˆè(€€€€€€€€€€€Á…å±½…€ôÉÐ¹…¹ÍÝ•È ˆ€ˆ¹©½¥¸¡…ÉÌ¹…ÉÌ¤°…ÉÌ¹±¥µ¥Ð¤(€€€€€€€•±¥˜µ€ôô€‰ÀÄµÉ…œµÍ½ÕÉ•Ìˆè(€€€€€€€€€€€Á…å±½…€ôÉÐ¹Í½ÕÉ•Ì ¤(€€€€€€€•±¥˜µ€ôô€‰ÀÄµÉ…œµ•áÁ±…¥¸ˆè(€€€€€€€€€€€Á…å±½…€ôÉÐ¹•áÁ±…¥¸ ˆ€ˆ¹©½¥¸¡…ÉÌ¹…ÉÌ¤°…ÉÌ¹±¥µ¥Ð¤(€€€€€€€•±¥˜µ€ôô€‰ÀÄµÉ…œµÙ…±¥‘…Ñ”ˆè(€€€€€€€€€€€Á…å±½…€ôÉÐ¹Ù…±¥‘…Ñ•}¥¹‘•à¡ÝÉ¥Ñ•}É•Á½ÉÐõ…ÉÌ¹ÝÉ¥Ñ•}É•Á½ÉÐ¤(€€€€€€€•±¥˜µ€ôô€‰ÀÄµÉ…œµÅÕ…±¥Ñäˆè(€€€€€€€€€€€Á…å±½…€ôÉÐ¹ÅÕ…±¥Ñå}É•Á½ÉÐ ˆ€ˆ¹©½¥¸¡…ÉÌ¹…ÉÌ¤½È€‰)…ÉÙ¥ÌIEÕ•±±•¸ˆ°…ÉÌ¹±¥µ¥Ð°ÝÉ¥Ñ•}É•Á½ÉÐõ…ÉÌ¹ÝÉ¥Ñ•}É•Á½ÉÐ¤(€€€€€€€•±Í”è(€€€€€€€€€€€Á…å±½…€ôÉÐ¹…Ñ”¡ÝÉ¥Ñ•}É•Á½ÉÐõ…ÉÌ¹ÝÉ¥Ñ•}É•Á½ÉÐ¤(€€€€€€€½ÕÐ¡Á…å±½…¤(€€€€€€€É•ÑÕÉ¸€À¥˜Á…å±½…¹•Ð ‰½¬ˆ¤•±Í”€Ä(€€€¥˜µ¥¸ì‰‘½Õµ•¹Ðµ•¹Ñ•ÈµÍÑ…ÑÕÌˆ°€‰µ•µ½Éäµ•¹Ñ•ÈµÍÑ…ÑÕÌ‰ôè(€€€€€€€Á…ÉÍ•È€ô…ÉÁ…ÉÍ”¹ÉÕµ•¹ÑA…ÉÍ•È¡ÁÉ½œô‰Í•½¹‘‰É…¥¸ˆ¤(€€€€€€€Á…ÉÍ•È¹…‘‘}…ÉÕµ•¹Ð ‰µˆ¤(€€€€€€€Á…ÉÍ•È¹…‘‘}…ÉÕµ•¹Ð ˆ´µÁÉ½©•ÐµÉ½½Ðˆ°‘•™…Õ±ÐõÍÑÈ¡A…Ñ ¹Ý ¤¤¤(€€€€€€€Á…ÉÍ•È¹…‘‘}…ÉÕµ•¹Ð ˆ´µÁÉ½™¥±”ˆ°‘•™…Õ±Ðõ9½¹”¤(€€€€€€€…ÉÌ°|€ôÁ…ÉÍ•È¹Á…ÉÍ•}­¹½Ý¹}…ÉÌ¡É…Ü¤(€€€€€€€¥˜µ€ôô€‰‘½Õµ•¹Ðµ•¹Ñ•ÈµÍÑ…ÑÕÌˆè(€€€€€€€€€€€™É½´Í•½¹‘‰É…¥¸¹Õ¤¹‘½Õµ•¹Ñ}•¹Ñ•É}ÉÕ¹Ñ¥µ”¥µÁ½ÉÐ‘½Õµ•¹Ñ}•¹Ñ•É}ÍÑ…ÑÕÌ(€€€€€€€€€€€Á…å±½…€ô‘½Õµ•¹Ñ}•¹Ñ•É}ÍÑ…ÑÕÌ¡…ÉÌ¹ÁÉ½©•Ñ}É½½Ð°…ÉÌ¹ÁÉ½™¥±”¤(€€€€€€€•±Í”è(€€€€€€€€€€€™É½´Í•½¹‘‰É…¥¸¹Õ¤¹µ•µ½Éå}•¹Ñ•É}ÉÕ¹Ñ¥µ”¥µÁ½ÉÐµ•µ½Éå}•¹Ñ•É}ÍÑ…ÑÕÌ(€€€€€€€€€€€Á…å±½…€ôµ•µ½Éå}•¹Ñ•É}ÍÑ…ÑÕÌ¡…ÉÌ¹ÁÉ½©•Ñ}É½½Ð°…ÉÌ¹ÁÉ½™¥±”¤(€€€€€€€½ÕÐ¡Á…å±½…¤(€€€€€€€É•ÑÕÉ¸€À¥˜Á…å±½…¹•Ð ‰½¬ˆ¤•±Í”€Ä(€€€¥˜µ¥¸ì‰ÀÀµ‘½Ñ½Èˆ°€‰ÀÀµ…Ñ”ˆ°€‰ÀÀµÉ•Á½ÉÐˆ°€‰ÀÀµÍµ½­”ˆ°€‰ÀÀµ½¹ÑÉ…Ðˆ°€‰ÀÀµÉ•…‘¥¹•ÍÌˆ°€‰ÀÀµ‰½½ÑÍÑÉ…Àˆ°€‰ÀÀµÁÉ½‘ÕÑ¥½¸ˆ°€‰ÀÀµ…Õ‘¥Ð‰ôè(€€€€€€€Á…ÉÍ•È€ô…ÉÁ…ÉÍ”¹ÉÕµ•¹ÑA…ÉÍ•È¡ÁÉ½œô‰Í•½¹‘‰É…¥¸ˆ¤(€€€€€€€Á…ÉÍ•È¹…‘‘}…ÉÕµ•¹Ð ˆ´µÁÉ½©•ÐµÉ½½Ðˆ°‘•™…Õ±ÐõÍÑÈ¡A…Ñ ¹Ý ¤¤¤(€€€€€€€Á…ÉÍ•È¹…‘‘}…ÉÕµ•¹Ð ˆ´µÁÉ½™¥±”ˆ°‘•™…Õ±Ðõ9½¹”¤(€€€€€€€Á…ÉÍ•È¹…‘‘}…ÉÕµ•¹Ð ‰µˆ¤(€€€€€€€Á…ÉÍ•È¹…‘‘}…ÉÕµ•¹Ð ˆ´µÝÉ¥Ñ”µÉ•Á½ÉÐˆ°…Ñ¥½¸ô‰ÍÑ½É•}ÑÉÕ”ˆ¤(€€€€€€€…ÉÌ°|€ôÁ…ÉÍ•È¹Á…ÉÍ•}­¹½Ý¹}…ÉÌ¡É…Ü¤(€€€€€€€¥˜µ€ôô€‰ÀÀµ…Ñ”ˆè(€€€€€€€€€€€Á…å±½…€ôÀÁ}…Ñ”¡…ÉÌ¹ÁÉ½©•Ñ}É½½Ð°…ÉÌ¹ÁÉ½™¥±”°ÝÉ¥Ñ•}É•Á½ÉÐõ…ÉÌ¹ÝÉ¥Ñ•}É•Á½ÉÐ¤(€€€€€€€•±¥˜µ€ôô€‰ÀÀµÉ•Á½ÉÐˆè(€€€€€€€€€€€Á…å±½…€ôÀÁ}É•Á½ÉÐ¡…ÉÌ¹ÁÉ½©•Ñ}É½½Ð°…ÉÌ¹ÁÉ½™¥±”¤(€€€€€€€•±¥˜µ€ôô€‰ÀÀµÍµ½­”ˆè(€€€€€€€€€€€Á…å±½…€ôÀÁ}Íµ½­”¡…ÉÌ¹ÁÉ½©•Ñ}É½½Ð°…ÉÌ¹ÁÉ½™¥±”°ÝÉ¥Ñ•}É•Á½ÉÐõ…ÉÌ¹ÝÉ¥Ñ•}É•Á½ÉÐ¤(€€€€€€€•±¥˜µ€ôô€‰ÀÀµ½¹ÑÉ…Ðˆè(€€€€€€€€€€€Á…å±½…€ôÀÁ}½¹ÑÉ…Ð¡…ÉÌ¹ÁÉ½©•Ñ}É½½Ð°…ÉÌ¹ÁÉ½™¥±”°ÝÉ¥Ñ•}É•Á½ÉÐõ…ÉÌ¹ÝÉ¥Ñ•}É•Á½ÉÐ¤(€€€€€€€•±¥˜µ€ôô€‰ÀÀµÉ•…‘¥¹•ÍÌˆè(€€€€€€€€€€€Á…å±½…€ôÀÁ}É•…‘¥¹•ÍÌ¡…ÉÌ¹ÁÉ½©•Ñ}É½½Ð°…ÉÌ¹ÁÉ½™¥±”°ÝÉ¥Ñ•}É•Á½ÉÐõ…ÉÌ¹ÝÉ¥Ñ•}É•Á½ÉÐ¤(€€€€€€€•±¥˜µ€ôô€‰ÀÀµ‰½½ÑÍÑÉ…Àˆè(€€€€€€€€€€€Á…å±½…€ôÀÁ}‰½½ÑÍÑÉ…À¡…ÉÌ¹ÁÉ½©•Ñ}É½½Ð°…ÉÌ¹ÁÉ½™¥±”°ÝÉ¥Ñ•}É•Á½ÉÐõ…ÉÌ¹ÝÉ¥Ñ•}É•Á½ÉÐ¤(€€€€€€€•±¥˜µ€ôô€‰ÀÀµÁÉ½‘ÕÑ¥½¸ˆè(€€€€€€€€€€€Á…å±½…€ôÀÁ}ÁÉ½‘ÕÑ¥½¹}…Ñ”¡…ÉÌ¹ÁÉ½©•Ñ}É½½Ð°…ÉÌ¹ÁÉ½™¥±”°ÝÉ¥Ñ•}É•Á½ÉÐõ…ÉÌ¹ÝÉ¥Ñ•}É•Á½ÉÐ¤(€€€€€€€•±¥˜µ€ôô€‰ÀÀµ…Õ‘¥Ðˆè(€€€€€€€€€€€Á…å±½…€ôÀÁ}…ÉÑ¥™…Ñ}…Õ‘¥Ð¡…ÉÌ¹ÁÉ½©•Ñ}É½½Ð°…ÉÌ¹ÁÉ½™¥±”°ÝÉ¥Ñ•}É•Á½ÉÐõ…ÉÌ¹ÝÉ¥Ñ•}É•Á½ÉÐ¤(€€€€€€€•±Í”è(€€€€€€€€€€€Á…å±½…€ôÀÁ}‘½Ñ½È¡…ÉÌ¹ÁÉ½©•Ñ}É½½Ð°…ÉÌ¹ÁÉ½™¥±”¤(€€€€€€€½ÕÐ¡Á…å±½…¤(€€€€€€€É•ÑÕÉ¸€À¥˜Á…å±½…¹•Ð ‰½¬ˆ¤•±Í”€Ä(€€€¥˜µ¥¸ì‰‘…Í¡‰½…Éµ•¹Ñ•Èˆ°€‰‘…Í¡‰½…Éµ•¹Ñ•ÈµÕ¤ˆ°€‰‘…Í¡‰½…Éµ•¹Ñ•ÈµÍÑ…ÑÕÌˆ°€‰‘…Í¡‰½…Éµ•¹Ñ•ÈµÍ¹…ÁÍ¡½Ðˆ°€‰‘…Í¡‰½…Éµ•¹Ñ•Èµ…Ñ¥Ù¥Ñäˆ°€‰‘…Í¡‰½…Éµ•¹Ñ•ÈµÉ•½É‰ôè(€€€€€€€™É½´Í•½¹‘‰É…¥¸¹¹…Ñ¥Ù”¹‘…Í¡‰½…É‘}•¹Ñ•È¹±¤¥µÁ½ÉÐµ…¥¸…Ì‘…Í¡‰½…É‘}•¹Ñ•É}µ…¥¸(€€€€€€€É•ÑÕÉ¸‘…Í¡‰½…É‘}•¹Ñ•É}µ…¥¸¡É…Ü¤(€€€¥˜µ¥¸ì‰±…å½ÕÐµ•¹Ñ•Èˆ°€‰±…å½ÕÐµ•¹Ñ•ÈµÕ¤ˆ°€‰±…å½ÕÐµÍÑ…ÑÕÌˆ°€‰±…å½ÕÐµ±¥ÍÐˆ°€‰±…å½ÕÐµ±½…ˆ°€‰±…å½ÕÐµ…Ñ¥Ù…Ñ”ˆ°€‰±…å½ÕÐµÍ…Ù”ˆ°€‰±…å½ÕÐµÉ•Í•Ðˆ°€‰±…å½ÕÐµ•áÁ½ÉÐˆ°€‰±…å½ÕÐµ¥µÁ½ÉÐˆ°€‰±…å½ÕÐµ¡¥ÍÑ½Éä‰ôè(€€€€€€€™É½´Í•½¹‘‰É…¥¸¹¹…Ñ¥Ù”¹±…å½ÕÑ}•¹Ñ•È¹±¤¥µÁ½ÉÐµ…¥¸…Ì±…å½ÕÑ}•¹Ñ•É}µ…¥¸(€€€€€€€É•ÑÕÉ¸±…å½ÕÑ}•¹Ñ•É}µ…¥¸¡É…Ü¤(€€€¥˜µ¥¸ì‰Ñ¡•µ”µ•¹Ñ•Èˆ°€‰Ñ¡•µ”µ•¹Ñ•ÈµÕ¤ˆ°€‰Ñ¡•µ”µÍÑ…ÑÕÌˆ°€‰Ñ¡•µ”µ±¥ÍÐˆ°€‰Ñ¡•µ”µÕÉÉ•¹Ðˆ°€‰Ñ¡•µ”µ…Ñ¥Ù…Ñ”ˆ°€‰Ñ¡•µ”µÁÉ•Ù¥•Üˆ°€‰Ñ¡•µ”µ•áÁ½ÉÐˆ°€‰Ñ¡•µ”µ¥µÁ½ÉÐˆ°€‰Ñ¡•µ”µÉ•Í•Ðˆ°€‰Ñ¡•µ”µ¡¥ÍÑ½Éä‰ôè(€€€€€€€™É½´Í•½¹‘‰É…¥¸¹¹…Ñ¥Ù”¹Ñ¡•µ•}•¹Ñ•È¹±¤¥µÁ½ÉÐµ…¥¸…ÌÑ¡•µ•}•¹Ñ•É}µ…¥¸(€€€€€€€É•ÑÕÉ¸Ñ¡•µ•}•¹Ñ•É}µ…¥¸¡É…Ü¤(€€€¥˜µ¥¸ì‰¹½Ñ¥™¥…Ñ¥½¸µ•¹Ñ•Èˆ°€‰¹½Ñ¥™¥…Ñ¥½¸µ•¹Ñ•ÈµÕ¤ˆ°€‰¹½Ñ¥™¥…Ñ¥½¸µ•¹Ñ•ÈµÍÑ…ÑÕÌˆ°€‰¹½Ñ¥™¥…Ñ¥½¸µ±¥ÍÐˆ°€‰¹½Ñ¥™¥…Ñ¥½¸µÍ•¹ˆ°€‰¹½Ñ¥™¥…Ñ¥½¸µÉ•…ˆ°€‰¹½Ñ¥™¥…Ñ¥½¸µÉ•…µ…±°ˆ°€‰¹½Ñ¥™¥…Ñ¥½¸µ±•…È‰ôè(€€€€€€€™É½´Í•½¹‘‰É…¥¸¹¹…Ñ¥Ù”¹¹½Ñ¥™¥…Ñ¥½¹}•¹Ñ•È¹±¤¥µÁ½ÉÐµ…¥¸…Ì¹½Ñ¥™¥…Ñ¥½¹}•¹Ñ•É}µ…¥¸(€€€€€€€É•ÑÕÉ¸¹½Ñ¥™¥…Ñ¥½¹}•¹Ñ•É}µ…¥¸¡É…Ü¤(€€€¥˜µ¥¸ì‰©½ˆµÅÕ•Õ”µÍÑ…ÑÕÌˆ°€‰©½ˆµÅÕ•Õ”µ…‘ˆ°€‰©½ˆµÅÕ•Õ”µ±¥ÍÐˆ°€‰©½ˆµÅÕ•Õ”µÉÕ¸ˆ°€‰©½ˆµÅÕ•Õ”µ…ÁÁÉ½Ù”ˆ°€‰©½ˆµÅÕ•Õ”µ…¹•°ˆ°€‰©½ˆµÅÕ•Õ”µ±•…Èµ™¥¹¥Í¡•ˆ°€‰©½ˆµÅÕ•Õ”µ•¹Ñ•ÈµÕ¤‰ôè(€€€€€€€™É½´Í•½¹‘‰É…¥¸¹¹…Ñ¥Ù”¹©½‰}ÅÕ•Õ•}•¹Ñ•È¹±¤¥µÁ½ÉÐ±…Õ¹¡•É}µ…¥¸…Ì©½‰}ÅÕ•Õ•}µ…¥¸(€€€€€€€É•ÑÕÉ¸©½‰}ÅÕ•Õ•}µ…¥¸¡É…Ü¤(€€€¥˜µ¥¸ì‰¹…Ñ¥Ù”µ‘•Í­Ñ½Àµ¡•…±Ñ ˆ°€‰¹…Ñ¥Ù”µ‘•Í­Ñ½Àµ‘½Ñ½Èˆ°€‰¹…Ñ¥Ù”µ‘•Í­Ñ½ÀµÉ•Á½ÉÐ‰ôè(€€€€€€€™É½´Í•½¹‘‰É…¥¸¹¹…Ñ¥Ù”¹‘•Í­Ñ½Á}¡•…±Ñ ¹±¤¥µÁ½ÉÐµ…¥¸…Ì‘•Í­Ñ½Á}¡•…±Ñ¡}µ…¥¸(€€€€€€€É•ÑÕÉ¸‘•Í­Ñ½Á}¡•…±Ñ¡}µ…¥¸¡É…Ü¤(€€€¥˜µ¥¸ì‰Í•ÑÑ¥¹Ìµ•¹Ñ•Èˆ°€‰Í•ÑÑ¥¹Ìµ•¹Ñ•ÈµÕ¤ˆ°€‰Í•ÑÑ¥¹Ìµ•¹Ñ•ÈµÍÑ…ÑÕÌˆ°€‰Í•ÑÑ¥¹Ìµ•¹Ñ•ÈµÍ¹…ÁÍ¡½Ðˆ°€‰Í•ÑÑ¥¹Ìµ•¹Ñ•ÈµÝÉ¥Ñ”µ‘•™…Õ±ÑÌˆ°€‰Í•ÑÑ¥¹Ìµ•¹Ñ•ÈµÍ•Ðˆ°€‰Í•ÑÑ¥¹Ìµ•¹Ñ•Èµ¡¥ÍÑ½Éä‰ôè(€€€€€€€™É½´Í•½¹‘‰É…¥¸¹¹…Ñ¥Ù”¹Í•ÑÑ¥¹Í}•¹Ñ•È¹±¤¥µÁ½ÉÐµ…¥¸…ÌÍ•ÑÑ¥¹Í}•¹Ñ•É}µ…¥¸(€€€€€€€É•ÑÕÉ¸Í•ÑÑ¥¹Í}•¹Ñ•É}µ…¥¸¡É…Ü¤(€€€¥˜µ¥¸ì‰½¹™¥œµÍÑ…ÑÕÌˆ°€‰½¹™¥œµÍ¹…ÁÍ¡½Ðˆ°€‰½¹™¥œµÍ•Ðˆ°€‰½¹™¥œµ‘½Ñ½È‰ôè(€€€€€€€±½…‘}•¹Ù}™¥±” ¤(€€€€€€€™É½´Í•½¹‘‰É…¥¸¹ÉÕ¹Ñ¥µ•}½¹™¥œ¹±¤¥µÁ½ÉÐµ…¥¸…ÌÉÕ¹Ñ¥µ•}½¹™¥}µ…¥¸(€€€€€€€É•ÑÕÉ¸ÉÕ¹Ñ¥µ•}½¹™¥}µ…¥¸¡É…Ü¤(€€€¥˜µ¥¸ì‰…¤µÝ½É­ÍÁ…”ˆ°€‰…¤µÝ½É­ÍÁ…”µÕ¤ˆ°€‰…¤µÝ½É­ÍÁ…”µÍÑ…ÑÕÌˆ°€‰…¤µÝ½É­ÍÁ…”µÍ¹…ÁÍ¡½Ðˆ°€‰…¤µÝ½É­ÍÁ…”µ¹…Ù¥…Ñ¥½¸ˆ°€‰…¤µÝ½É­ÍÁ…”µ…Ñ¥Ù¥Ñäˆ°€‰…¤µÝ½É­ÍÁ…”µÉ•½É‰ôè(€€€€€€€™É½´Í•½¹‘‰É…¥¸¹¹…Ñ¥Ù”¹…¥}Ý½É­ÍÁ…”¹±¤¥µÁ½ÉÐµ…¥¸…Ì…¥}Ý½É­ÍÁ…•}µ…¥¸(€€€€€€€É•ÑÕÉ¸…¥}Ý½É­ÍÁ…•}µ…¥¸¡É…Ü¤(€€€¥˜µ¥¸ì‰¥µÁ½ÉÐµ•¹Ñ•Èˆ°€‰¥µÁ½ÉÐµÍÑ…ÑÕÌˆ°€‰¥µÁ½ÉÐµ¡¥ÍÑ½Éä‰ôè(€€€€€€€™É½´Í•½¹‘‰É…¥¸¹¹…Ñ¥Ù”¹¥µÁ½ÉÑ}•¹Ñ•É}±¤¥µÁ½ÉÐµ…¥¸…Ì¥µÁ½ÉÑ}•¹Ñ•É}µ…¥¸(€€€€€€€É•ÑÕÉ¸¥µÁ½ÉÑ}•¹Ñ•É}µ…¥¸¡É…Ü¤(€€€¥˜µ¥¸ì‰…•¹ÐµÁ±…¸µÉ•…Ñ”ˆ°€‰…•¹ÐµÁ±…¸µÍ¡½Üˆ°€‰…•¹ÐµÁ±…¸µ±¥ÍÐˆ°€‰…•¹ÐµÁ±…¸µ…¹•°ˆ°€‰…•¹ÐµÁ±…¸µÉ•ÍÕµ”‰ôè(€€€€€€€™É½´Í•½¹‘‰É…¥¸¹…•¹Ð¹Á±…¹¹•É}±¤¥µÁ½ÉÐµ…¥¸…Ì…•¹Ñ}Á±…¹}µ…¥¸(€€€€€€€É•ÑÕÉ¸…•¹Ñ}Á±…¹}µ…¥¸¡É…Ü¤(€€€¥˜µ¥¸ì‰Ñ½½°µ±¥ÍÐˆ°€‰Ñ½½°µÍ¡½Üˆ°€‰Ñ½½°µ¡•…±Ñ ˆ°€‰Ñ½½°µÉÕ¸ˆ°€‰Ñ½½°µ‘¥Í…‰±”ˆ°€‰Ñ½½°µ•¹…‰±”‰ôè(€€€€€€€™É½´Í•½¹‘‰É…¥¸¹…•¹Ð¹Ñ½½±}±¤¥µÁ½ÉÐµ…¥¸…ÌÑ½½±}µ…¥¸(€€€€€€€É•ÑÕÉ¸Ñ½½±}µ…¥¸¡É…Ü¤(€€€¥˜µ¥¸ì‰‘½Õµ•¹ÐµÁÉ•Ù¥•Üˆ°€‰‘½Õµ•¹ÐµÁÉ•Ù¥•ÜµÕ¤ˆ°€‰‘½Õµ•¹ÐµÁÉ•Ù¥•ÜµÍÑ…ÑÕÌˆ°€‰‘½Õµ•¹ÐµÁÉ•Ù¥•Üµ½Á•¸ˆ°€‰‘½Õµ•¹ÐµÁÉ•Ù¥•Üµµ•Ñ…‘…Ñ„ˆ°€‰‘½Õµ•¹ÐµÁÉ•Ù¥•ÜµÍ•…É ˆ°€‰‘½Õµ•¹ÐµÁÉ•Ù¥•Üµ½Èˆ°€‰‘½Õµ•¹ÐµÁÉ•Ù¥•Üµ…¹¹½Ñ…Ñ”ˆ°€‰‘½Õµ•¹ÐµÁÉ•Ù¥•Üµ…¹¹½Ñ…Ñ¥½¹Ìˆ°€‰‘½Õµ•¹ÐµÁÉ•Ù¥•ÜµÙ•ÉÍ¥½¸µÍ¹…ÁÍ¡½Ðˆ°€‰‘½Õµ•¹ÐµÁÉ•Ù¥•ÜµÙ•ÉÍ¥½¹Ì‰ôè(€€€€€€€™É½´Í•½¹‘‰É…¥¸¹¹…Ñ¥Ù”¹‘½Õµ•¹Ñ}ÁÉ•Ù¥•Ü¹±¤¥µÁ½ÉÐµ…¥¸…Ì‘½Õµ•¹Ñ}ÁÉ•Ù¥•Ý}µ…¥¸(€€€€€€€É•ÑÕÉ¸‘½Õµ•¹Ñ}ÁÉ•Ù¥•Ý}µ…¥¸¡É…Ü¤(€€€¥˜µ¥¸ì‰…¤µ¡…Ðˆ°€‰½¹Ù•ÉÍ…Ñ¥½¸µ±¥ÍÐˆ°€‰½¹Ù•ÉÍ…Ñ¥½¸µ½Á•¸ˆ°€‰½¹Ù•ÉÍ…Ñ¥½¸µ•áÁ½ÉÐˆ°€‰½¹Ù•ÉÍ…Ñ¥½¸µ‘•±•Ñ”ˆ°€‰½¹Ù•ÉÍ…Ñ¥½¸µÁ¥¸ˆ°€‰½¹Ù•ÉÍ…Ñ¥½¸µÍ•…É ˆ°€‰½¹Ù•ÉÍ…Ñ¥½¸µÕ¤‰ôè(€€€€€€€™É½´Í•½¹‘‰É…¥¸¹¹…Ñ¥Ù”¹¡…Ð¥µÁ½ÉÐ½¹Ù•ÉÍ…Ñ¥½¹}±¥}µ…¥¸(€€€€€€€É•ÑÕÉ¸½¹Ù•ÉÍ…Ñ¥½¹}±¥}µ…¥¸¡É…Ü¤(€€€¥˜µ¥¸ì‰Õ¤ˆ°€‰Õ¤µÍÑ…ÉÐˆ°€‰Õ¤µ½Á•¸ˆ°€‰Õ¤µÍÑ…ÑÕÌˆ°€‰Õ¤µ‘½Ñ½Èˆ°€‰Õ¤µÍ¡½ÉÑÕÑÌˆ°€‰Õ¤µ‰½½ÑÍÑÉ…Àˆ°€‰©…ÉÙ¥Ìˆ°€‰‘•Í­Ñ½Àˆ°€‰‘•Í­Ñ½ÀµÕ¤ˆ°€‰‘•Í­Ñ½ÀÄØµÕ¤ˆ°€‰¹…Ñ¥Ù”µÕ¤ˆ°€‰¡Õˆ°€‰Õ¤µÝ•ˆˆ°€‰Ý•ˆµ¡Õ‰ôè(€€€€€€€±½…‘}•¹Ù}™¥±” ¤(€€€€€€€É•ÑÕÉ¸Õ¥}½µµ…¹¡É…Ü¤(€€€¥˜µ€ôô€‰½µµ…¹µ¥¹‘•àˆè(€€€€€€€½ÕÐ¡5½‘Õ±•I•¥ÍÑÉä ¤¹½µµ…¹‘}¥¹‘•à ¤¤(€€€€€€€É•ÑÕÉ¸€À(€€€¥˜µ¥¸ì‰ÍÑ…ÑÕÌˆ°€‰¡•…±Ñ ˆ°€‰µ½‘Õ±”µÍÑ…ÑÕÌˆ°€‰µ½‘Õ±”µ¡•…±Ñ ˆ°€‰µ½‘Õ±•Ì‰ôè(€€€€€€€É•ÑÕÉ¸}±½…±}ÍÑ…ÑÕÌ¡É…Ü¤(€€€¥˜µ¥¸ì‰…ÁÁÉ½Ù…°µ±¥ÍÐˆ°€‰…ÁÁÉ½Ù…°µÍ¡½Üˆ°€‰…ÁÁÉ½Ù…°µ…ÁÁÉ½Ù”ˆ°€‰…ÁÁÉ½Ù…°µÉ•©•Ðˆ°€‰…ÁÁÉ½Ù…°µ…Õ‘¥Ðˆ°€‰…ÁÁÉ½Ù…°µ•áÁ¥É”‰ôè(€€€€€€€™É½´Í•½¹‘‰É…¥¸¹…•¹Ð¹Í…™•Ñä¹±¤¥µÁ½ÉÐµ…¥¸…Ì…ÁÁÉ½Ù…±}µ…¥¸(€€€€€€€É•ÑÕÉ¸…ÁÁÉ½Ù…±}µ…¥¸¡É…Ü¤(€€€¥˜µ¥¸ì‰Ý½É­™±½ÜµÉ•…Ñ”ˆ°€‰Ý½É­™±½ÜµÉÕ¸ˆ°€‰Ý½É­™±½ÜµÍÑ…ÑÕÌˆ°€‰Ý½É­™±½Üµ±¥ÍÐˆ°€‰Ý½É­™±½Üµ…¹•°ˆ°€‰Ý½É­™±½ÜµÉ•ÍÕµ”ˆ°€‰Ý½É­™±½Üµ…Õ‘¥Ðˆ°€‰Ý½É­™±½ÜµÉ½±±‰…¬‰ôè(€€€€€€€™É½´Í•½¹‘‰É…¥¸¹…•¹Ð¹Ý½É­™±½Ü¹±¤¥µÁ½ÉÐµ…¥¸…ÌÝ½É­™±½Ý}µ…¥¸(€€€€€€€É•ÑÕÉ¸Ý½É­™±½Ý}µ…¥¸¡É…Ü¤(€€€¥˜µ¥¸ì‰‰…­É½Õ¹µ…•¹Ðµ±¥ÍÐˆ°€‰‰…­É½Õ¹µ…•¹ÐµÉ•¥ÍÑ•Èˆ°€‰‰…­É½Õ¹µ…•¹ÐµÍÑ…ÉÐˆ°€‰‰…­É½Õ¹µ…•¹ÐµÍÑ½Àˆ°€‰‰…­É½Õ¹µ…•¹ÐµÁ…ÕÍ”ˆ°€‰‰…­É½Õ¹µ…•¹ÐµÍÑ…ÑÕÌˆ°€‰‰…­É½Õ¹µ…•¹ÐµÉÕ¸ˆ°€‰‰…­É½Õ¹µ…•¹ÐµÉÕ¸µ‘Õ”ˆ°€‰‰…­É½Õ¹µ…•¹ÐµÉÕ¹Ì‰ôè(€€€€€€€™É½´Í•½¹‘‰É…¥¸¹…•¹Ð¹‰…­É½Õ¹‘}…•¹ÑÌ¹±¤¥µÁ½ÉÐµ…¥¸…Ì‰…­É½Õ¹‘}…•¹Ñ}µ…¥¸(€€€€€€€É•ÑÕÉ¸‰…­É½Õ¹‘}…•¹Ñ}µ…¥¸¡É…Ü¤(€€€¥˜µ¥¸ì‰…•¹Ðµµ•µ½ÉäµÁÉ•Ù¥•Üˆ°€‰…•¹Ðµµ•µ½Éäµ¥¹©•Ðˆ°€‰…•¹Ðµµ•µ½Éäµ…Õ‘¥Ð‰ôè(€€€€€€€™É½´Í•½¹‘‰É…¥¸¹…•¹Ð¹µ•µ½Éå}¥¹©•Ñ¥½¸¹±¤¥µÁ½ÉÐµ…¥¸…Ì…•¹Ñ}µ•µ½Éå}µ…¥¸(€€€€€€€É•ÑÕÉ¸…•¹Ñ}µ•µ½Éå}µ…¥¸¡É…Ü¤(€€€¥˜µ¥¸ì‰½…°µÉ•…Ñ”ˆ°€‰½…°µ±¥ÍÐˆ°€‰½…°µÍ¡½Üˆ°€‰½…°µÕÁ‘…Ñ”ˆ°€‰½…°µÉ•Á½ÉÐˆ°€‰½…°µ±½Í”‰ôè(€€€€€€€™É½´Í•½¹‘‰É…¥¸¹…•¹Ð¹½…±Ì¹±¤¥µÁ½ÉÐµ…¥¸…Ì½…±}µ…¥¸(€€€€€€€É•ÑÕÉ¸½…±}µ…¥¸¡É…Ü¤(€€€¥˜µ¥¸ì‰…•¹Ðµ½¹ÑÉ½°µ•¹Ñ•Èˆ°€‰…•¹Ðµ½¹ÑÉ½°µ•¹Ñ•ÈµÕ¤ˆ°€‰…•¹Ðµ½¹ÑÉ½°µ•¹Ñ•ÈµÍÑ…ÑÕÌˆ°€‰…•¹Ðµ½¹ÑÉ½°µ…É•„ˆ°€‰…•¹Ðµ½¹ÑÉ½°µÁ±…¸µÉ•…Ñ”ˆ°€‰…•¹Ðµ½¹ÑÉ½°µÁ±…¸µ¥¹ÍÁ•Ðˆ°€‰…•¹Ðµ½¹ÑÉ½°µÁ±…¸µÍÑ…ÉÐˆ°€‰…•¹Ðµ½¹ÑÉ½°µ…ÁÁÉ½Ù”ˆ°€‰…•¹Ðµ½¹ÑÉ½°µÉ•©•Ðˆ°€‰…•¹Ðµ½¹ÑÉ½°µÝ½É­™±½Üˆ°€‰…•¹Ðµ½¹ÑÉ½°µ½…°µÉ•Á½ÉÐˆ°€‰…•¹Ðµ½¹ÑÉ½°µ‰œ‰ôè(€€€€€€€™É½´Í•½¹‘‰É…¥¸¹¹…Ñ¥Ù”¹…•¹Ñ}½¹ÑÉ½°¹±¤¥µÁ½ÉÐµ…¥¸…Ì…•¹Ñ}½¹ÑÉ½±}µ…¥¸(€€€€€€€É•ÑÕÉ¸…•¹Ñ}½¹ÑÉ½±}µ…¥¸¡É…Ü¤(€€€¥˜µ¹ÍÑ…ÉÑÍÝ¥Ñ  ‰µ½‰¥±”ÄØ´ˆ¤è(€€€€€€€É•ÑÕÉ¸}µ½‰¥±•}µ…¥¸¡É…Ü¤(€€€ÑÉäè(€€€€€€€™É½´Í•½¹‘‰É…¥¸¹±…Õ¹¡•É}ÉÕ¹Ñ¥µ•}ØÄÈØ¥µÁ½ÉÐµ…¥¸…ÌÉÕ¹Ñ¥µ•}µ…¥¸(€€€€€€€É•ÑÕÉ¸ÉÕ¹Ñ¥µ•}µ…¥¸¡}ÍÑÉ¥Á}Õ¹¡…¹‘±•‘}±½‰…±}½ÁÑ¥½¹Ì¡É…Ü°ìˆ´µÁÉ½©•ÐµÉ½½Ðˆ°€ˆ´µÁÉ½™¥±”‰ô¤¤(€€€•á•ÁÐMåÍÑ•µá¥Ð…Ì•áŒè(€€€€€€€É•ÑÕÉ¸¥¹Ð¡•áŒ¹½‘”½È€À¤(()¥˜}}¹…µ•}|€ôô€‰}}µ…¥¹}|ˆè(€€€É…¥Í”MåÍÑ•µá¥Ð¡µ…¥¸ ¤¤(