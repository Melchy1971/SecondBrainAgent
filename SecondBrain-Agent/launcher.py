import argparse, json
from secondbrain.mobile_app import MobileAppRuntime


def out(obj):
    print(json.dumps(obj, indent=2, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(prog="secondbrain", description="SecondBrain OS v12.8 Mobile App Foundation launcher")
    parser.add_argument("--project-root", default=".")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("mobile2-status")
    p = sub.add_parser("mobile2-register")
    p.add_argument("device_id"); p.add_argument("name"); p.add_argument("--platform", default="ios"); p.add_argument("--trusted", action="store_true"); p.add_argument("--biometric", action="store_true")
    sub.add_parser("mobile2-devices")
    p = sub.add_parser("mobile2-command")
    p.add_argument("device_id"); p.add_argument("command"); p.add_argument("--payload", default="{}")
    sub.add_parser("mobile2-queue")
    sub.add_parser("mobile2-drain")
    p = sub.add_parser("mobile2-push")
    p.add_argument("title"); p.add_argument("body"); p.add_argument("--device-id", default=None); p.add_argument("--priority", default="normal")
    sub.add_parser("mobile2-push-outbox")
    sub.add_parser("mobile2-widgets")
    p = sub.add_parser("mobile2-widget-enable")
    p.add_argument("widget_id"); p.add_argument("enabled", choices=["true", "false"])
    p = sub.add_parser("mobile2-sync")
    p.add_argument("device_id")

    args = parser.parse_args()
    mobile = MobileAppRuntime(args.project_root)

    if args.cmd == "mobile2-status":
        out(mobile.status())
    elif args.cmd == "mobile2-register":
        out(mobile.devices.register(args.device_id, args.name, args.platform, args.trusted, args.biometric))
    elif args.cmd == "mobile2-devices":
        out(mobile.devices.list_devices())
    elif args.cmd == "mobile2-command":
        out(mobile.secure_command(args.device_id, args.command, json.loads(args.payload)))
    elif args.cmd == "mobile2-queue":
        out(mobile.queue.items())
    elif args.cmd == "mobile2-drain":
        out(mobile.queue.drain())
    elif args.cmd == "mobile2-push":
        out(mobile.push.send(args.title, args.body, args.device_id, args.priority))
    elif args.cmd == "mobile2-push-outbox":
        out(mobile.push.list())
    elif args.cmd == "mobile2-widgets":
        out(mobile.widgets.widgets())
    elif args.cmd == "mobile2-widget-enable":
        out(mobile.widgets.set_enabled(args.widget_id, args.enabled == "true"))
    elif args.cmd == "mobile2-sync":
        out(mobile.syncer.sync(args.device_id))


if __name__ == "__main__":
    main()
