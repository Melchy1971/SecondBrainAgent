from secondbrain.agent import AgentCore, AgentRequest, IntentRoute, IntentRouter, ToolDefinition, ToolRegistry
from secondbrain.agent.task_planner import TaskStepState


def test_tool_registry_executes_registered_tool():
    registry = ToolRegistry()
    registry.register(ToolDefinition(name="echo", description="Echo", handler=lambda payload: payload["value"]))

    assert registry.execute("echo", {"value": "ok"}) == "ok"


def test_tool_registry_blocks_confirmation_required_tool():
    registry = ToolRegistry()
    registry.register(ToolDefinition(name="delete", description="Delete", handler=lambda payload: True, requires_confirmation=True))

    try:
        registry.execute("delete", {})
    except ValueError as exc:
        assert "tool_requires_confirmation:delete" in str(exc)
    else:
        raise AssertionError("confirmation gate not enforced")


def test_intent_router_uses_keyword_rule():
    router = IntentRouter()
    router.add_keyword_rule("sync", IntentRoute(intent="connector_sync", tool_name="sync_connectors", confidence=0.9))

    route = router.route("please sync connectors")

    assert route.intent == "connector_sync"
    assert route.tool_name == "sync_connectors"


def test_agent_core_executes_routed_tool():
    router = IntentRouter()
    router.add_keyword_rule("diagnose", IntentRoute(intent="diagnostics", tool_name="diagnostics"))
    registry = ToolRegistry()
    registry.register(ToolDefinition(name="diagnostics", description="Run diagnostics", handler=lambda payload: {"status": "green"}))
    agent = AgentCore(router=router, registry=registry)

    response = agent.handle(AgentRequest(text="diagnose system"))

    assert response.ok is True
    assert response.intent == "diagnostics"
    assert response.results == [{"status": "green"}]
    assert response.plan.steps[0].state == TaskStepState.COMPLETED


def test_agent_core_isolates_tool_failure():
    router = IntentRouter()
    router.add_keyword_rule("fail", IntentRoute(intent="broken", tool_name="broken"))
    registry = ToolRegistry()
    registry.register(ToolDefinition(name="broken", description="Broken", handler=lambda payload: (_ for _ in ()).throw(RuntimeError("boom"))))
    agent = AgentCore(router=router, registry=registry)

    response = agent.handle(AgentRequest(text="fail now"))

    assert response.ok is False
    assert response.message == "failed"
    assert "boom" in response.errors[0]
    assert response.plan.steps[0].state == TaskStepState.FAILED


def test_agent_core_fallback_chat_plan():
    agent = AgentCore()

    response = agent.handle(AgentRequest(text="hello"))

    assert response.ok is True
    assert response.intent == "chat"
    assert response.results[0]["type"] == "chat"
