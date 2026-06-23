from secondbrain.agent.tools import (
    ToolCall,
    ToolDefinition,
    ToolExecutionAdapter,
    ToolExecutionPolicy,
    ToolParameter,
    ToolPermission,
    ToolRegistry,
    ToolRisk,
)


def make_echo_tool():
    return ToolDefinition(
        name="echo",
        description="Echo text",
        parameters=(ToolParameter("text", "str"),),
        permissions=(ToolPermission.READ,),
        risk=ToolRisk.LOW,
    )


def test_registry_registers_and_lists_tools():
    registry = ToolRegistry()
    registry.register(make_echo_tool(), lambda args: args["text"])

    assert registry.contains("echo")
    assert [tool.name for tool in registry.list_definitions()] == ["echo"]


def test_adapter_executes_valid_tool_call():
    registry = ToolRegistry()
    registry.register(make_echo_tool(), lambda args: {"echo": args["text"]})
    adapter = ToolExecutionAdapter(registry)

    result = adapter.execute(ToolCall("echo", {"text": "hello"}, correlation_id="c1"))

    assert result.success is True
    assert result.output == {"echo": "hello"}
    assert adapter.audit_log.last().success is True
    assert adapter.audit_log.last().correlation_id == "c1"


def test_adapter_rejects_unknown_parameters():
    registry = ToolRegistry()
    registry.register(make_echo_tool(), lambda args: args)
    adapter = ToolExecutionAdapter(registry)

    result = adapter.execute(ToolCall("echo", {"text": "ok", "extra": True}))

    assert result.success is False
    assert "unknown parameter" in result.error


def test_adapter_rejects_missing_permission():
    dangerous = ToolDefinition(
        name="delete_document",
        description="Delete a document",
        parameters=(ToolParameter("document_id", "str"),),
        permissions=(ToolPermission.DELETE,),
        risk=ToolRisk.HIGH,
    )
    registry = ToolRegistry()
    registry.register(dangerous, lambda args: "deleted")
    adapter = ToolExecutionAdapter(registry, policy=ToolExecutionPolicy(allowed_permissions={ToolPermission.READ}))

    result = adapter.execute(ToolCall("delete_document", {"document_id": "d1"}))

    assert result.success is False
    assert "missing permission" in result.error


def test_adapter_requires_approval_for_medium_risk_tool():
    tool = ToolDefinition(
        name="export_data",
        description="Export data",
        parameters=(ToolParameter("target", "str"),),
        permissions=(ToolPermission.EXPORT,),
        risk=ToolRisk.MEDIUM,
    )
    registry = ToolRegistry()
    registry.register(tool, lambda args: "exported")
    adapter = ToolExecutionAdapter(
        registry,
        policy=ToolExecutionPolicy(allowed_permissions={ToolPermission.READ, ToolPermission.EXPORT}),
    )

    result = adapter.execute(ToolCall("export_data", {"target": "local"}))

    assert result.success is False
    assert "approval required" in result.error


def test_adapter_executes_approved_medium_risk_tool():
    tool = ToolDefinition(
        name="export_data",
        description="Export data",
        parameters=(ToolParameter("target", "str"),),
        permissions=(ToolPermission.EXPORT,),
        risk=ToolRisk.MEDIUM,
    )
    registry = ToolRegistry()
    registry.register(tool, lambda args: "exported")
    adapter = ToolExecutionAdapter(
        registry,
        policy=ToolExecutionPolicy(
            allowed_permissions={ToolPermission.READ, ToolPermission.EXPORT},
            approved_tools={"export_data"},
        ),
    )

    result = adapter.execute(ToolCall("export_data", {"target": "local"}))

    assert result.success is True
    assert result.output == "exported"


def test_sensitive_arguments_are_masked_in_success_audit_log():
    tool = ToolDefinition(
        name="connect",
        description="Connect to remote service",
        parameters=(ToolParameter("api_key", "str", sensitive=True),),
    )
    registry = ToolRegistry()
    registry.register(tool, lambda args: "ok")
    adapter = ToolExecutionAdapter(registry)

    result = adapter.execute(ToolCall("connect", {"api_key": "secret"}))

    assert result.success is True
    assert adapter.audit_log.last().arguments == {"api_key": "***"}


def test_handler_exception_is_converted_to_failed_result():
    registry = ToolRegistry()
    registry.register(make_echo_tool(), lambda args: (_ for _ in ()).throw(RuntimeError("boom")))
    adapter = ToolExecutionAdapter(registry)

    result = adapter.execute(ToolCall("echo", {"text": "hello"}))

    assert result.success is False
    assert "boom" in result.error
