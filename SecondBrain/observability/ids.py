"""ID-Erzeugung mit stabilen Präfixen für Korrelation über Systemgrenzen."""

from __future__ import annotations

import uuid

PREFIX_CORRELATION = "cor"
PREFIX_JOB = "job"
PREFIX_PLAN = "plan"
PREFIX_SYNC = "sync"


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:20]}"


def new_correlation_id() -> str:
    return _new_id(PREFIX_CORRELATION)


def new_job_id() -> str:
    return _new_id(PREFIX_JOB)


def new_plan_id() -> str:
    return _new_id(PREFIX_PLAN)


def new_sync_id() -> str:
    return _new_id(PREFIX_SYNC)
