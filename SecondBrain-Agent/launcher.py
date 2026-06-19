import argparse, json
from secondbrain.learning import LearningEngine


def out(obj):
    print(json.dumps(obj, indent=2, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(prog="secondbrain", description="SecondBrain OS v12.9 Learning Engine launcher")
    parser.add_argument("--project-root", default=".")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("learn-status")
    p = sub.add_parser("learn-experience")
    p.add_argument("task")
    p.add_argument("outcome")
    p.add_argument("--success", action="store_true")
    p.add_argument("--capability", default="general")
    p.add_argument("--duration", type=float, default=0.0)
    p.add_argument("--error", default=None)

    sub.add_parser("learn-experiences")
    sub.add_parser("learn-metrics")
    sub.add_parser("learn-reflect")
    sub.add_parser("learn-backlog-create")
    sub.add_parser("learn-backlog")
    p = sub.add_parser("learn-episode")
    p.add_argument("title")
    p.add_argument("summary")
    p.add_argument("--experience-ids", default="")

    args = parser.parse_args()
    engine = LearningEngine(args.project_root)

    if args.cmd == "learn-status":
        out(engine.status())
    elif args.cmd == "learn-experience":
        out(engine.add_experience(args.task, args.outcome, args.success, args.capability, args.duration, args.error))
    elif args.cmd == "learn-experiences":
        out(engine.experiences.list())
    elif args.cmd == "learn-metrics":
        out(engine.metrics.compute())
    elif args.cmd == "learn-reflect":
        out(engine.reflect())
    elif args.cmd == "learn-backlog-create":
        out(engine.create_backlog_from_reflection())
    elif args.cmd == "learn-backlog":
        out(engine.backlog.list())
    elif args.cmd == "learn-episode":
        ids = [x.strip() for x in args.experience_ids.split(",") if x.strip()]
        out(engine.episodes.create(args.title, ids, args.summary))


if __name__ == "__main__":
    main()
