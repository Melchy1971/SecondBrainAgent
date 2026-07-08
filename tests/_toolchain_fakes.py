"""Shared fakes for v30.70 toolchain tests."""

from __future__ import annotations

from typing import Any


class RecordingRunner:
    """tool_runner(name, inputs) -> output; controllable per-tool behaviour."""

    def __init__(self, fail: dict[str, int] | None = None, always_fail: set[str] | None = None,
                 outputs: dict[str, Any] | None = None):
        # fail: tool -> number of leading attempts that raise before succeeding
        self.fail = dict(fail or {})
        self.always_fail = set(always_fail or set())
        self.outputs = dict(outputs or {})
        self.calls: list[tuple[str, dict]] = []

    def __call__(self, name: str, inputs: dict) -> Any:
        self.calls.append((name, dict(inputs)))
        if name in self.always_fail:
            raise RuntimeError(f"{name}_always_fails")
        if self.fail.get(name, 0) > 0:
            self.fail[name] -= 1
            raise RuntimeError(f"{name}_transient")
        return self.outputs.get(name, {"tool": name, "inputs": inputs})

    def count(self, name: str) -> int:
        return len([c for c in self.calls if c[0] == name])


class FakeToolResult:
    def __init__(self, success: bool, output: Any = None, error: str = ""):
        self.success = success
        self.output = output
        self.error = error


class FakeRegistry:
    """Minimal ToolRegistry stand-in exposing .run(name, inputs, approved=)."""

    def __init__(self, runner: RecordingRunner):
        self.runner = runner

    def run(self, name: str, inputs: dict, approved: bool = True) -> FakeToolResult:
        try:
            return FakeToolResult(True, self.runner(name, inputs))
        except Exception as exc:  # noqa: BLE001
            return FakeToolResult(False, error=str(exc))
