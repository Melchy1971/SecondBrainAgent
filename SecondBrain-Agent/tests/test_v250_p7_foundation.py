from secondbrain.mobile.offline_cache import OfflineCache
from secondbrain.mobile.push_notifications import PushNotificationService


def test_offline_cache():
    cache = OfflineCache()
    cache.put("a", 1)
    assert cache.get("a") == 1


def test_push_notifications():
    service = PushNotificationService()
    service.send("Test", "Hello")
    assert len(service.list()) == 1
