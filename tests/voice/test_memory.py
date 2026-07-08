from secondbrain.voice.memory import VoiceMemory, VoiceMemoryStore
from secondbrain.voice.speaker import SpeakerProfileStore, SpeakerMatcher
from secondbrain.voice.engines.fake import FakeSpeakerEmbedder
from secondbrain.voice.ports import Audio, Transcript, TranscriptSegment
from secondbrain.connectors.import_bridge import InMemoryImportJobSink


def _t(text): return Transcript.from_segments([TranscriptSegment(text, 0, 1, 0.9)])


def test_remember_appends_and_ingests(tmp_path):
    store = VoiceMemoryStore(str(tmp_path / "mem.json"))
    sink = InMemoryImportJobSink()
    vm = VoiceMemory(store, sink=sink)
    res = vm.remember(_t("kaufe milch"), source_uri="audio://n1")
    assert res["import"]["imported"] == 1
    assert store.all()[0]["text"] == "kaufe milch"
    reopened = VoiceMemoryStore(str(tmp_path / "mem.json"))
    assert len(reopened.all()) == 1


def test_remember_attributes_speaker(tmp_path):
    emb = FakeSpeakerEmbedder({b"markus": [1.0, 0.0, 0.0]})
    matcher = SpeakerMatcher(emb, SpeakerProfileStore(), threshold=0.75)
    matcher.enroll("markus", "Markus", [Audio(b"markus")])
    sink = InMemoryImportJobSink()
    vm = VoiceMemory(VoiceMemoryStore(), sink=sink, matcher=matcher)
    res = vm.remember(_t("notiz"), audio=Audio(b"markus"), source_uri="audio://n2")
    assert res["record"]["speaker"] == "markus"
    job = list(sink.jobs.values())[0]
    assert job.metadata["speaker"] == "markus"
