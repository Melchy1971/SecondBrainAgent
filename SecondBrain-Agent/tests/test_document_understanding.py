from secondbrain.document_understanding import DocumentUnderstandingRuntime


def test_status(tmp_path):
    rt = DocumentUnderstandingRuntime(tmp_path)
    assert rt.status()["version"] == "16.3"


def test_ingest_text(tmp_path):
    rt = DocumentUnderstandingRuntime(tmp_path)
    result = rt.ingest_text("Jarvis Plan", "Jarvis nutzt Gmail und GitHub. SecondBrain speichert Wissen.")
    assert result["chunks"] == 1
    assert result["entities"] >= 3


def test_search_citations_entities(tmp_path):
    rt = DocumentUnderstandingRuntime(tmp_path)
    doc = rt.ingest_text("Connector Plan", "Gmail Connector synchronisiert E-Mails.")
    assert rt.search("gmail")
    assert rt.entities(doc["document_id"])
    assert rt.citations(doc["document_id"])


def test_ingest_file_txt(tmp_path):
    f = tmp_path / "note.txt"
    f.write_text("Jarvis Dokumentenverständnis", encoding="utf-8")
    rt = DocumentUnderstandingRuntime(tmp_path)
    result = rt.ingest_file(f)
    assert result["ok"] is True


def test_answer_stub(tmp_path):
    rt = DocumentUnderstandingRuntime(tmp_path)
    rt.ingest_text("RAG", "SecondBrain nutzt RAG mit Zitaten.")
    answer = rt.answer_stub("RAG")
    assert answer["matches"] >= 1
