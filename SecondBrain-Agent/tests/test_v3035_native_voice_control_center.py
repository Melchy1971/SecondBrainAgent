from secondbrain.native.voice_control_center import parse_german_voice_command, run_voice_command, voice_center_status


def test_status_command_is_german():
    result = parse_german_voice_command("Jarvis Status")
    assert result.ok is True
    assert result.intent == "status"
    assert result.requires_confirmation is False


def test_write_command_requires_confirmation():
    result = parse_german_voice_command("Jarvis repariere Index")
    assert result.ok is True
    assert result.intent == "index_repair"
    assert result.requires_confirmation is True


def test_search_command_maps_to_document_search():
    result = parse_german_voice_command("Suche Rechnung Telekom")
    assert result.ok is True
    assert result.intent == "search"
    assert result.action == "document-explorer-search"


def test_unknown_command_is_rejected():
    result = parse_german_voice_command("Jarvis mach irgendwas")
    assert result.ok is False
    assert result.intent == "unknown"


def test_status_shape():
    status = voice_center_status()
    assert status["ok"] is True
    assert status["language"] == "de-DE"


def test_run_voice_command_serializable():
    payload = run_voice_command("Jarvis öffne Dokumente", record=False)
    assert payload["ok"] is True
    assert payload["intent"] == "open_documents"
