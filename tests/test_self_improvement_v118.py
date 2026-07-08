
from secondbrain.self_improvement_v118 import SelfImprovementEngine


def test_negative_feedback_creates_backlog(tmp_path):
    e=SelfImprovementEngine(tmp_path)
    fb=e.record_feedback('user','command','launcher',-2,'launcher command failed with missing file')
    assert fb['rating'] == -2
    backlog=e.backlog()
    assert len(backlog) == 1
    assert backlog[0]['status'] == 'open'
    assert backlog[0]['score'] > 0


def test_recommendation_orders_by_score(tmp_path):
    e=SelfImprovementEngine(tmp_path)
    e.record_feedback('user','feature','api',-2,'security permission token approval problem')
    e.record_feedback('user','doc','readme',-1,'docs unclear')
    rec=e.recommend_next(2)
    assert len(rec) == 2
    assert rec[0]['score'] >= rec[1]['score']


def test_regression_detection_records_feedback(tmp_path):
    e=SelfImprovementEngine(tmp_path)
    row=e.detect_regressions({'tests_failed':2},{'tests_failed':0})
    assert row['ok'] is False
    assert e.status()['regressions'] == 1
    assert e.status()['feedback_count'] == 1


def test_run_analysis_clusters_failures(tmp_path):
    run_dir=tmp_path/'automation'; run_dir.mkdir(parents=True)
    (run_dir/'runs.jsonl').write_text('{"ok": false, "error": "timeout"}\n{"ok": false, "error": "timeout"}\n', encoding='utf-8')
    e=SelfImprovementEngine(tmp_path)
    result=e.analyze_runs()
    assert result['analyzed_failures'] == 2
    assert result['clusters'] >= 1
    assert len(e.backlog()) >= 1
