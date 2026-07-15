from secondbrain.personal_dashboard.gui import DashboardViewModel
from secondbrain.personal_dashboard.models import DashboardCard


def test_viewmodel_accepts_empty_card():
    view = DashboardViewModel().build([DashboardCard(card_id="tasks", title="Aufgaben", area="arbeit")])
    assert view["areas"]["arbeit"][0]["title"] == "Aufgaben"
