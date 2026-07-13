import pytest

from secondbrain.desktop.dashboard.actions import (
    DashboardAction,
    DashboardActionRegistry,
    DashboardActionService,
    DashboardActionStatus,
    DashboardActionType,
)


def test_action_validation_requires_id_and_label():
    action = DashboardAction(action_id="", label="")
    assert action.validate() == ["action_id_required", "label_required"]


def test_refresh_action_requires_widget_id():
    action = DashboardAction("refresh", "Refresh", DashboardActionType.REFRESH_WIDGET)
    assert "widget_id_required_for_refresh" in action.validate()


def test_registry_lists_widget_actions_sorted():
    registry = DashboardActionRegistry()
    registry.register(DashboardAction("open:jobs", "Open", widget_id="jobs"))
    registry.register(DashboardAction("refresh:jobs", "Refresh", widget_id="jobs"))
    registry.register(DashboardAction("open:rag", "Open", widget_id="rag"))

    assert [action.action_id for action in registry.list_actions("jobs")] == ["open:jobs", "refresh:jobs"]


def test_executor_returns_not_found_for_unknown_action():
    service = DashboardActionService()

    result = service.execute("missing")

    assert result.status == DashboardActionStatus.NOT_FOUND
    assert not result.ok


def test_executor_respects_disabled_action():
    service = DashboardActionService()
    service.registry.register(DashboardAction("x", "Disabled", enabled=False))

    result = service.execute("x")

    assert result.status == DashboardActionStatus.DISABLED


def test_executor_runs_handler_and_wraps_mapping_payload():
    service = DashboardActionService()
    service.registry.register(
        DashboardAction("sync", "Sync", payload={"ignored": True}),
        handler=lambda action: {"ran": action.action_id},
    )

    result = service.execute("sync")

    assert result.ok
    assert result.payload == {"ran": "sync"}


def test_executor_converts_handler_exception_to_failed_result():
    def fail(_action):
        raise RuntimeError("boom")

    service = DashboardActionService()
    service.registry.register(DashboardAction("bad", "Bad"), handler=fail)

    result = service.execute("bad")

    assert result.status == DashboardActionStatus.FAILED
    assert result.message == "boom"


def test_default_widget_actions_create_refresh_and_open_actions():
    service = DashboardActionService()

    service.register_default_widget_actions(["jobs", "rag"])

    assert service.registry.get("refresh:jobs").action_type == DashboardActionType.REFRESH_WIDGET
    assert service.registry.get("open:rag").payload == {"view": "rag"}
