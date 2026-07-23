"""Harness-free tests for the command-policy example.

One assertion per outcome — the whole four-verb Verdict surface, exercised in
process through the real Contract types with no harness present.
"""

from __future__ import annotations

from command_policy import command_policy
from hook_bridge import ToolBeforeVerdict, shell, tool_before


def decide(command: str) -> ToolBeforeVerdict:
    return command_policy.dispatch(tool_before(shell(command)))


def test_denies_a_blocked_command() -> None:
    verdict = decide("rm -rf / now")
    assert verdict.is_deny
    assert verdict.reason


def test_asks_before_a_review_command() -> None:
    verdict = decide("git push --force origin main")
    assert verdict.is_ask
    assert verdict.reason


def test_allows_a_vouched_command() -> None:
    assert decide("git status --short").is_allow


def test_defers_an_unrecognised_command() -> None:
    assert decide("make build").is_defer


def test_defers_an_empty_command() -> None:
    assert decide("   ").is_defer
