from secondbrain.agent_os import PersonalAGIOS


def test_os_status(tmp_path):
    os = PersonalAGIOS(tmp_path)
    status = os.status()
    assert status["version"] == "13.0"
    assert status["jobs"] >= 1


def test_start_health_stop(tmp_path):
    os = PersonalAGIOS(tmp_path)
    os.start()
    assert os.health()["status"] == "healthy"
    os.stop()
    assert os.health()["status"] == "degraded"


def test_recover_critical_services(tmp_path):
    os = PersonalAGIOS(tmp_path)
    os.stop()
    recovered = os.recover()
    assert "event_bus" in recovered["recovered"]
    assert os.health()["status"] == "healthy"


def test_jobs_run(tmp_path):
    os = PersonalAGIOS(tmp_path)
    runs = os.jobs.run_due()
    assert len(runs) >= 1
    assert os.jobs.runs()


def test_goal_forecast_and_recommendations(tmp_path):
    os = PersonalAGIOS(tmp_path)
    os.goals.add_goal("TTR 1200", 1200, 1147, "points", 10, 1)
    forecast = os.goals.forecast()
    assert forecast[0]["name"] == "TTR 1200"
    recs = os.recommendations.generate()
    assert recs


def test_briefing_creates_notification(tmp_path):
    os = PersonalAGIOS(tmp_path)
    os.start()
    briefing = os.assistant.briefing()
    assert "runtime" in briefing
    assert os.notifications.list()
