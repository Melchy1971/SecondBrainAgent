"""v30.70 ToolChain - domain models.

Composable tool workflows with control flow (conditional / loop / parallel) and
resilience (retry / fallback / rollback). Tools are executed through the existing
``secondbrain.agent.tool_registry.ToolRegistry`` - no second tool executor.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Callable
from uuid import uuid4

# Step type tags (also drive serialization + visualization).
STEP_TOOL = "tool"
STEP_CONDITIONAL = "conditional"
STEP_LOOP = "loop"
STEP_PARALLEL = "parallel"

# Step run status.
OK = "ok"
FAILED = "failed"
SKIPPED = "skipped"
ROLLED_BACK = "rolled_back"


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:8]}"


# -- context ----------------------------------------------------------------
class ChainContext:
    """Variable store shared across steps; supports ``$var`` input resolution."""

    def __init__(self, initial: dict[str, Any] | None = None):
        self.vars: dict[str, Any] = dict(initial or {})

    def get(self, key: str, default: Any = None) -> Any:
        return self.vars.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self.vars[key] = value

    def resolve(self, value: Any) -> Any:
        if isinstance(value, str) and value.startswith("$"):
            return self.vars.get(value[1:])
        if isinstance(value, dict):
            return {k: self.resolve(v) for k, v in value.items()}
        if isinstance(value, list):
            return [self.resolve(v) for v in value]
        return value

    def to_dict(self) -> dict[str, Any]:
        return dict(self.vars)


# -- condition --------------------------------------------------------------
def eval_condition(cond: Any, ctx: ChainContext) -> bool:
    """Evaluate a callable, a {var,op,value} spec, or a truthy value."""
    if cond is None:
        return True
    if callable(cond):
        return bool(cond(ctx))
    if isinstance(cond, dict):
        left = ctx.resolve(cond.get("var")) if str(cond.get("var", "")).startswith("$") \
            else ctx.get(cond.get("var"))
        op = cond.get("op", "==")
        right = cond.get("value")
        return _apply_op(left, op, right)
    return bool(cond)


def _apply_op(left: Any, op: str, right: Any) -> bool:
    try:
        if op == "==":
            return left == right
        if op == "!=":
            return left != right
        if op == ">":
            return left > right
        if op == ">=":
            return left >= right
        if op == "<":
            return left < right
        if op == "<=":
            return left <= right
        if op == "in":
            return left in right
        if op == "truthy":
            return bool(left)
        if op == "falsy":
            return not bool(left)
    except TypeError:
        return False
    return False


# -- policies ---------------------------------------------------------------
@dataclass
class RetryPolicy:
    max_attempts: int = 1   # total attempts (1 = no retry)

    def to_dict(self) -> dict[str, Any]:
        return {"max_attempts": self.max_attempts}


# -- steps ------------------------------------------------------------------
@dataclass
class Step:
    id: str
    name: str
    type: str

    def to_dict(self) -> dict[str, Any]:
        return {"id": self.id, "name": self.name, "type": self.type}


@dataclass
class ToolStep(Step):
    tool: str = ""
    inputs: dict[str, Any] = field(default_factory=dict)
    output_var: str = ""
    retry: RetryPolicy = field(default_factory=RetryPolicy)
    fallback: "Step | None" = None
    rollback_tool: str = ""            # compensating tool run on rollback
    rollback_inputs: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        d = Step.to_dict(self)
        d.update({
            "tool": self.tool, "inputs": self.inputs, "output_var": self.output_var,
            "retry": self.retry.to_dict(),
            "fallback": self.fallback.to_dict() if self.fallback else None,
            "rollback_tool": self.rollback_tool,
        })
        return d

    @classmethod
    def create(cls, tool: str, *, name: str = "", inputs: dict | None = None, output_var: str = "",
               max_attempts: int = 1, fallback: "Step | None" = None,
               rollback_tool: str = "", rollback_inputs: dict | None = None) -> "ToolStep":
        return cls(id=new_id("tool"), name=name or tool, type=STEP_TOOL, tool=tool,
                   inputs=inputs or {}, output_var=output_var,
                   retry=RetryPolicy(max_attempts=max_attempts), fallback=fallback,
                   rollback_tool=rollback_tool, rollback_inputs=rollback_inputs or {})


@dataclass
class ConditionalStep(Step):
    condition: Any = None
    then_steps: list[Step] = field(default_factory=list)
    else_steps: list[Step] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        d = Step.to_dict(self)
        d.update({"then": [s.to_dict() for s in self.then_steps],
                  "else": [s.to_dict() for s in self.else_steps]})
        return d

    @classmethod
    def create(cls, condition: Any, then_steps: list[Step], else_steps: list[Step] | None = None,
               *, name: str = "if") -> "ConditionalStep":
        return cls(id=new_id("if"), name=name, type=STEP_CONDITIONAL, condition=condition,
                   then_steps=list(then_steps), else_steps=list(else_steps or []))


@dataclass
class LoopStep(Step):
    mode: str = "while"                # "while" | "foreach"
    condition: Any = None             # for while
    items_var: str = ""               # for foreach (context var holding a list)
    item_var: str = "item"            # name each item is bound to
    body: list[Step] = field(default_factory=list)
    max_iterations: int = 100

    def to_dict(self) -> dict[str, Any]:
        d = Step.to_dict(self)
        d.update({"mode": self.mode, "items_var": self.items_var,
                  "max_iterations": self.max_iterations, "body": [s.to_dict() for s in self.body]})
        return d

    @classmethod
    def while_(cls, condition: Any, body: list[Step], *, max_iterations: int = 100,
               name: str = "while") -> "LoopStep":
        return cls(id=new_id("loop"), name=name, type=STEP_LOOP, mode="while",
                   condition=condition, body=list(body), max_iterations=max_iterations)

    @classmethod
    def foreach(cls, items_var: str, body: list[Step], *, item_var: str = "item",
                name: str = "foreach") -> "LoopStep":
        return cls(id=new_id("loop"), name=name, type=STEP_LOOP, mode="foreach",
                   items_var=items_var, item_var=item_var, body=list(body))


@dataclass
class ParallelStep(Step):
    branches: list[list[Step]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        d = Step.to_dict(self)
        d.update({"branches": [[s.to_dict() for s in b] for b in self.branches]})
        return d

    @classmethod
    def create(cls, branches: list[list[Step]], *, name: str = "parallel") -> "ParallelStep":
        return cls(id=new_id("par"), name=name, type=STEP_PARALLEL, branches=[list(b) for b in branches])


# -- results ----------------------------------------------------------------
@dataclass
class StepResult:
    step_id: str
    name: str
    type: str
    status: str
    output: Any = None
    error: str = ""
    attempts: int = 0
    used_fallback: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ChainRun:
    chain_id: str
    status: str
    results: list[StepResult] = field(default_factory=list)
    rolled_back: list[str] = field(default_factory=list)
    context: dict[str, Any] = field(default_factory=dict)
    error: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "chain_id": self.chain_id,
            "status": self.status,
            "results": [r.to_dict() for r in self.results],
            "rolled_back": self.rolled_back,
            "context": self.context,
            "error": self.error,
        }
