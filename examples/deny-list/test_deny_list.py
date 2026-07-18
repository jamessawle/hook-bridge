"""Harness-free tests for the deny-list example.

The whole point of the SDK: import the Hook and drive its pure `dispatch` seam
with SDK-built Context — no harness, no subprocess, no JSON.
"""

from __future__ import annotations

from hook_bridge import shell, tool_before

from deny_list import deny_list


def test_allows_an_ordinary_command() -> None:
    assert deny_list.dispatch(tool_before(shell("ls -la"))).is_allow


def test_denies_a_blocklisted_command() -> None:
    verdict = deny_list.dispatch(tool_before(shell("rm -rf / --no-preserve-root")))
    assert verdict.is_deny
    assert verdict.reason  # deny carries a mandatory reason
