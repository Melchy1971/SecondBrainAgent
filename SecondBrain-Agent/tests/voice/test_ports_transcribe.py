from secondbrain.voice.ports import Transcript, TranscriptSegment, Audio, AudioClip
from secondbrain.voice.transcribe import VoiceTranscriber, transcript_to_item, SOURCE
from secondbrain.voice.engines.fake import FakeSttEngine
from secondbrain.connectors.adapter_contract import ConnectorItem
from secondbrain.connectors.import_bridge import InMemoryImportJobSink


def test_transcript_from_segments_aggregates():
    t = Transcript.from_segments([TranscriptSegment("hello", 0, 1, 0.8),
                                  TranscriptSegment("world", 1, 2, 0.6)])
    assert t.text == "hello world"
    assert abs(t.mean_confidence - 0.7) < 1e-9


def test_transcript_to_item_is_connector_item():
    t = Transcript.from_segments([TranscriptSegment("Buy milk. And eggs", 0, 2, 0.9)], language="en")
    item = transcript_to_item(t, source_uri="file:///note.wav")
    assert isinstance(item, ConnectorItem)
    assert item.source == SOURCE
    assert item.title.startswith("Buy milk")
    assert item.metadata["language"] == "en"


def test_transcriber_ingests_into_sink():
    sink = InMemoryImportJobSink()
    r = VoiceTranscriber(FakeSttEngine("erste. zweite"), sink=sink).transcribe(
        Audio(b"x", source_uri="file:///a.wav"))
    assert r["transcript"]["text"] == "erste zweite"
    assert r["import"]["imported"] == 1
    assert len(sink.jobs) == 1


def test_audioclip_write(tmp_path):
    p = tmp_path / "o.wav"
    AudioClip(b"RIFFdata").write(p)
    assert p.read_bytes() == b"RIFFdata"
