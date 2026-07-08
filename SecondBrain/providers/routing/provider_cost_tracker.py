"""v30.0 provider cost tracking."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Pricing:
    input_per_1m: float = 0.0
    output_per_1m: float = 0.0


class ProviderCostTracker:
    def __init__(self, pricing: dict[str, Pricing] | None = None) -> None:
        self.pricing = pricing or {}

    def estimate(self, model: str, input_tokens: int = 0, output_tokens: int = 0) -> float:
        price = self.pricing.get(model, Pricing())
        return round((input_tokens / 1_000_000 * price.input_per_1m) + (output_tokens / 1_000_000 * price.output_per_1m), 6)
