from secondbrain.desktop.status_service import StatusColor, StatusService


def test_status_service_overall_worst_color():
    service = StatusService()
    service.set_status("Database", StatusColor.GREEN)
    service.set_status("RAG", StatusColor.RED, "offline")

    assert service.get_status("RAG").message == "offline"
    assert service.overall() == StatusColor.RED
