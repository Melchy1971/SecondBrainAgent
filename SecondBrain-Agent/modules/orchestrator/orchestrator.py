from pathlib import Path
from secondbrain.config import load_settings
from secondbrain.importers import read_input_file
from secondbrain.classifier import classify_text
from secondbrain.tags import generate_tags
from secondbrain.markdown import write_note
from secondbrain.duplicates import is_processed, mark_processed
from secondbrain.journal import append_journal
from secondbrain.digest import write_digest
from secondbrain.graph import update_graph
from secondbrain.reports import write_import_report
from secondbrain.logger import log, log_error
from secondbrain.extractor import extract_tasks
from secondbrain.task_writer import write_task_files
from secondbrain.archive import archive_source
from secondbrain.claude_review import write_review_item
from secondbrain.backup import create_backup
from secondbrain.dashboard import write_dashboard
from secondbrain.weighted_graph import update_weighted_graph
from secondbrain.recommendations import write_recommendations

def run_once(project_root: Path) -> list[dict]:
    settings = load_settings(project_root)
    inbox = Path(settings["inbox_path"])
    providers = settings.get("providers", {})

    imported = []
    log(project_root, "Importlauf gestartet")

    if settings.get("backup_before_import", True):
        backup = create_backup(project_root)
        log(project_root, f"Backup erstellt: {backup}")

    for provider, cfg in providers.items():
        if isinstance(cfg, dict) and not cfg.get("enabled", True):
            continue

        folder = cfg.get("inbox_folder", provider) if isinstance(cfg, dict) else provider
        provider_dir = inbox / folder
        provider_dir.mkdir(parents=True, exist_ok=True)

        for source in provider_dir.rglob("*"):
            if not source.is_file() or source.name.startswith("."):
                continue

            try:
                if settings.get("duplicate_detection", True) and is_processed(project_root, source):
                    log(project_root, f"Übersprungen: {source}")
                    if settings.get("archive_processed", False):
                        archive_source(project_root, source, "processed")
                    continue

                text = read_input_file(source)
                note_type = classify_text(text, provider)
                tags = generate_tags(text) if settings.get("auto_tags", True) else []
                target = write_note(settings, note_type, provider, source, text, tags)

                tasks = extract_tasks(text)
                task_files = write_task_files(settings, target, tasks, provider)

                mark_processed(project_root, source, target)

                item = {
                    "source": str(source),
                    "target": str(target),
                    "provider": provider,
                    "type": note_type,
                    "tags": tags,
                    "task_files": [str(p) for p in task_files],
                }
                imported.append(item)

                if note_type in ["inbox", "source"] or not tags:
                    write_review_item(settings, target, note_type, "Automatische Einordnung unsicher oder Tags fehlen.")

                if settings.get("archive_processed", False):
                    archive_source(project_root, source, "processed")

                log(project_root, f"Importiert: {source} -> {target}")

            except Exception as exc:
                log_error(project_root, f"{source}: {exc}")
                try:
                    archive_source(project_root, source, "failed")
                except Exception:
                    pass

    append_journal(settings, imported)
    write_digest(settings, imported)
    update_graph(settings, imported)
    if settings.get("weighted_graph", True):
        update_weighted_graph(settings)
    if settings.get("recommendations_enabled", True):
        write_recommendations(settings)
    write_import_report(settings, imported, project_root)
    write_dashboard(settings, project_root, imported)

    log(project_root, f"Importlauf beendet. Neue Dateien: {len(imported)}")
    return imported
