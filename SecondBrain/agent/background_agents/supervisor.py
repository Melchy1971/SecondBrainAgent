"""v30.63 Background Agents - AgentSupervisor.

Registers agents, manages their lifecycle (start/stop/pause/status), runs them,
emits heartbeats and enforces the failure policy. Each run is executed through
the v30.62 Workflow Engine, which in turn mirrors the run into the native Job
Queue and routes notifications through the Notification Center - no parallel
execution or queue is introduced here.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable
from uuid import uuid4

from secondbrain.agent.workflow.executor import WorkflowExecutor
from secondbrain.agent.workflow_models import WorkflowStep

from .handlers import AgentContext, get_handler
from .models import (
    RUN_FAILED,
    RUN_SKIPPED,
    RUN_SUCCESS,
    AgentFailurePolicy,
    AgentHeartbeat,
    AgentRun,
    AgentSchedule,
    AgentState,
    AgentType,
    BackgroundAgent,
    utc_now,
)
from .store import BackgroundAgentStore

DEFAULT_HEARTBEAT_TTL_SECONDS = 15 * 60


class AgentSupervisor:
    def __init__(
        self,
        project_root: str | Path,
        *,
        jobs: Any | None = None,
        notifications: Any | None = None,
        memory_sink: Callable[[dict], None] | None = None,
        handler_overrides: dict[str, Callable[[AgentContext], dict]] | None = None,
        heartbeat_ttl_seconds: int = DEFAULT_HEARTBEAT_TTL_SECONDS,
    ):
        self.project_root = Path(project_root).resolve()
        self.store = BackgroundAgentStore(self.project_root)
        self.jobs = jobs
        self.notifications = notifications
        self.memory_sink = memory_sink
        self.handler_overrides = handler_overrides or {}
        self.heartbeat_ttl_seconds = heartbeat_ttl_seconds

    @classmethod
    def for_project(cls, project_root: str | Path, **overrides: Any) -> "AgentSupervisor":
        root = Path(project_root).resolve()
        from secondbrain.native.job_queue_center.service import JobQueueService
        from secondbrain.native.notification_center.service import NotificationCenterService

        defaults: dict[str, Any] = {
            "jobs": JobQueueService(root=root),
            "notifications": NotificationCenterService(root),
        }
        defaults.update(overrides)
        return cls(root, **defaults)

    # -- registration & lifecycle -----------------------------------------
    def register(
        self,
        name: str,
        agent_type: AgentType | str,
        *,
        agent_id: str | None = None,
        schedule: AgentSchedule | dict | None = None,
        failure_policy: AgentFailurePolicy | dict | None = None,
        config: dict | None = None,
    ) -> BackgroundAgent:
        atype = AgentType.parse(agent_type)
        sched = schedule if isinstance(schedule, AgentSchedule) else AgentSchedule.from_dict(schedule)
        policy = (failure_policy if isinstance(failure_policy, AgentFailurePolicy)
                  else AgentFailurePolicy.from_dict(failure_policy))
        agent = BackgroundAgent(
            id=agent_id or f"agent_{atype.value}_{uuid4().hex[:8]}",
            name=name,
            agent_type=atype,
            schedule=sched,
            failure_policy=policy,
            config=dict(config or {}),
            state=AgentState.REGISTERED,
        )
        self.store.upsert_agent(agent)
        self._heartbeat(agent, "registered")
        return agent

    def start(self, agent_id: str) -> BackgroundAgent:
        return self._set_state(agent_id, AgentState.ACTIVE, "started")

    def stop(self, agent_id: str) -> BackgroundAgent:
        return self._set_state(agent_id, AgentState.STOPPED, "stopped")

    def pause(self, agent_id: str) -> BackgroundAgent:
        return self._set_state(agent_id, AgentState.PAUSED, "paused")

    def resume(self, agent_id: str) -> BackgroundAgent:
        return self._set_state(agent_id, AgentState.ACTIVE, "resumed")

    def _set_state(self, agent_id: str, state: AgentState, event: str) -> BackgroundAgent:
        agent = self._require(agent_id)
        agent.state = state
        agent.updated_at = utc_now()
        if state == AgentState.ACTIVE:
            agent.consecutive_failures = 0
        self.store.upsert_agent(agent)
        self._heartbeat(agent, event)
        return agent

    # -- status ------------------------------------------------------------
    def status(self, agent_id: str) -> dict[str, Any]:
        agent = self._require(agent_id)
        hb = self.store.get_heartbeat(agent_id)
        runs = self.store.runs(agent_id, limit=1)
        stale = hb.is_stale(ttl_seconds=self.heartbeat_ttl_seconds) if hb else True
        return {
            "agent": agent.to_dict(),
            "heartbeat": hb.to_dict() if hb else None,
            "heartbeat_stale": stale,
            "last_run": runs[-1].to_dict() if runs else None,
            "next_due": agent.schedule.next_due(last_run=agent.last_run_at),
        }

    def list(self) -> list[dict[str, Any]]:
        agents = self.store.load_agents()
        beats = self.store.load_heartbeats()
        result = []
        for agent in agents.values():
            hb = beats.get(agent.id)
            result.append({
                "id": agent.id,
                "name": agent.name,
                "agent_type": agent.agent_type.value,
                "state": agent.state.value,
                "last_run_at": agent.last_run_at,
                "last_status": agent.last_status,
                "consecutive_failures": agent.consecutive_failures,
                "heartbeat_stale": hb.is_stale(ttl_seconds=self.heartbeat_ttl_seconds) if hb else True,
            })
        return result

    def runs(self, agent_id: str | None = None, *, limit: int = 50) -> list[dict[str, Any]]:
        return [r.to_dict() for r in self.store.runs(agent_id, limit=limit)]

    # -- heartbeats --------------------------------------------------------
    def heartbeat(self, agent_id: str, state: str = "alive", detail: dict | None = None) -> AgentHeartbeat:
        agent = self._require(agent_id)
        return self._heartbeat(agent, state, detail)

    def _heartbeat(self, agent: BackgroundAgent, state: str, detail: dict | None = None) -> AgentHeartbeat:
        prev = self.store.get_heartbeat(agent.id)
        seq = (prev.sequence + 1) if prev else 1
        hb = AgentHeartbeat(agent_id=agent.id, ts=utc_now(), state=state, sequence=seq, detail=detail or {})
        self.store.save_heartbeat(hb)
        return hb

    # -- execution ---------------------------------------------------------
    def run_agent(self, agent_id: str, *, force: bool = False, now: datetime | None = None) -> AgentRun:
        agent = self._require(agent_id)
        if agent.state != AgentState.ACTIVE and not force:
            run = AgentRun(
                run_id=f"run_{uuid4().hex[:10]}", agent_id=agent.id,
                agent_type=agent.agent_type.value, status=RUN_SKIPPED,
                started_at=utc_now(), ended_at=utc_now(),
                error=f"agent_not_active:{agent.state.value}",
            )
            return self.store.append_run(run)

        self._heartbeat(agent, "running")
        handler = self.handler_overrides.get(agent.agent_type.value) or get_handler(agent.agent_type)
        ctx = AgentContext(
            project_root=self.project_root, agent=agent, jobs=self.jobs,
            notifications=self.notifications, memory_sink=self.memory_sink,
        )

        def tool_runner(step: WorkflowStep, approved: bool):
            return handler(ctx)

        executor = WorkflowExecutor(
            self.project_root, tool_runner=tool_runner, safety=None,
            jobs=self.jobs, notifications=self.notifications, memory_sink=self.memory_sink,
        )
        step = WorkflowStep(
            id="check", name=agent.name,
            tool_name=f"agent.{agent.agent_type.value}",
            input={"agent_id": agent.id},
            max_retries=int(agent.config.get("max_retries", 0)),
        )
        started = (now or datetime.now(timezone.utc)).isoformat(timespec="seconds")
        cp = executor.create(f"background:{agent.name}", [step], workflow_id=f"wf_{agent.id}_{uuid4().hex[:6]}")
        cp = executor.run(cp.workflow_id)

        step_run = cp.runs().get("check")
        succeeded = cp.state.value == "COMPLETED"
        run = AgentRun(
            run_id=f"run_{uuid4().hex[:10]}",
            agent_id=agent.id,
            agent_type=agent.agent_type.value,
            status=RUN_SUCCESS if succeeded else RUN_FAILED,
            started_at=started,
            ended_at=utc_now(),
            output=step_run.output if step_run else None,
            error="" if succeeded else (step_run.error if step_run else cp.error),
            workflow_id=cp.workflow_id,
        )
        self.store.append_run(run)
        self._apply_outcome(agent, run)
        self._heartbeat(agent, "idle" if succeeded else "failed",
                        detail={"run_id": run.run_id, "status": run.status})
        return run

    def run_due(self, *, now: datetime | None = None) -> list[AgentRun]:
        current = now or datetime.now(timezone.utc)
        results: list[AgentRun] = []
        for agent in self.store.load_agents().values():
            if agent.state != AgentState.ACTIVE:
                continue
            if agent.schedule.is_due(last_run=agent.last_run_at, now=current):
                results.append(self.run_agent(agent.id, now=current))
        return results

    # -- failure policy ----------------------------------------------------
    def _apply_outcome(self, agent: BackgroundAgent, run: AgentRun) -> None:
        agent.total_runs += 1
        agent.last_run_at = run.started_at
        agent.last_status = run.status
        if run.status == RUN_SUCCESS:
            agent.consecutive_failures = 0
        else:
            agent.consecutive_failures += 1
            policy = agent.failure_policy
            if policy.tripped(agent.consecutive_failures):
                if policy.action == "stop":
                    agent.state = AgentState.FAILED
                elif policy.action == "pause":
                    agent.state = AgentState.PAUSED
                # "alert_only" leaves the agent ACTIVE
                if policy.notify and self.notifications is not None:
                    try:
                        self.notifications.notify(
                            f"Background-Agent gestoppt: {agent.name}",
                            f"{agent.consecutive_failures} aufeinanderfolgende Fehler "
                            f"(Aktion: {policy.action}). Letzter Fehler: {run.error}",
                            level="error", category="agent", source="background_agent",
                            action_required=True, metadata={"agent_id": agent.id},
                        )
                    except Exception:
                        pass
        agent.updated_at = utc_now()
        self.store.upsert_agent(agent)

    # -- helpers -----------------------------------------------------------
    def _require(self, agent_id: str) -> BackgroundAgent:
        agent = self.store.get_agent(agent_id)
        if agent is None:
            raise KeyError(f"unknown_agent:{agent_id}")
        return agent
