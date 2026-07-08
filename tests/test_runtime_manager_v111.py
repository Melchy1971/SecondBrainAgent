from pathlib import Path
from secondbrain.launcher_runtime_v111 import SecondBrainLauncherV111
from secondbrain.runtime_manager_v111 import JsonStateStore, ServiceRegistry, ServiceDefinition
from secondbrain.gui_v111 import write_dashboard_snapshot


def test_state_store_roundtrip(tmp_path):
    store = JsonStateStore(tmp_path / 'state')
    store.write('sample', {'a': 1})
    assert store.read('sample')['a'] == 1
    store.append_event('activity', {'type': 'x'})
    assert store.read('activity')[0]['type'] == 'x'


def test_service_registry_dependency_order():
    reg = ServiceRegistry()
    reg.register(ServiceDefinition('eventbus'))
    reg.register(ServiceDefinition('ai', dependencies=['eventbus']))
    reg.register(ServiceDefinition('agent', dependencies=['ai']))
    assert reg.resolve_order(['agent']) == ['eventbus', 'ai', 'agent']


def test_runtime_up_status_metrics_diagnose(tmp_path):
    project = tmp_path / 'SecondBrain-Agent'
    project.mkdir()
    (project / 'config').mkdir()
    (project / 'config' / 'runtime.yaml').write_text('runtime:\n  profile: test\n', encoding='utf-8')
    launcher = SecondBrainLauncherV111(project)
    up = launcher.up()
    assert up['status'] == 'started'
    status = launcher.runtime_status()
    assert 'services' in status
    metrics = launcher.metrics()
    assert metrics['services_total'] >= 1
    diag = launcher.diagnose()
    assert diag['status'] in {'ok', 'error'}


def test_dashboard_snapshot(tmp_path):
    project = tmp_path / 'SecondBrain-Agent'
    project.mkdir()
    (project / 'config').mkdir()
    launcher = SecondBrainLauncherV111(project)
    launcher.up()
    path = write_dashboard_snapshot(launcher.runtime_manager)
    assert path.exists()
    assert 'SecondBrain OS v11.1' in path.read_text(encoding='utf-8')
