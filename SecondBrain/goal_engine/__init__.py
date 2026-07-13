from __future__ import annotations

from importlib import util
from pathlib import Path

from .engine import GoalEngine


def _load_legacy_module():
	module_path = Path(__file__).resolve().parents[1] / "goal_engine.py"
	spec = util.spec_from_file_location("secondbrain._legacy_goal_engine", module_path)
	if spec is None or spec.loader is None:
		raise ImportError(f"Cannot load legacy goal_engine module from {module_path}")
	module = util.module_from_spec(spec)
	spec.loader.exec_module(module)
	return module


def write_goal_map(project_root: Path, settings: dict) -> Path:
	return _load_legacy_module().write_goal_map(project_root, settings)


__all__ = ["GoalEngine", "write_goal_map"]
