"""Unit tests on the claude-code Adapter's decode/encode/native_event,
isolated from any subprocess — the fast, harness-free layer of this test
suite."""

from __future__ import annotations

from typing import Any

import pytest
from hook_bridge_runner.adapters.claude_code import claude_code_adapter
from hook_bridge_runner.codec import RunnerError

_PRE_TOOL_USE = {
    "session_id": "s1",
    "cwd": "/repo",
    "hook_event_name": "PreToolUse",
    "tool_name": "Bash",
    "tool_input": {"command": "git status"},
}


def test_native_event_reads_hook_event_name() -> None:
    assert claude_code_adapter.native_event(_PRE_TOOL_USE) == "PreToolUse"


def test_native_event_requires_hook_event_name() -> None:
    with pytest.raises(RunnerError):
        claude_code_adapter.native_event({})


def test_decode_builds_the_generic_wire_context() -> None:
    codec = claude_code_adapter.codecs["PreToolUse"]
    assert codec.decode(_PRE_TOOL_USE) == {
        "event": "tool.before",
        "session_id": "s1",
        "cwd": "/repo",
        "tool": {"kind": "shell", "command": "git status"},
    }


def test_decode_requires_session_id_and_cwd() -> None:
    codec = claude_code_adapter.codecs["PreToolUse"]
    with pytest.raises(RunnerError):
        codec.decode({**_PRE_TOOL_USE, "session_id": None})


def test_decode_rejects_a_misrouted_event() -> None:
    codec = claude_code_adapter.codecs["PreToolUse"]
    with pytest.raises(RunnerError):
        codec.decode({**_PRE_TOOL_USE, "hook_event_name": "PostToolUse"})


def test_decode_rejects_an_unsupported_tool() -> None:
    codec = claude_code_adapter.codecs["PreToolUse"]
    with pytest.raises(RunnerError):
        codec.decode({**_PRE_TOOL_USE, "tool_name": "WebFetch"})


def test_decode_requires_the_command_field() -> None:
    codec = claude_code_adapter.codecs["PreToolUse"]
    with pytest.raises(RunnerError):
        codec.decode({**_PRE_TOOL_USE, "tool_input": {}})


_V1_OUTCOMES: list[tuple[dict[str, str], tuple[dict[str, Any], int]]] = [
    (
        {"outcome": "allow"},
        (
            {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "allow"}},
            0,
        ),
    ),
    ({"outcome": "defer"}, ({}, 0)),
    (
        {"outcome": "deny", "reason": "no"},
        (
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": "no",
                }
            },
            0,
        ),
    ),
    (
        {"outcome": "ask", "reason": "confirm?"},
        (
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "ask",
                    "permissionDecisionReason": "confirm?",
                }
            },
            0,
        ),
    ),
]


@pytest.mark.parametrize(("outcome", "expected"), _V1_OUTCOMES)
def test_encode_maps_every_v1_outcome(
    outcome: dict[str, str], expected: tuple[dict[str, Any], int]
) -> None:
    codec = claude_code_adapter.codecs["PreToolUse"]
    assert codec.encode(outcome) == expected


def test_encode_rejects_unknown_outcome() -> None:
    codec = claude_code_adapter.codecs["PreToolUse"]
    with pytest.raises(RunnerError):
        codec.encode({"outcome": "modify"})


# --- PostToolUse (tool.after) ---------------------------------------------

_POST_TOOL_USE = {
    "session_id": "s1",
    "cwd": "/repo",
    "hook_event_name": "PostToolUse",
    "tool_name": "Bash",
    "tool_input": {"command": "git status"},
    "tool_response": {"text": "clean", "exitCode": 0},
}


def test_after_native_event_reads_hook_event_name() -> None:
    assert claude_code_adapter.native_event(_POST_TOOL_USE) == "PostToolUse"


def test_after_decode_builds_the_generic_wire_context() -> None:
    codec = claude_code_adapter.codecs["PostToolUse"]
    assert codec.decode(_POST_TOOL_USE) == {
        "event": "tool.after",
        "session_id": "s1",
        "cwd": "/repo",
        "tool": {"kind": "shell", "command": "git status"},
        "result": {"text": "clean", "exit_code": 0},
    }


def test_after_decode_requires_session_id_and_cwd() -> None:
    codec = claude_code_adapter.codecs["PostToolUse"]
    with pytest.raises(RunnerError):
        codec.decode({**_POST_TOOL_USE, "session_id": None})


def test_after_decode_rejects_a_misrouted_event() -> None:
    codec = claude_code_adapter.codecs["PostToolUse"]
    with pytest.raises(RunnerError):
        codec.decode({**_POST_TOOL_USE, "hook_event_name": "PreToolUse"})


def test_after_decode_rejects_an_unsupported_tool() -> None:
    codec = claude_code_adapter.codecs["PostToolUse"]
    with pytest.raises(RunnerError):
        codec.decode({**_POST_TOOL_USE, "tool_name": "WebFetch"})


def test_after_decode_requires_tool_response_text_and_exit_code() -> None:
    codec = claude_code_adapter.codecs["PostToolUse"]
    with pytest.raises(RunnerError):
        codec.decode({**_POST_TOOL_USE, "tool_response": {"text": "clean"}})
    with pytest.raises(RunnerError):
        codec.decode({**_POST_TOOL_USE, "tool_response": {"exitCode": 0}})


_V1_AFTER_OUTCOMES: list[tuple[dict[str, str], tuple[dict[str, Any], int]]] = [
    ({"outcome": "pass"}, ({}, 0)),
    (
        {"outcome": "block", "message": "flaky test"},
        ({"decision": "block", "reason": "flaky test"}, 0),
    ),
    (
        {"outcome": "annotate", "message": "audit note"},
        (
            {
                "hookSpecificOutput": {
                    "hookEventName": "PostToolUse",
                    "additionalContext": "audit note",
                }
            },
            0,
        ),
    ),
]


@pytest.mark.parametrize(("outcome", "expected"), _V1_AFTER_OUTCOMES)
def test_after_encode_maps_every_v1_outcome(
    outcome: dict[str, str], expected: tuple[dict[str, Any], int]
) -> None:
    codec = claude_code_adapter.codecs["PostToolUse"]
    assert codec.encode(outcome) == expected


def test_after_encode_rejects_unknown_outcome() -> None:
    codec = claude_code_adapter.codecs["PostToolUse"]
    with pytest.raises(RunnerError):
        codec.encode({"outcome": "modify"})
