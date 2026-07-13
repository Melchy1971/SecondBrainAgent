from __future__ import annotations

import pytest

from secondbrain.agent.safety import RISK_LEVELS, RiskClassifier, SafetyPolicy
from secondbrain.agent.safety.policy import ALLOW, BLOCK, REQUIRE_APPROVAL


def test_risk_levels_contract_is_exactly_the_six_brief_levels():
    assert RISK_LEVELS == ("read", "low", "medium", "high", "destructive", "external")


@pytest.mark.parametrize(
    "action,expected",
    [
        ("file.read", "read"),
        ("note.append", "low"),
        ("file.write", "medium"),
        ("file.delete", "destructive"),
        ("email.send", "high"),
        ("calendar.modify", "high"),
        ("db.migrate", "destructive"),
        ("index.repair", "high"),
        ("import.bulk", "high"),
        ("shell.exec", "destructive"),
        ("api.external", "external"),
    ],
)
def test_classifier_maps_brief_actions(action, expected):
    assert RiskClassifier().classify(action) == expected


def test_classifier_keyword_fallback_picks_highest_risk():
    # unknown action containing both "write" (medium) and "delete" (destructive)
    assert RiskClassifier().classify("bulk.delete_and_write") == "destructive"


def test_classifier_unknown_action_defaults_to_low_not_read():
    # safe-by-default: never silently downgrade an unknown write to read
    assert RiskClassifier().classify("totally.unknown.verb") == "low"


def test_classifier_legacy_write_level_hint_maps_to_medium():
    assert RiskClassifier().classify("whatever", hint="write") == "medium"


def test_policy_defaults_auto_allow_read_and_low():
    policy = SafetyPolicy()
    assert policy.evaluate("file.read", "read").outcome == ALLOW
    assert policy.evaluate("note.append", "low").outcome == ALLOW


@pytest.mark.parametrize("level", ["medium", "high", "destructive", "external"])
def test_policy_defaults_require_approval_for_risky_levels(level):
    verdict = SafetyPolicy().evaluate("some.action", level)
    assert verdict.outcome == REQUIRE_APPROVAL
    assert verdict.requires_approval is True


def test_policy_blocked_action_is_hard_blocked():
    policy = SafetyPolicy.from_config({"blocked_actions": ["shell.exec"]})
    verdict = policy.evaluate("shell.exec", "destructive")
    assert verdict.outcome == BLOCK
    assert verdict.blocked is True


def test_policy_blocked_level_config():
    policy = SafetyPolicy.from_config({"blocked_levels": ["external"]})
    assert policy.evaluate("api.external", "external").outcome == BLOCK


def test_policy_allowlist_blocks_everything_else():
    policy = SafetyPolicy.from_config({"allowlist_actions": ["file.read"]})
    assert policy.evaluate("file.read", "read").outcome == ALLOW
    assert policy.evaluate("file.write", "medium").outcome == BLOCK


def test_policy_unlisted_level_defaults_to_approval():
    # a policy that forgot to list "high" must not silently allow it
    policy = SafetyPolicy(auto_allow_levels={"read"}, approval_levels={"medium"})
    assert policy.evaluate("x", "high").outcome == REQUIRE_APPROVAL
