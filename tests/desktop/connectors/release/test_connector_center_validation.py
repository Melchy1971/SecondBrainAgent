from secondbrain.desktop.connectors.release import ConnectorCenterChecklist, ConnectorCenterMetrics
from secondbrain.desktop.connectors.release.connector_center_validation import ConnectorCenterValidation


def test_validation_detects_unavailable_connectors_as_failure():
    checklist = ConnectorCenterChecklist().build(ConnectorCenterChecklist.REQUIRED_KEYS)
    issues = ConnectorCenterValidation().validate(checklist, ConnectorCenterMetrics(total_connectors=2, enabled_connectors=2, healthy_connectors=1, unavailable_connectors=1))
    assert ConnectorCenterValidation().status_from_issues(issues) == "FAIL"
    assert any(issue.code == "connectors_unavailable" for issue in issues)


def test_validation_warns_when_no_connector_enabled():
    checklist = ConnectorCenterChecklist().build(ConnectorCenterChecklist.REQUIRED_KEYS)
    issues = ConnectorCenterValidation().validate(checklist, ConnectorCenterMetrics(total_connectors=2, enabled_connectors=0, disabled_connectors=2, healthy_connectors=2))
    assert ConnectorCenterValidation().status_from_issues(issues) == "WARNING"
    assert any(issue.code == "no_enabled_connectors" for issue in issues)
