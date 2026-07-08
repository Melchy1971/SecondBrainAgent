from __future__ import annotations

from secondbrain.agent import AgentPlanService, PlanStatus


def test_agent_planner_decomposes_goal_with_existing_services(tmp_path):
    service = AgentPlanService(tmp_path)

    plan = service.create("Status prüfen; danach beantworte die Projektfrage", workspace_id="workspace-1")

    assert plan.status == PlanStatus.VALIDATED
    assert len(plan.steps) == 2
    assert plan.steps[0].tool == "command.center"
    assert plan.steps[1].tool == "chat.ask"
    assert all(step.id and step.intent and step.expected_output for step in plan.steps)
    assert plan.workspace_id == "workspace-1"


def test_resume_uses_existing_queue_and_approval_queue(tmp_path):
    service = AgentPlanService(tmp_path)
    plan = service.create("Index aktualisieren")

    resumed = service.resume(plan.id)

    assert resumed.status == PlanStatus.WAITING_APPROVAL
    assert resumed.steps[0].status == PlanStatus.WAITING_APPROVAL
    approval_id = next(item["approval_id"] for item in resumed.steps[0].evidence if item["type"] == "approval")
    job_id = next(item["job_id"] for item in resumed.steps[0].evidence if item["type"] == "queue")
    assert service.approvals.get(approval_id)["status"] == "pending"
    assert service.queue.get_job(job_id).status == "blocked"

    service.approvals.mark(approval_id, "approved")
    queued = service.resume(plan.id)
    assert queued.status == PlanStatus.QUEUED
    assert queued.steps[0].status == PlanStatus.QUEUED
    assert service.queue.get_job(job_id).status == "pending"


def test_cancel_and_resume_plan_without_duplicate_job(tmp_path):
    service = AgentPlanService(tmp_path)
    plan = service.create("Erkläre den Projektstatus")
    queued = service.resume(plan.id)
    job_id = next(item["job_id"] for item in queued.steps[0].evidence if item["type"] == "queue")

    cancelled = service.cancel(plan.id)
    assert cancelled.status == PlanStatus.CANCELLED
    assert service.queue.get_job(job_id).status == "cancelled"

    resumed = service.resume(plan.id)
    new_job_id = next(item["job_id"] for item in reversed(resumed.steps[0].evidence) if item["type"] == "queue")
    assert resumed.status == PlanStatus.QUEUED
    assert new_job_id != job_id


def test_read_only_question_about_deletion_does_not_require_approval(tmp_path):
    plan = AgentPlanService(tmp_path).create("Erkläre, wie delete abgesichert ist")
    assert plan.steps[0].tool == "chat.ask"
    assert plan.steps[0].risk_level == "low"
    assert plan.steps[0].requires_approval is False


def test_resume_synchronizes_successful_queue_job(tmp_path):
    service = AgentPlanService(tmp_path)
    plan = service.resume(service.create("Erkläre den Status").id)
    job_id = next(item["job_id"] for item in plan.steps[0].evidence if item["type"] == "queue")
    service.queue.update_status(job_id, "success")

    completed = service.resume(plan.id)
    assert completed.status == PlanStatus.COMPLETED
    assert completed.steps[0].status == PlanStatus.COMPLETED
