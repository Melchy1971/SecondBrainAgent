"""P1 v18.7 - OpenAI Embedding Provider"""

from secondbrain.rag.embedding_provider import EmbeddingProvider

class OpenAIEmbeddingProvider(EmbeddingProvider):
    def __init__(self, model: str = "text-embedding-3-small"):
        self.model = model

    def embed(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError("Wire to OpenAI embeddings API")
