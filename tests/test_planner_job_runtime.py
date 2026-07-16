from secondbrain.jobs.integrations import register_planner_handler, submit_planner_job
from secondbrain.jobs.models import JobStatus
from secondbrain.jobs.repository import PostgresJobRepository
from secondbrain.jobs.worker import JobHandlerRegistry, JobWorker
from secondbrain.planner_v2.models import PlanNode
from secondbrain.planner_v2.service import Planner
from secondbrain.storage.db_executor import SqliteExecutor


def test_planner_v2_runs_through_central_runtime(tmp_path):
    repo = PostgresJobRepository(SqliteExecutor(str(tmp_path / "planner.sqlite")))
    repo.ensure_schema()
    submit_planner_job(repo, workspace_id="ws", payload_reference="plan://one", idempotency_key="one")
    planner = Planner(available_tools=["fetch"], max_parallelism=2)
    plan = planner.create_plan(goal="run", workspace_id="ws", nodes=[
        PlanNode("a", "A", tool="fetch", input={"x": 1}),
        PlanNode("b", "B", tool="fetch", input={"x": 2}),
    ])
    handlers = JobHandlerRegistry()
    register_planner_handler(handlers, lambda ref: (planner, plan, {"fetch": lambda data: data}, None))
    result = JobWorker(repo, handlers, worker_id="planner-1", workspace_id="ws").run_once()
    assert result.status == JobStatus.COMPLETED.value
    assert result.checkpoint["completed_nodes"] == ["a", "b"]
