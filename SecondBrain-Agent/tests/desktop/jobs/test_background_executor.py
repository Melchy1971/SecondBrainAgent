from secondbrain.desktop.jobs import BackgroundExecutor


def test_background_executor_runs_callable():
    executor = BackgroundExecutor(max_workers=1)
    try:
        future = executor.submit(lambda: 42)
        assert future.result(timeout=2) == 42
    finally:
        executor.shutdown()
