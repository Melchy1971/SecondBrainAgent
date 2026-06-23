from secondbrain.agent.release import AgentChecklist, AgentMetrics, AgentRC1Gate, AgentValidation


def _all_capabilities():
    return {
        "agent_foundation": True,
        "memory_context": True,
        "planning_execution": True,
        "tool_calling": True,
        "background_jobs": True,
        "approval_gates": True,
        "privacy_gates": True,
        "audit_trail": True,
    }


def _all_checklist_keys():
    return [key for key, _label in AgentChecklist.DEFAULT_ITEMS]


def test_agent_validation_passes_all_required_capabilities():
    result = AgentValidation().validate(_all_capabilities())
    assert len(result) == 8
    assert all(item.status == "PASS" for item in result)


def test_agent_validation_blocks_missing_capability():
    caps = _all_capabilities()
    caps["privacy_gates"] = False
    assert AgentValidation().status(caps) == "BLOCKED"


def test_agent_checklist_requires_all_required_items():
    checklist = AgentChecklist()
    items = checklist.build(["foundation"])
    assert not checklist.complete(items)


def test_agent_metrics_calculates_rates_and_average():
    snapshot = AgentMetrics().snapshot(
        completed_tasks=8,
        failed_tasks=2,
        tool_calls=10,
        blocked_tool_calls=1,
        execution_durations_ms=[100, 300],
    )
    assert snapshot.completion_rate == 0.8
    assert snapshot.blocked_tool_call_rate == 0.1
    assert snapshot.average_execution_ms == 200


def test_agent_rc1_gate_passes_when_complete():
    result = AgentRC1Gate().run(
        capabilities=_all_capabilities(),
        checklist_passed=_all_checklist_keys(),
        metric_inputs={"completed_tasks": 1, "tool_calls": 2},
    )
    assert result.passed
    assert result.status == "PASS"
    assert result.blockers == []
    assert result.report.status == "PASS"


def test_agent_rc1_gate_blocks_incomplete_checklist():
    result = AgentRC1Gate().run(
        capabilities=_all_capabilities(),
        checklist_passed=["foundation"],
    )
    assert not result.passed
    assert "checklist_incomplete" in result.blockers


def test_agent_health_report_contains_blockers():
    caps = _all_capabilities()
    caps["tool_calling"] = False
    result = AgentRC1Gate().run(capabilities=caps, checklist_passed=_all_checklist_keys())
    assert result.status == "BLOCKED"
    assert "tool_calling" in result.report.blockers
