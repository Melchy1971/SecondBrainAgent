import argparse
import json
from secondbrain.long_term_memory import LongTermMemoryRuntime


def out(obj):
    print(json.dumps(obj, indent=2, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(prog="secondbrain", description="SecondBrain OS v16.6 Long-Term Memory launcher")
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--db-path", default=None)
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("mem16-migrate")
    sub.add_parser("mem16-status")
    sub.add_parser("mem16-seed")
    p = sub.add_parser("mem16-episode-add")
    p.add_argument("title")
    p.add_argument("what")
    p.add_argument("--outcome", default="")
    p.add_argument("--importance", type=float, default=0.5)
    p.add_argument("--emotion", type=float, default=0.0)
    p = sub.add_parser("mem16-fact-add")
    p.add_argument("entity")
    p.add_argument("attribute")
    p.add_argument("value")
    p.add_argument("--confidence", type=float, default=0.6)
    p = sub.add_parser("mem16-procedure-add")
    p.add_argument("name")
    p.add_argument("steps_json")
    p = sub.add_parser("mem16-procedure-result")
    p.add_argument("procedure_id")
    p.add_argument("--success", choices=["true", "false"], default="true")
    p = sub.add_parser("mem16-recall")
    p.add_argument("query")
    p.add_argument("--type", default="all")
    p = sub.add_parser("mem16-link")
    p.add_argument("source_type")
    p.add_argument("source_id")
    p.add_argument("target_type")
    p.add_argument("target_id")
    p.add_argument("relation")
    sub.add_parser("mem16-consolidate")
    sub.add_parser("mem16-importance")
    sub.add_parser("mem16-graph-export")

    args = parser.parse_args()
    rt = LongTermMemoryRuntime(args.project_root, args.db_path)

    if args.cmd == "mem16-migrate": out(rt.migrate())
    elif args.cmd == "mem16-status": out(rt.status())
    elif args.cmd == "mem16-seed": out(rt.seed_demo())
    elif args.cmd == "mem16-episode-add": out(rt.add_episode(args.title, args.what, outcome=args.outcome, importance=args.importance, emotion_weight=args.emotion))
    elif args.cmd == "mem16-fact-add": out(rt.add_fact(args.entity, args.attribute, args.value, args.confidence))
    elif args.cmd == "mem16-procedure-add": out(rt.add_procedure(args.name, json.loads(args.steps_json)))
    elif args.cmd == "mem16-procedure-result": out(rt.record_procedure_result(args.procedure_id, args.success == "true"))
    elif args.cmd == "mem16-recall": out(rt.recall(args.query, args.type))
    elif args.cmd == "mem16-link": out(rt.link(args.source_type, args.source_id, args.target_type, args.target_id, args.relation))
    elif args.cmd == "mem16-consolidate": out(rt.consolidate())
    elif args.cmd == "mem16-importance": out(rt.importance_report())
    elif args.cmd == "mem16-graph-export": out(rt.graph_export())


if __name__ == "__main__":
    main()
