from secondbrain.personal_agi import PersistentPersonalAGI


def test_status(tmp_path):
    agi = PersistentPersonalAGI(tmp_path)
    assert agi.status()["version"] == "14.0"


def test_daemon_lifecycle(tmp_path):
    agi = PersistentPersonalAGI(tmp_path)
    agi.daemon.start()
    assert agi.daemon.tick()["ok"] is True
    agi.daemon.stop()
    assert agi.daemon.tick()["ok"] is False


def test_cycle(tmp_path):
    agi = PersistentPersonalAGI(tmp_path)
    cycle = agi.cycle.run("Prüfe Tageslage")
    assert cycle["verification"]["status"] == "success"


def test_policy_blocks(tmp_path):
    agi = PersistentPersonalAGI(tmp_path)
    assert agi.policy.evaluate("send_email", "high")["allowed"] is False


def test_briefing(tmp_path):
    agi = PersistentPersonalAGI(tmp_path)
    assert "message" in agi.assistant.briefing()


def test_optimizer(tmp_path):
    agi = PersistentPersonalAGI(tmp_path)
    assert agi.optimizer.backlog()
