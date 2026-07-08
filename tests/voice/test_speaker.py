from secondbrain.voice.speaker import SpeakerProfileStore, SpeakerMatcher, cosine
from secondbrain.voice.engines.fake import FakeSpeakerEmbedder
from secondbrain.voice.ports import Audio


def _matcher(tmp_path, threshold=0.75):
    embedder = FakeSpeakerEmbedder({b"markus": [1.0, 0.0, 0.0], b"anna": [0.0, 1.0, 0.0]})
    store = SpeakerProfileStore(str(tmp_path / "speakers.json"))
    return SpeakerMatcher(embedder, store, threshold=threshold), store


def test_cosine_basic():
    assert cosine([1, 0], [1, 0]) == 1.0
    assert cosine([1, 0], [0, 1]) == 0.0


def test_enroll_and_identify_known(tmp_path):
    m, _ = _matcher(tmp_path)
    m.enroll("markus", "Markus", [Audio(b"markus")])
    sid = m.identify(Audio(b"markus"))
    assert sid.id == "markus" and sid.score == 1.0


def test_identify_unknown_below_threshold(tmp_path):
    m, _ = _matcher(tmp_path)
    m.enroll("markus", "Markus", [Audio(b"markus")])
    sid = m.identify(Audio(b"stranger"))
    assert sid.id == "unknown"


def test_profile_store_persists(tmp_path):
    m, store = _matcher(tmp_path)
    m.enroll("anna", "Anna", [Audio(b"anna")])
    reopened = SpeakerProfileStore(str(tmp_path / "speakers.json"))
    assert reopened.get("anna")["label"] == "Anna"
