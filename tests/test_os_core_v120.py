from secondbrain.os_core_v120 import CapabilityRegistry, PersonalOSOrchestrator


def test_capability_registry_defaults(tmp_path):
    registry = CapabilityRegistry(tmp_path / 'runtime')
    rows = registry.ensure()
    assert len(rows) >= 12
    assert registry.get('os')['version'] == '12.0'
    assert registry.summary()['by_status']['available'] >= 12


def test_os_plan_selects_rag_for_knowledge_objective(tmp_path):
    os = PersonalOSOrchestrator(tmp_path / 'runtime')
    plan = os.plan('Fasse mein Wissen zu Jarvis zusammen')
    assert plan['step_count'] >= 1
    assert plan['steps'][0]['capability'] == 'rag'


def test_os_run_dry_run_persists(tmp_path):
    os = PersonalOSOrchestrator(tmp_path / 'runtime')
    run = os.run('Backup und Release prüfen', dry_run=True)
    assert run['status'] == 'PLANNED'
    assert os.runs.list(1)[0]['run_id'] == run['run_id']


def test_os_readiness_gate(tmp_path):
    os = PersonalOSOrchestrator(tmp_path / 'runtime')
    gate = os.readiness_gate()
    assert gate['status'] == 'PASS'
    assert gate['failures'] == 0
