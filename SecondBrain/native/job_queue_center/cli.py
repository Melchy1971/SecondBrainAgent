from __future__ import annotations

import argparse
import json
from pathlib import Path

from .service import JobQueueService


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="job-queue-center")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("status")
    add = sub.add_parser("add")
    add.add_argument("kind")
    add.add_argument("title")
    add.add_argument("--priority", type=int, default=50)
    add.add_argument("--approval-required", action="store_true")
    list_p = sub.add_parser("list")
    list_p.add_argument("--status")
    list_p.add_argument("--kind")
    run = sub.add_parser("run")
    run.add_argument("job_id")
    approve = sub.add_parser("approve")
    approve.add_argument("job_id")
    cancel = sub.add_parser("cancel")
    cancel.add_argument("job_id")
    sub.add_parser("clear-finished")
    return parser


def main(argv: list[str] | None = None, *, root: str | Path | None = None) -> int:
    args = build_parser().parse_args(argv)
    service = JobQueueService(root=root)
    if args.cmd == "status":
        print(json.dumps(service.snapshot(), ensure_ascii=False, indent=2))
        return 0
    if args.cmd == "add":
        job = service.add_job(args.kind, args.title, priority=args.priority, approval_required=args.approval_required)
        print(json.dumps(job.to_dict(), ensure_ascii=False, indent=2))
        return 0
    if args.cmd == "list":
        jobs = service.list_jobs(status=args.status, kind=args.kind)
        print(json.dumps([job.to_dict() for job in jobs], ensure_ascii=False, indent=2))
        return 0
    if args.cmd == "run":
        job = service.update_status(args.job_id, "running")
        print(json.dumps(job.to_dict(), ensure_ascii=False, indent=2))
        return 0
    if args.cmd == "approve":
        job = service.approve(args.job_id)
        print(json.dumps(job.to_dict(), ensure_ascii=False, indent=2))
        return 0
    if args.cmd == "cancel":
        job = service.cancel(args.job_id)
        print(json.dumps(job.to_dict(), ensure_ascii=False, indent=2))
        return 0
    if args.cmd == "clear-finished":
        print(json.dumps({"removed": service.clear_finished()}, ensure_ascii=False, indent=2))
        return 0
    return 2


def launcher_main(argv: list[str] | None = None) -> int:
    """Translate stable launcher aliases to the queue center subcommands."""
    raw = list(argv or [])
    aliases = {
        "job-queue-status": "status",
        "job-queue-add": "add",
        "job-queue-list": "list",
        "job-queue-run": "run",
        "job-queue-approve": "approve",
        "job-queue-cancel": "cancel",
        "job-queue-clear-finished": "clear-finished",
    }
    command_index = next((index for index, value in enumerate(raw) if value in aliases or value == "job-queue-center-gui"), None)
    if command_index is None:
        return 2
    command = raw[command_index]
    project_root = Path.cwd()
    if "--project-root" in raw:
        index = raw.index("--project-root")
        if index + 1 < len(raw):
            project_root = Path(raw[index + 1])
        del raw[index:index + 2]
    del raw[command_index]
    if command == "job-queue-center-gui":
        from .gui import launch
        launch(project_root)
        return 0
    return main([aliases[command], *raw], root=project_root)


if __name__ == "__main__":
    raise SystemExit(main())
