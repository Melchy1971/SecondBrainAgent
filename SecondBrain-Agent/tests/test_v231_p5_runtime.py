from secondbrain.gui.notification_center import NotificationCenter
from secondbrain.gui.theme_manager import ThemeManager
from secondbrain.gates.p5_production_gate import P5ProductionGate


def test_notifications():
    center = NotificationCenter()
    center.push("Test", "Hello")
    assert len(center.list()) == 1


def test_theme_manager():
    manager = ThemeManager()
    manager.set_theme("dark")
    assert manager.theme == "dark"


def test_p5_gate():
    caps = {k: True for k in P5ProductionGate.REQUIRED}
    assert P5ProductionGate().evaluate(caps)["status"] == "PASS"
