class StreamingSTTAdapter:
    def transcribe_chunks(self, chunks: list[str]) -> dict:
        text = " ".join(chunk.strip() for chunk in chunks if chunk.strip())
        return {"text": text, "chunks": len(chunks), "engine": "manual_stream_stt"}


class StreamingTTSAdapter:
    def synthesize(self, text: str) -> dict:
        return {
            "text": text,
            "audio_ref": f"tts://local/{abs(hash(text))}",
            "engine": "console_stream_tts",
            "status": "ready",
        }
