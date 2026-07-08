from __future__ import annotations

from secondbrain.agent.memory_injection import MemoryInjector, MemoryQuery

from tests._mem_helpers import make_record, make_store


def test_secret_never_injected_via_metadata_flag(tmp_path):
    store = make_store([
        make_record("Normaler Fakt", source="a"),
        make_record("Der SAP Login", source="b", metadata={"secret": True}),
    ])
    ctx = MemoryInjector(store).preview(MemoryQuery(text=""))
    texts = [e.text for e in ctx.evidences]
    assert "Der SAP Login" not in texts
    assert any(x.reason == "secret" for x in ctx.exclusions)


def test_secret_never_injected_via_text_pattern(tmp_path):
    store = make_store([
        make_record("Mein Key ist sk-abcdefghijklmnop1234", source="a"),
        make_record("Harmloser Fakt", source="b"),
    ])
    ctx = MemoryInjector(store).preview(MemoryQuery(text=""))
    assert [e.text for e in ctx.evidences] == ["Harmloser Fakt"]


def test_secret_excluded_even_if_highly_relevant(tmp_path):
    store = make_store([
        make_record("SAP SAP SAP password=hunter2", source="a", tags=("secret",)),
    ])
    ctx = MemoryInjector(store).preview(MemoryQuery(text="SAP"))
    assert ctx.evidences == []
    assert any(x.reason == "secret" for x in ctx.exclusions)


def test_privacy_mode_withholds_private_visibility(tmp_path):
    store = make_store([
        make_record("Oeffentlicher Fakt", source="a", visibility="public"),
        make_record("Privater Fakt", source="b", visibility="private"),
    ])
    ctx = MemoryInjector(store).preview(MemoryQuery(text="", privacy_mode=True))
    texts = [e.text for e in ctx.evidences]
    assert "Oeffentlicher Fakt" in texts
    assert "Privater Fakt" not in texts
    assert any(x.reason == "privacy_mode" for x in ctx.exclusions)


def test_privacy_mode_withholds_personal_tag(tmp_path):
    store = make_store([
        make_record("Team Info", source="a", visibility="public"),
        make_record("Gesundheitsdaten", source="b", visibility="public", tags=("personal",)),
    ])
    ctx = MemoryInjector(store).preview(MemoryQuery(text="", privacy_mode=True))
    assert "Gesundheitsdaten" not in [e.text for e in ctx.evidences]


def test_private_allowed_when_privacy_mode_off(tmp_path):
    store = make_store([
        make_record("Privater Fakt", source="b", visibility="private"),
    ])
    ctx = MemoryInjector(store).preview(MemoryQuery(text="", privacy_mode=False))
    assert [e.text for e in ctx.evidences] == ["Privater Fakt"]


def test_context_marks_privacy_mode(tmp_path):
    store = make_store([make_record("x", source="a")])
    ctx = MemoryInjector(store).preview(MemoryQuery(text="", privacy_mode=True))
    assert ctx.to_dict()["privacy_mode"] is True
