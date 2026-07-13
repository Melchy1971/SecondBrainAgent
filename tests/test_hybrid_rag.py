from secondbrain.hybrid_rag import HybridRAGRuntime


def test_status(tmp_path):
    rt = HybridRAGRuntime(tmp_path)
    assert rt.status()["version"] == "16.7"


def test_index_search(tmp_path):
    rt = HybridRAGRuntime(tmp_path)
    rt.index_text("Demo", "Jarvis nutzt Hybrid RAG mit BM25 und Embeddings.")
    assert rt.hybrid_search("Hybrid RAG")


def test_bm25_vector(tmp_path):
    rt = HybridRAGRuntime(tmp_path)
    rt.index_text("Demo", "SecondBrain verwendet Citation Engine.")
    assert rt.bm25_like("Citation")
    assert rt.vector_search("Citation")


def test_answer_citations(tmp_path):
    rt = HybridRAGRuntime(tmp_path)
    rt.index_text("Demo", "Jarvis kombiniert Reranking und Context Compression.")
    answer = rt.answer_stub("Was kombiniert Jarvis?")
    assert answer["citations"]


def test_seed_runs(tmp_path):
    rt = HybridRAGRuntime(tmp_path)
    rt.seed_demo()
    assert rt.sources()
    assert rt.index_runs()
