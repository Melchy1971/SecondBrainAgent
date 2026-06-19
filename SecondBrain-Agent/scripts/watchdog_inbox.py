from pathlib import Path
import sys
import subprocess
import time

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from secondbrain.config import load_settings

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
except Exception:
    print("watchdog fehlt. Installation: pip install watchdog")
    raise SystemExit(1)

class Handler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory:
            print("Neue Datei erkannt:", event.src_path)
            subprocess.run([sys.executable, str(PROJECT_ROOT / "scripts" / "run_once.py")], cwd=str(PROJECT_ROOT))

if __name__ == "__main__":
    settings = load_settings(PROJECT_ROOT)
    inbox = Path(settings["inbox_path"])
    inbox.mkdir(parents=True, exist_ok=True)

    observer = Observer()
    observer.schedule(Handler(), str(inbox), recursive=True)
    observer.start()

    print(f"Watchdog aktiv: {inbox}")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
