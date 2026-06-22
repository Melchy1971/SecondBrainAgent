from secondbrain.cli.p1_maturity import run_p1_maturity
from secondbrain.cli.p1_benchmark import run_p1_benchmark
from secondbrain.cli.p1_answer_check import run_answer_check
from secondbrain.gates.p1_completion_report import build_p1_completion_report, write_p1_completion_report


def test_p1_maturity_cli_passes(tmp_path):
    result = run_p1_maturity(str(tmp_path / "maturity.json"))
    assert result["status"] == "PASS"


def test_p1_benchmark_cli_passes(tmp_path):
    result = run_p1_benchmark(str(tmp_path / "benchmark.json"))
    assert result["status"] == "PASS"
    assert result["cases"] == 2


def test_p1_answer_check_requires_citation():
    result = run_answer_check()
    assert result["status"] == "PASS"
    assert result["citations"]


def test_p1_completion_report_marks_next_phase():
    report = build_p1_completion_report()
    assert report.status == "PASS"
    assert report.next_phase == "P3_MEMORY_SYSTEM"


def test_p1_completion_report_writes_file(tmp_path):
    path = write_p1_completion_report(tmp_path / "completion.json")
    assert path.exists()
