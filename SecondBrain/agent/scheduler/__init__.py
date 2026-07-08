"""v30.71 Scheduler.

Recurring / cron jobs with dependency-aware scheduling, driving the existing
native Job Queue - no second queue. Ships built-in maintenance jobs (health
check, auto index, knowledge refresh, memory consolidation).

Public surface:
    JobScheduler                 - registration + due detection + run cycle
    RecurringJob, JobRun         - job definition + run record
    CronSchedule, IntervalSchedule, parse_schedule
    maintenance_jobs, MAINTENANCE_HANDLERS
"""

from __future__ import annotations

from .cron import CronSchedule, IntervalSchedule, parse_schedule
from .maintenance import MAINTENANCE_HANDLERS, maintenance_jobs
from .models import JobRun, RecurringJob
from .scheduler import JobScheduler
from .store import SchedulerStore

__all__ = [
    "JobScheduler",
    "RecurringJob",
    "JobRun",
    "CronSchedule",
    "IntervalSchedule",
    "parse_schedule",
    "maintenance_jobs",
    "MAINTENANCE_HANDLERS",
    "SchedulerStore",
]
