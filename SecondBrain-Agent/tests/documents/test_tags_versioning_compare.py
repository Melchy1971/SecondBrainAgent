from secondbrain.documents.tags import TagStore
from secondbrain.documents.versioning import VersionStore
from secondbrain.documents.compare import diff_documents


def test_tags_add_remove_find(tmp_path):
    store = TagStore(tmp_path / "tags.json")
    store.add("doc1", "invoice", "2026")
    store.add("doc2", "invoice")
    assert store.get("doc1") == ["2026", "invoice"]
    assert store.find_by_tag("invoice") == ["doc1", "doc2"]
    store.remove("doc1", "2026")
    assert store.get("doc1") == ["invoice"]
    # persisted
    assert TagStore(tmp_path / "tags.json").get("doc2") == ["invoice"]


def test_versioning_dedups_and_orders():
    vs = VersionStore()
    v1 = vs.add_version("d", "hello")
    v_same = vs.add_version("d", "hello")     # unchanged -> same version
    v2 = vs.add_version("d", "hello world")
    assert v1.version == 1 and v_same.version == 1 and v2.version == 2
    assert [v.version for v in vs.list("d")] == [1, 2]
    assert vs.content("d", 2) == "hello world"
    assert vs.latest("d").version == 2


def test_compare_documents():
    r = diff_documents("a\nb\nc", "a\nB\nc")
    assert r["added"] == 1 and r["removed"] == 1 and r["identical"] is False
    assert diff_documents("x", "x")["identical"] is True
    assert 0.0 <= r["similarity"] <= 1.0
