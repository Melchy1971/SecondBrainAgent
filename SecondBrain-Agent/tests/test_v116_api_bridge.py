
from secondbrain.launcher_runtime_v116 import SecondBrainLauncherV116


def test_api_manifest_has_routes(tmp_path):
    l = SecondBrainLauncherV116(tmp_path)
    m = l.api_manifest()
    assert m['version'] == '11.6'
    assert any(r['path'] == '/status' for r in m['routes'])


def test_api_token_scope_enforced(tmp_path):
    l = SecondBrainLauncherV116(tmp_path)
    tok = l.api_token_create('status-only', 'read:status')['token']
    ok = l.api_dispatch('GET', '/status', token=tok)
    assert ok['http_status'] == 200
    denied = l.api_dispatch('GET', '/metrics', token=tok)
    assert denied['http_status'] == 403


def test_internal_capture_route(tmp_path):
    l = SecondBrainLauncherV116(tmp_path)
    res = l.api_dispatch('POST', '/capture', {'title':'T','text':'Hallo'}, internal=True)
    assert res['http_status'] == 200
    assert res['ok'] is True


def test_risky_remote_requires_approval(tmp_path):
    l = SecondBrainLauncherV116(tmp_path)
    tok = l.api_token_create('agent', 'execute:agent')['token']
    denied = l.api_dispatch('POST', '/agent/run', {'objective':'test'}, token=tok)
    assert denied['http_status'] == 403
