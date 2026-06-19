from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]

def run(script, *args):
    subprocess.run([sys.executable, str(ROOT / "scripts" / script), *args], cwd=str(ROOT))

def main():
    while True:
        print("")
        print("SecondBrain OS v9.7 AI Copilot")
        print("1 = Import AI Exports")
        print("2 = SecondBrain v9.5 Cycle")
        print("3 = SecondBrain v9.7 AI Copilot Cycle")
        print("4 = RAG Antwort mit Ollama")
        print("5 = Installer Check v9.6")
        print("6 = Production Ready Gate v9.6")
        print("7 = Path Check v9")
        print("8 = Regression Tests v9")
        print("9 = Pfade anzeigen")
        print("0 = Beenden")
        choice = input("Auswahl: ").strip()

        if choice == "1":
            run("import_ai_exports.py")
        elif choice == "2":
            run("run_v95_cycle.py")
        elif choice == "3":
            run("run_v97_cycle.py")
        elif choice == "4":
            q = input("Frage: ").strip()
            run("rag_answer.py", q)
        elif choice == "5":
            run("installer_check_v96.py")
        elif choice == "6":
            run("production_ready_gate_v96.py")
        elif choice == "7":
            run("check_paths_v9.py")
        elif choice == "8":
            run("run_regression_tests_v9.py")
        elif choice == "9":
            print("Vault: H:\\SecondBrainAgent\\SecondBrain")
            print("Inbox: H:\\SecondBrainAgent\\SecondBrain-Inbox")
            print("Agent: H:\\SecondBrainAgent\\SecondBrain-Agent")
        elif choice == "0":
            break
        else:
            print("Ungültige Auswahl.")

if __name__ == "__main__":
    main()
