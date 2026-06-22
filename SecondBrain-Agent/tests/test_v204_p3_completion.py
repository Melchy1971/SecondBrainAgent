from secondbrain.memory.cross_memory_linker import CrossMemoryLinker
from secondbrain.memory.memory_score_fusion import MemoryScoreFusion
from secondbrain.gates.p3_maturity_gate import P3MaturityGate
from secondbrain.gates.p3_completion_report import build_p3_completion_report


def test_cross_memory_links():
    links = CrossMemoryLinker().build_links(["s1"], ["e1"])
    assert links == [("s1", "e1")]


def test_score_fusion():
    assert MemoryScoreFusion().score(1.0, 0.5) > 0


def test_p3_maturity_gate():
    caps = {k: True for k in P3MaturityGate.REQUIRED}
    assert P3MaturityGate().evaluate(caps)["status"] == "PASS"


def test_p3_completion_report():
    report = build_p3_completion_report()
    assert report["status"] == "PASS"
    assert report["next_phase"] == "P2_AGENT_RUNTIME"
