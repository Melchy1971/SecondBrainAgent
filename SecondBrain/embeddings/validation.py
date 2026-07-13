"""Dimension + model validation."""

from __future__ import annotations

from secondbrain.embeddings.base import DimensionMismatchError, ModelNotAllowedError


def validate_dimensions(vectors: list[list[float]], expected: int) -> None:
    for v in vectors:
        if len(v) != expected:
            raise DimensionMismatchError(f"expected={expected}:actual={len(v)}")


def validate_model(model: str, allowed: tuple[str, ...] | list[str]) -> None:
    if allowed and model not in tuple(allowed):
        raise ModelNotAllowedError(f"model {model!r} not in allowed set {tuple(allowed)!r}")
