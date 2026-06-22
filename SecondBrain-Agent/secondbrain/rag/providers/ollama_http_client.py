"""P1 v18.8 - Ollama HTTP Client Scaffold"""

class OllamaHttpClient:
    def embed(self, texts: list[str], model: str = "nomic-embed-text"):
        raise NotImplementedError("Call Ollama /api/embed endpoint")
