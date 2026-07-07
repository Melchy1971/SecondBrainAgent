import pytest
from secondbrain.vision.classify import HeuristicTextClassifier
from secondbrain.vision.ports import Label


@pytest.mark.parametrize("text,expected", [
    ("INVOICE\nAmount due: 120\nIBAN DE00 1234", "invoice"),
    ("From: a@b.de\nTo: c@d.de\nSubject: Hallo", "email"),
    ("def run(x):\n    import os\n    return os.getcwd()", "code"),
    ("09:15 Alice: hi\n09:16 Bob: yo\ntyping...", "chat"),
    ("Team meeting 10:30 am\nTermin Kalender", "calendar"),
])
def test_top_class(text, expected):
    assert HeuristicTextClassifier().top(text).name == expected


def test_empty_and_generic():
    c = HeuristicTextClassifier()
    assert c.top("").name == "empty"
    assert c.top("just some neutral words here").name == "generic"


def test_scores_sum_to_one_ish():
    labels = HeuristicTextClassifier().classify_text("INVOICE total IBAN")
    assert all(isinstance(l, Label) for l in labels)
    assert abs(sum(l.score for l in labels) - 1.0) < 1e-6
