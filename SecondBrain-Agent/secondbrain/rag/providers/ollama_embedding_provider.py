"""P1 v18.7 - Ollama Embedding Provider"""

from secondbrain.rag.embedding_provider import EmbeddingProvider

class OllamaEmbeddingProvider(EmbeddingProvider):
    def __init__(self, host: str = "http://localhost:11434", model: str = "nomic-embed-text"):
        self.host = host
        self.model = model

    def embed(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError("Wire to Ollama /api/embeddings")
