from threading import Event, Thread
from time import sleep

from secondbrain.personal_dashboard.models import CardStatus, DashboardConfig
from secondbrain.personal_dashboard.runtime import DashboardRuntime


def _config():
    return DashboardConfig(enabled=["tasks", "important_mail"],
                           order=["tasks", "important_mail"], workspace_id="ws")


def test_parallel_reads_timeout_and_pagination_are_isolated():
    seen = {}

    def tasks(**kwargs):
        seen.update(kwargs)
        return [{"id": "t", "title": "Schnell", "workspace_id": "ws"}]

    def mail(**kwargs):
        sleep(0.1)
        return [{"id": "m", "subject": "Langsam", "important": True}]

    snapshot, performance = DashboardRuntime(source_timeout_seconds=0.02).load(
        request_id="r", config=_config(), providers={"tasks": tasks, "mail": mail},
        page=2, page_size=10)
    cards = {card.card_id: card for card in snapshot.cards}
    assert cards["tasks"].items[0].label == "Schnell"
    assert cards["important_mail"].status == CardStatus.ERROR.value
    assert performance.timed_out == ["mail"]
    assert seen["offset"] == 10 and seen["limit"] == 10


def test_request_cancellation_is_visible_to_provider():
    entered = Event()
    cancelled = Event()
    runtime = DashboardRuntime(source_timeout_seconds=1)

    def provider(**kwargs):
        entered.set()
        while not kwargs["cancel_event"].is_set():
            sleep(0.005)
        cancelled.set()
        return []

    thread = Thread(target=lambda: runtime.load(
        request_id="cancel-me", config=_config(), providers={"tasks": provider}))
    thread.start()
    assert entered.wait(0.5)
    assert runtime.cancel("cancel-me") is True
    thread.join(1)
    assert cancelled.is_set() and not thread.is_alive()


def test_incremental_card_refresh():
    runtime = DashboardRuntime()
    card = runtime.refresh_card(
        card_id="tasks", config=_config(), source_key="tasks",
        provider=lambda **kwargs: [{"id": "t", "title": "Aktualisiert", "workspace_id": "ws"}],
    )
    assert card.items[0].label == "Aktualisiert"
