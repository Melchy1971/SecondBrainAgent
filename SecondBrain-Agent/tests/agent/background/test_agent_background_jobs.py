from secondbrain.agent.background import AgentJobManager, AgentJobResult, AgentRetryPolicy
from secondbrain.agent.background.agent_job import AgentJobStatus


def test_submit_places_job_in_queue():
    manager = AgentJobManager(lambda job: AgentJobResult(success=True))
    job = manager.submit('Run plan', 'plan-1')
    assert job.status == AgentJobStatus.QUEUED
    assert manager.snapshot()['queued'] == 1


def test_run_next_completes_job_and_records_history():
    manager = AgentJobManager(lambda job: AgentJobResult(success=True, output={'ok': True}))
    manager.submit('Run plan', 'plan-1')
    finished = manager.run_next()
    assert finished is not None
    assert finished.status == AgentJobStatus.COMPLETED
    assert finished.result.output == {'ok': True}
    assert manager.snapshot()['completed'] == 1


def test_failed_job_records_error():
    def fail(_job):
        raise RuntimeError('boom')
    manager = AgentJobManager(fail)
    manager.submit('Run plan', 'plan-1')
    finished = manager.run_next()
    assert finished.status == AgentJobStatus.FAILED
    assert finished.error == 'boom'
    assert manager.snapshot()['failed'] == 1


def test_retry_policy_retries_runtime_errors():
    attempts = {'count': 0}
    def flaky(_job):
        attempts['count'] += 1
        if attempts['count'] == 1:
            raise RuntimeError('temporary')
        return AgentJobResult(success=True, output='ok')
    manager = AgentJobManager(flaky, retry_policy=AgentRetryPolicy(max_attempts=2))
    manager.submit('Run plan', 'plan-1', max_attempts=2)
    finished = manager.run_next()
    assert finished.status == AgentJobStatus.COMPLETED
    assert attempts['count'] == 2


def test_cancel_queued_job_moves_to_history():
    manager = AgentJobManager(lambda job: AgentJobResult(success=True))
    job = manager.submit('Run plan', 'plan-1')
    assert manager.cancel_queued(job.job_id, 'user requested') is True
    assert manager.snapshot()['queued'] == 0
    assert manager.snapshot()['cancelled'] == 1


def test_events_are_emitted_for_successful_lifecycle():
    manager = AgentJobManager(lambda job: AgentJobResult(success=True))
    job = manager.submit('Run plan', 'plan-1')
    manager.run_next()
    event_types = [event.event_type.value for event in manager.event_bus.for_job(job.job_id)]
    assert event_types == [
        'agent_job_created',
        'agent_job_queued',
        'agent_job_started',
        'agent_job_completed',
    ]
