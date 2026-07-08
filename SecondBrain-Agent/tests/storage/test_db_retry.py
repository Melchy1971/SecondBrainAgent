import pytest
from secondbrain.storage.db_retry import run_with_retry, RetryPolicy, is_transient


class OperationalError(Exception):
    pass


def test_transient_retried_then_succeeds():
    calls = {"n": 0}
    def fn():
        calls["n"] += 1
        if calls["n"] < 3:
            raise OperationalError("temporary")
        return "ok"
    result = run_with_retry(fn, RetryPolicy(max_attempts=5, base_delay=0), sleeper=lambda _s: None)
    assert result == "ok" and calls["n"] == 3


def test_non_transient_not_retried():
    calls = {"n": 0}
    def fn():
        calls["n"] += 1
        raise ValueError("permanent")
    with pytest.raises(ValueError):
        run_with_retry(fn, RetryPolicy(max_attempts=5), sleeper=lambda _s: None)
    assert calls["n"] == 1


def test_exhausts_and_raises_last():
    def fn():
        raise OperationalError("always")
    with pytest.raises(OperationalError):
        run_with_retry(fn, RetryPolicy(max_attempts=3, base_delay=0), sleeper=lambda _s: None)


def test_backoff_growth_and_cap():
    p = RetryPolicy(base_delay=1, multiplier=2, max_delay=5)
    assert [p.delay_for(i) for i in range(4)] == [1, 2, 4, 5]


def test_is_transient_by_name():
    assert is_transient(OperationalError("x"))
    assert not is_transient(ValueError("x"))
