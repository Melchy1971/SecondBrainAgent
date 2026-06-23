# PATCH P3.1.2 — Agent Memory & Context

## Scope
- Added memory record model with scope, visibility, workspace isolation and duplicate fingerprinting.
- Added in-memory memory store for deterministic local agent tests.
- Added privacy guard with strict block mode and secret redaction.
- Added memory service enforcing privacy before writes.
- Added context builder for workspace-aware prompt context assembly.

## Validation
- New tests: `tests/agent/test_agent_memory_context.py`
- Result: `6 passed`

## Risk
- Persistence is not included yet.
- No vectorized long-term memory retrieval yet.
- Memory writes remain explicit service calls only.
