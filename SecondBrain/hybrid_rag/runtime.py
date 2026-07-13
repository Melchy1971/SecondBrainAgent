import json
import math
import re
import sqlite3
from pathlib import Path
from datetime import datetime, timezone
from uuid import uuid4
from collections import Counter


def tokenize(text):
    return [t.lower() for t in re.findall(r"[A-Za-zÄÖÜäöüß0-9_+-]{2,}", text or "")]


def cosine(a, b):
    if not a or not b:
        return 0.0
    dot = sum(x*y for x, y in zip(a, b))
    na = math.sqrt(sum(x*x for x in a))
    nb = math.sqrt(sum(y*y for y in b))
    return dot / (na * nb) if na and nb else 0.0


def pseudo_embedding(text, dims=16):
    vec = [0.0] * dims
    for tok in tokenize(text):
        idx = abs(hash(tok)) % dims
        vec[idx] += 1.0
    norm = math.sqrt(sum(v*v for v in vec)) or 1.0
    return [round(v/norm, 6) for v in vec]


class HybridRAGRuntime:
    def __init__(self, root=".", db_path=None):
        self.root = Path(root)
        self.data_dir = self.root / "data" / "hybrid_rag"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = Path(db_path) if db_path else self.data_dir / "hybrid_rag.sqlite3"

    def connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def migrate(self):
        with self.connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sources (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    source_path TEXT,
                    source_type TEXT DEFAULT 'manual',
                    checksum TEXT,
                    indexed_at TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS chunks (
                    id TEXT PRIMARY KEY,
                    source_id TEXT NOT NULL,
                    chunk_index INTEGER NOT NULL,
                    text TEXT NOT NULL,
                    tokens_json TEXT NOT NULL,
                    embedding_json TEXT NOT NULL,
                    citation_label TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS index_runs (
                    id TEXT PRIMARY KEY,
                    mode TEXT NOT NULL,
                    sources INTEGER DEFAULT 0,
                    chunks INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_chunks_source ON chunks(source_id)")
            conn.commit()
        return {"ok": True, "db_path": str(self.db_path)}

    def status(self):
        self.migrate()
        with self.connect() as conn:
            sources = conn.execute("SELECT COUNT(*) c FROM sources").fetchone()["c"]
            chunks = conn.execute("SELECT COUNT(*) c FROM chunks").fetchone()["c"]
            runs = conn.execute("SELECT COUNT(*) c FROM index_runs").fetchone()["c"]
        return {"version": "16.7", "sources": sources, "chunks": chunks, "index_runs": runs, "features": ["bm25_like", "pseudo_embeddings", "hybrid_rank", "rerank", "citations", "compression"]}

    def chunk_text(self, text, size=850, overlap=120):
        text = re.sub(r"\s+", " ", text or "").strip()
        if not text:
            return []
        chunks = []
        start = 0
        while start < len(text):
            end = start + size
            chunks.append(text[start:end].strip())
            if end >= len(text):
                break
            start = max(0, end - overlap)
        return chunks

    def index_text(self, title, text, source_path="manual", source_type="manual", mode="incremental"):
        self.migrate()
        source_id = str(uuid4())
        now = datetime.now(timezone.utc).isoformat()
        chunks = self.chunk_text(text)
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO sources(id, title, source_path, source_type, checksum, indexed_at) VALUES (?, ?, ?, ?, ?, ?)",
                (source_id, title, source_path, source_type, str(abs(hash(text))), now)
            )
            for idx, chunk in enumerate(chunks):
                toks = tokenize(chunk)
                emb = pseudo_embedding(chunk)
                conn.execute(
                    "INSERT INTO chunks(id, source_id, chunk_index, text, tokens_json, embedding_json, citation_label, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (str(uuid4()), source_id, idx, chunk, json.dumps(toks), json.dumps(emb), f"{title}#chunk-{idx}", now)
                )
            conn.execute(
                "INSERT INTO index_runs(id, mode, sources, chunks, created_at) VALUES (?, ?, ?, ?, ?)",
                (str(uuid4()), mode, 1, len(chunks), now)
            )
            conn.commit()
        return {"ok": True, "source_id": source_id, "chunks": len(chunks)}

    def index_file(self, path):
        p = Path(path)
        text = p.read_text(encoding="utf-8", errors="ignore")
        return self.index_text(p.name, text, str(p), "file")

    def _all_chunks(self):
        with self.connect() as conn:
            rows = conn.execute("""
                SELECT c.*, s.title, s.source_path, s.source_type
                FROM chunks c JOIN sources s ON s.id=c.source_id
            """).fetchall()
        return [dict(r) for r in rows]

    def bm25_like(self, query):
        self.migrate()
        q_tokens = tokenize(query)
        chunks = self._all_chunks()
        doc_freq = Counter()
        chunk_tokens = {}
        for c in chunks:
            toks = json.loads(c["tokens_json"])
            chunk_tokens[c["id"]] = toks
            for t in set(toks):
                doc_freq[t] += 1
        n = max(len(chunks), 1)
        results = []
        for c in chunks:
            toks = chunk_tokens[c["id"]]
            tf = Counter(toks)
            score = 0.0
            for qt in q_tokens:
                idf = math.log((n + 1) / (doc_freq.get(qt, 0) + 1)) + 1
                score += tf.get(qt, 0) * idf
            if score > 0:
                results.append({**c, "bm25_score": round(score, 4)})
        return sorted(results, key=lambda r: r["bm25_score"], reverse=True)

    def vector_search(self, query):
        self.migrate()
        q_emb = pseudo_embedding(query)
        results = []
        for c in self._all_chunks():
            emb = json.loads(c["embedding_json"])
            score = cosine(q_emb, emb)
            if score > 0:
                results.append({**c, "vector_score": round(score, 4)})
        return sorted(results, key=lambda r: r["vector_score"], reverse=True)

    def hybrid_search(self, query, limit=5):
        bm = {r["id"]: r for r in self.bm25_like(query)}
        vec = {r["id"]: r for r in self.vector_search(query)}
        ids = set(bm) | set(vec)
        results = []
        for cid in ids:
            base = bm.get(cid) or vec.get(cid)
            bm_score = bm.get(cid, {}).get("bm25_score", 0.0)
            vector_score = vec.get(cid, {}).get("vector_score", 0.0)
            hybrid = 0.55 * bm_score + 0.45 * vector_score
            results.append({**base, "bm25_score": bm_score, "vector_score": vector_score, "hybrid_score": round(hybrid, 4)})
        results = sorted(results, key=lambda r: r["hybrid_score"], reverse=True)
        return self.rerank(query, results)[:limit]

    def rerank(self, query, results):
        q_tokens = set(tokenize(query))
        reranked = []
        for rank, r in enumerate(results):
            toks = set(json.loads(r["tokens_json"]))
            exact_overlap = len(q_tokens & toks)
            rerank_score = r.get("hybrid_score", 0) + exact_overlap * 0.25 - rank * 0.01
            reranked.append({**r, "rerank_score": round(rerank_score, 4)})
        return sorted(reranked, key=lambda r: r["rerank_score"], reverse=True)

    def compress_context(self, results, max_chars=1200):
        selected = []
        used = 0
        for r in results:
            text = r["text"]
            if used + len(text) > max_chars:
                remaining = max_chars - used
                if remaining > 100:
                    selected.append({**r, "text": text[:remaining]})
                break
            selected.append(r)
            used += len(text)
        return {"chunks": selected, "chars": used, "max_chars": max_chars}

    def citations(self, results):
        return [
            {
                "chunk_id": r["id"],
                "source_id": r["source_id"],
                "title": r["title"],
                "source_path": r["source_path"],
                "citation": r["citation_label"],
                "score": r.get("rerank_score", r.get("hybrid_score", 0)),
            }
            for r in results
        ]

    def answer_stub(self, question, limit=5):
        results = self.hybrid_search(question, limit)
        context = self.compress_context(results)
        return {
            "question": question,
            "answer": "RAG-Antwort-Stub. Ein LLM muss die komprimierten Chunks mit Zitaten verwenden.",
            "context": [{"citation": r["citation_label"], "text": r["text"]} for r in context["chunks"]],
            "citations": self.citations(results),
            "matches": len(results),
        }

    def sources(self):
        self.migrate()
        with self.connect() as conn:
            return [dict(r) for r in conn.execute("SELECT * FROM sources ORDER BY indexed_at DESC").fetchall()]

    def index_runs(self):
        self.migrate()
        with self.connect() as conn:
            return [dict(r) for r in conn.execute("SELECT * FROM index_runs ORDER BY created_at DESC").fetchall()]

    def seed_demo(self):
        text = "Jarvis nutzt SecondBrain. Hybrid RAG kombiniert BM25, Embeddings, Reranking, Context Compression und Citation Engine."
        return self.index_text("Hybrid RAG Demo", text, "seed", "demo")
