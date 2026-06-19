from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]

def run(script, *args):
    subprocess.run([sys.executable, str(ROOT / "scripts" / script), *args], cwd=str(ROOT))

def main():
    while True:
        print("")
        print("SecondBrain OS v9.6 Production Ready")
        print("1 = Import AI Exports")
        print("2 = SecondBrain v9.5 Cycle")
        print("3 = Installer Check v9.6")
        print("4 = Update Backup v9.6")
        print("5 = Settings Report v9.6")
        print("6 = Production Ready Gate v9.6")
        print("7 = Update Preflight v9.6")
        print("8 = Vector RAG Index bauen")
        print("9 = RAG Antwort mit Ollama")
        print("10 = Path Check v9")
        print("11 = Regression Tests v9")
        print("12 = Pfade anzeigen")
        print("0 = Beenden")
        choice = input("Auswahl: ").strip()

        if choice == "1":
            run("import_ai_exports.py")
        elif choice == "2":
            run("run_v95_cycle.py")
        elif choice == "3":
            run("installer_check_v96.py")
        elif choice == "4":
            run("create_update_backup_v96.py")
        elif choice == "5":
            run("settings_report_v96.py")
        elif choice == "6":
            run("production_ready_gate_v96.py")
        elif choice == "7":
            run("update_preflight_v96.py")
        elif choice == "8":
            run("build_vector_rag.py")
        elif choice == "9":
            q = input("Frage: ").strip()
            run("rag_answer.py", q)
        elif choice == "10":
            run("check_paths_v9.py")
        elif choice == "11":
            run("run_regression_tests_v9.py")
        elif choice == "12":
            print("Vault: H:\\SecondBrainAgent\\SecondBrain")
            print("Inbox: H:\\SecondBrainAgent\\SecondBrain-Inbox")
            print("Agent: H:\\SecondBrainAgent\\SecondBrain-Agent")
        elif choice == "0":
            break
        else:
            print("Ungültige Auswahl.")

if __name__ == "__main__":
    main()
