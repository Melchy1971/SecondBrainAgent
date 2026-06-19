from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]

def run(script, *args):
    subprocess.run([sys.executable, str(ROOT / "scripts" / script), *args], cwd=str(ROOT))

def main():
    while True:
        print("")
        print("SecondBrain OS v10.3 Voice Layer")
        print("1 = Import AI Exports")
        print("2 = v10.2 GUI Cycle")
        print("3 = v10.3 Voice Layer Cycle")
        print("4 = Voice Status")
        print("5 = Diktat importieren")
        print("6 = Voice Command prüfen")
        print("7 = Voice Command ausführen")
        print("8 = Jarvis GUI starten")
        print("9 = RAG Antwort mit Ollama")
        print("10 = Path Check v9")
        print("0 = Beenden")
        choice = input("Auswahl: ").strip()

        if choice == "1":
            run("import_ai_exports.py")
        elif choice == "2":
            run("run_v102_cycle.py")
        elif choice == "3":
            run("run_v103_cycle.py")
        elif choice == "4":
            run("voice_status_v103.py")
        elif choice == "5":
            p = input("Diktat-Datei oder leer für Ordnerimport: ").strip().strip('"')
            if p:
                run("import_dictation_v103.py", p)
            else:
                run("import_dictation_v103.py")
        elif choice == "6":
            cmd = input("Befehl: ").strip()
            run("voice_command_v103.py", cmd)
        elif choice == "7":
            cmd = input("Befehl: ").strip()
            run("voice_command_v103.py", cmd, "--execute")
        elif choice == "8":
            run("start_gui.py")
        elif choice == "9":
            q = input("Frage: ").strip()
            run("rag_answer.py", q)
        elif choice == "10":
            run("check_paths_v9.py")
        elif choice == "0":
            break
        else:
            print("Ungültige Auswahl.")

if __name__ == "__main__":
    main()
