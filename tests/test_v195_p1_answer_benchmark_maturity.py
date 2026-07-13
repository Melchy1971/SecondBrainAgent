from secondbrain.rag.query_rewriter import QueryRewriter
from secondbrain.rag.evidence_policy import EvidenceItem, EvidencePolicy
from secondbrain.rag.answer_composer import AnswerComposer
from secondbrain.rag.e2e_benchmark_suite import E2ERagBenchmarkSuite, BenchmarkCase
from secondbrain.rag.rrf import RankedItem
from secondbrain.gates.p1_maturity_gate import P1MaturityGate


class StaticRetriever:
    def search(self, query, limit=10):
        class Result:
            results = [RankedItem("doc1"), RankedItem("doc2")]
        return Result()


def test_query_rewriter_normalizes_and_limits_variants():
    result = QueryRewriter().rewrite("  Meine  E-Mails   finden ")
    assert result.normalized == "Meine E-Mails finden"
    assert len(result.variants) <= 5


def test_evidence_policy_blocks_empty_evidence():
    decision = EvidencePolicy().evaluate([])
    assert decision.status == "NO_EVIDENCE"


def test_answer_composer_requires_citations():
    answer = AnswerComposer().compose("q", [EvidenceItem("s1", "T", "Belegtext", 0.5)])
    assert answer.status == "PASS"
    assert answer.citations == ["s1"]


def test_e2e_benchmark_suite_computes_metrics():
    suite = E2ERagBenchmarkSuite(StaticRetriever())
    result = suite.run([BenchmarkCase("q1", "test", {"doc1"})], k=2)
    assert result.cases == 1
    assert result.averages["recall_at_2"] == 1.0


def test_p1_maturity_gate_passes_all_capabilities():
    caps = {name: True for name in P1MaturityGate.required_capabilities}
    assert P1MaturityGate().evaluate(caps).status == "PASS"
