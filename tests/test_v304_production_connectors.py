from secondbrain.connectors.oauth_flow_manager import OAuthClientConfig, OAuthFlowManager
from secondbrain.connectors.gmail_sync_service import GmailSyncService
from secondbrain.connectors.sync_job_runner import SyncJobRunner
from secondbrain.connectors.webhook_receiver import WebhookReceiver


class GmailClient:
    def list_messages(self, cursor=None, limit=100):
        return {"messages": [{"id": "m1", "internalDate": 10}], "historyId": "h1"}


def test_oauth_authorization_url():
    cfg = OAuthClientConfig("cid", "secret", "https://auth", "https://token", "http://localhost/cb", ["email"])
    url = OAuthFlowManager(cfg).authorization_url("state1")
    assert "client_id=cid" in url
    assert "state=state1" in url


def test_gmail_sync_service():
    result = GmailSyncService(GmailClient()).sync()
    assert result.status == "PASS"
    assert result.items == 1
    assert result.cursor == "h1"


def test_sync_job_runner():
    report = SyncJobRunner().run([GmailSyncService(GmailClient())])
    assert report.status == "PASS"
    assert report.results[0].items == 1


def test_github_signature_verification():
    receiver = WebhookReceiver()
    body = b'{"ok":true}'
    import hmac, hashlib
    sig = "sha256=" + hmac.new(b"secret", body, hashlib.sha256).hexdigest()
    assert receiver.verify_github_signature(body, sig, "secret")
