from secondbrain.memory.memory_compression import MemoryCompressor
from secondbrain.memory.forgetting_policy import ForgettingPolicy
from secondbrain.gates.p3_memory_gate import P3MemoryGate


def test_memory_compression():
    text = "a" * 1000
    assert len(MemoryCompressor().compress(text, 100)) == 100


def test_forgetting_policy():
    assert ForgettingPolicy().should_archive(0)


def test_memory_gate():
    caps = {c: True for c in P3MemoryGate.REQUIRED}
    assert P3MemoryGate().evaluate(caps)["status"] == "PASS"
