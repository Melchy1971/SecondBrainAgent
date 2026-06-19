from pathlib import Path
import json

from secondbrain.event_bus_v121 import EventBus
from secondbrain.tool_registry_v121 import ToolDefinition, ToolRegistry
from secondbrain.long_running_runtime_v121 import LongRunningRuntime
from secondbrain.launcher_runtime_v121 import SecondBrainLauncherV121


def test_event_bus_publish_replay_and_dlq(tmp_path: Path):
    bus = EventBus(tmp_path)
    seen = []
    bus.subscribe('demo.*', 'ok', lambda e: seen.append(e))
    bus.subscribe('demo.*', 'bad', lambda e: (_ for _ in ()).throw(RuntimeError('boom')))
    row = bus.publish('demo.created', 'test', {'x': 1})
    assert row['topic'] == 'demo.created'
    assert seen[0]['payload']['x'] == 1
    assert bus.replay('demo.*', 10)[0]['event_id'] == row['event_id']
    assert bus.dead_letters(10)[0]['subscriber'] == 'bad'


def test_tool_registry_scope_and_approval(tmp_path: Path):
    reg = ToolRegistry(tmp_path)
    reg.register(ToolDefinition('demo.echo','Echo', {'required':['text']}, {}, ['demo.use'], 3, True), lambda p: {'echo': p['text']})
    try:
        reg.execute('demo.echo', {'text':'x'}, ['demo.use'], approved=False)
        assert False
    except PermissionError:
        pass
    result = reg.execute('demo.echo', {'text':'x'}, ['demo.use'], approved=True)
    assert result['result']['echo'] == 'x'
    assert reg.audit(1)[0]['tool'] == 'demo.echo'


def test_long_runtime_start_tick_tool(tmp_path: Path):
    bus = EventBus(tmp_path)
    reg = ToolRegistry(tmp_path)
    reg.register(ToolDefinition('demo.ok','OK', {}, {}, ['demo'], 1, False), lambda p: {'ok': True})
    rt = LongRunningRuntime(tmp_path, bus, reg)
    started = rt.start()
    assert 'event_bus' in started['started']
    assert rt.tick()['status'] == 'tick'
    result = rt.run_tool('demo.ok', {}, ['demo'])
    assert result['status'] == 'success'
    assert rt.runs(1)[0]['action'] == 'tool.execute'


def test_launcher_v121_core_status(tmp_path: Path):
    launcher = SecondBrainLauncherV121(project_root=tmp_path)
    status = launcher.core121_status()
    assert status['version'] == '12.1'
    assert status['event_bus']['healthy'] is True
    assert launcher.tool_execute('system.status', {}, ['system.read'])['status'] == 'success'
