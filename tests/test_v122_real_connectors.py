from secondbrain.launcher_runtime_v122 import SecondBrainLauncherV122


def test_connectors_status(tmp_path):
    l=SecondBrainLauncherV122(tmp_path)
    s=l.connectors_status()
    assert s['version']=='12.2'
    assert len(s['connectors']) >= 8


def test_gmail_sync_emits_events(tmp_path):
    l=SecondBrainLauncherV122(tmp_path)
    r=l.connector_sync('gmail')
    assert r['status']=='ok'
    assert r['pulled'] > 0
    events=l.bus_events('connector.gmail.item', 10)
    assert len(events) == r['emitted']


def test_webhook_inbox_and_event(tmp_path):
    l=SecondBrainLauncherV122(tmp_path)
    event=l.connector_webhook('gmail', {'message_id':'abc'})
    assert event['payload']['connector']=='gmail'
    assert len(l.connector_webhooks()) == 1
    assert len(l.bus_events('connector.gmail.webhook', 5)) == 1


def test_connector_tools_registered(tmp_path):
    l=SecondBrainLauncherV122(tmp_path)
    tools=[t['name'] for t in l.tool_list()]
    assert 'connectors.status' in tools
    out=l.tool_execute('connectors.status', {}, ['connectors.read'])
    assert out['status'] in {'ok','success'}


def test_oauth_templates(tmp_path):
    l=SecondBrainLauncherV122(tmp_path)
    providers={x['provider'] for x in l.connector_oauth_templates()}
    assert {'google','microsoft','github'} <= providers
