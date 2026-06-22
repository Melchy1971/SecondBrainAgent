"""P2 v21.3 - Parallel Tool Executor."""

from concurrent.futures import ThreadPoolExecutor


class ParallelExecutor:
    def run(self, callables):
        with ThreadPoolExecutor() as pool:
            return [f.result() for f in [pool.submit(fn) for fn in callables]]
