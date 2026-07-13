
from pathlib import Path
from secondbrain.launcher_runtime_v117 import SecondBrainLauncherV117


def test_automation_create_interval(tmp_path):
    l = SecondBrainLauncherV117(tmp_path)
    task = l.automation_every('status', 'api.dispatch', 60, {'method':'GET','path':'/status'}, max_runs=1)
    assert task['task_id'].startswith('auto_')
    assert l.automation_status()['tasks_total'] == 1


def test_automation_once_capture_runs(tmp_path):
    l = SecondBrainLauncherV117(tmp_path)
    task = l.automation_once('capture', 'capture', {'title':'T','text':'Hallo'})
    run = l.automation_run(task['task_id'])
    assert run['ok'] is True
    assert l.automation_tasks()[0]['status'] == 'completed'


def test_automation_disable_enable(tmp_path):
    l = SecondBrainLauncherV117(tmp_path)
    task = l.automation_every('notify', 'notify', 60, {'message':'x'})
    off = l.automation_disable(task['task_id'])
    assert off['enabled'] is False
    on = l.automation_enable(task['task_id'])
    assert on['enabled'] is True


def test_automation_due_runner(tmp_path):
    l = SecondBrainLauncherV117(tmp_path)
    l.automation_once('notify', 'notify', {'message':'due now'})
    result = l.automation_run_due()
    assert result['executed'] == 1
