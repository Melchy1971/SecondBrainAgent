from pathlib import Path
import sys
import importlib.util

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from secondbrain.config import load_settings

def check_package(name: str) -> bool:
    return importlib.util.find_spec(name) is not None

def main():
    settings = load_settings(PROJECT_ROOT)

    checks = []
    checks.append(("Python >= 3.10", sys.version_info >= (3, 10)))
    checks.append(("Vault existiert", Path(settings["vault_path"]).exists()))
    checks.append(("Inbox existiert", Path(settings["inbox_path"]).exists()))
    checks.append(("Agent existiert", PROJECT_ROOT.exists()))
    checks.append(("pypdf installiert", check_package("pypdf")))
    checks.append(("requests installiert", check_package("requests")))
    checks.append(("beautifulsoup4 installiert", check_package("bs4")))

    print("SecondBrain-Agent Healthcheck")
    print("")

    ok_all = True
    for name, ok in checks:
        status = "OK" if ok else "FEHLT"
        print(f"{status:6} {name}")
        if not ok and name in ["Python >= 3.10", "Vault existiert", "Inbox existiert", "Agent existiert"]:
            ok_all = False

    print("")
    if ok_all:
        print("Status: startfähig")
    else:
        print("Status: blockiert. Fehlende Pflichtpunkte beheben.")

    print("")
    print("Optionale Pakete installieren:")
    print("pip install pypdf requests beautifulsoup4")

if __name__ == "__main__":
    main()
