from secondbrain.desktop_native.dialog_prompts import dialog_prompt


def test_slot_prompts_follow_missing_slot_order():
    assert dialog_prompt({"status": "slots_required", "missing": ["title", "when"]}) == "Wie lautet der Titel?"
    assert dialog_prompt({"status": "slots_required", "missing": ["when"]}) == "Wann soll der Termin stattfinden?"


def test_task_completion_prompt_requests_a_reference():
    assert dialog_prompt({"status": "slots_required", "missing": ["task"]}) == (
        "Welche Aufgabe soll abgeschlossen werden?"
    )


def test_task_rename_prompt_requests_the_new_title():
    assert dialog_prompt({"status": "slots_required", "missing": ["task"], "action_id": "tasks.rename"}) == (
        "Welche Aufgabe soll umbenannt werden?"
    )
    assert dialog_prompt({"status": "slots_required", "missing": ["new_title"]}) == (
        "Wie soll die Aufgabe künftig heißen?"
    )


def test_task_archive_prompt_is_action_specific():
    assert dialog_prompt({"status": "slots_required", "missing": ["task"], "action_id": "tasks.archive"}) == (
        "Welche Aufgabe soll archiviert werden?"
    )


def test_confirmation_prompt_supports_spoken_yes_and_cancel():
    prompt = dialog_prompt({"status": "confirmation_required", "action_id": "documents.import"})
    assert "Sage Ja" in prompt
    assert "Abbrechen" in prompt


def test_approval_prompt_never_contains_payload_values():
    result = {
        "status": "approval_required",
        "action_id": "mail.send",
        "recipient": "secret@example.test",
        "body": "vertraulicher Inhalt",
    }
    prompt = dialog_prompt(result)
    assert prompt == "Die Aktion wartet auf eine Freigabe im Approval Center."
    assert "secret" not in prompt
    assert "vertraulich" not in prompt


def test_cancel_and_slot_error_have_clear_prompts():
    assert dialog_prompt({"status": "dialog_cancelled"}) == "Dialog abgebrochen."
    assert "fehlende Angabe" in dialog_prompt({"status": "error", "error": "slot_value_required"})
    assert dialog_prompt({"status": "executed"}) is None
