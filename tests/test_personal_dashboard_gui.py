from secondbrain.personal_dashboard.gui import DashboardViewModel, render_dashboard_html
from secondbrain.personal_dashboard.models import CardItem, DashboardCard


def test_gui_redacts_technical_reference_from_visible_html():
    card = DashboardCard(card_id="tasks", title="Aufgaben", area="arbeit",
                         items=[CardItem(label="Konzept", reference="task-secret-id")])
    html = render_dashboard_html(DashboardViewModel().build([card]))
    assert "Konzept" in html and "task-secret-id" not in html
