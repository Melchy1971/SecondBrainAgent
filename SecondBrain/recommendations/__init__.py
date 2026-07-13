from __future__ import annotations

from importlib import util
from pathlib import Path

from .engine import RecommendationEngine


def _load_legacy_module():
	module_path = Path(__file__).resolve().parents[1] / "recommendations.py"
	spec = util.spec_from_file_location("secondbrain._legacy_recommendations", module_path)
	if spec is None or spec.loader is None:
		raise ImportError(f"Cannot load legacy recommendations module from {module_path}")
	module = util.module_from_spec(spec)
	spec.loader.exec_module(module)
	return module


def write_recommendations(settings: dict) -> Path:
	return _load_legacy_module().write_recommendations(settings)


__all__ = ["RecommendationEngine", "write_recommendations"]
