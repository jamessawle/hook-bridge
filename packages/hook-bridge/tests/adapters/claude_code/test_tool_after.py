"""Interface tests for the claude-code `tool.after` Codec."""

from __future__ import annotations

from typing import Any

import pytest
from hook_bridge_runner.adapters.claude_code.tool_after import codec
from hook_bridge_runner.codec import RunnerError

_POST_TOOL_USE = {
    "session_id": "s1",
    "cwd": "/repo",
    "hook_event_name": "PostToolUse",
    "tool_name": "Bash",
    "tool_input": {"command": "git status"},
    "tool_response": {"text": "clean", "exitCode": 0},
}


def test_declares_its_native_and_contract_events() -> None:
    assert codec.native_event == "PostToolUse"
    assert codec.contract_event == "tool.after"


def test_decode_builds_the_generic_wire_context() -> None:
    assert codec.decode(_POST_TOOL_USE) == {
        "event": "tool.after",
        "session_id": "s1",
        "cwd": "/repo",
        "tool": {"kind": "shell", "command": "git status"},
        "result": {"text": "clean", "exit_code": 0},
    }


def test_decode_requires_session_id_and_cwd() -> None:
    with pytest.raises(RunnerError):
        codec.decode({**_POST_TOOL_USE, "session_id": None})


def test_decode_rejects_a_misrouted_event() -> None:
    with pytest.raises(RunnerError):
        codec.decode({**_POST_TOOL_USE, "hook_event_name": "PreToolUse"})


def test_decode_rejects_an_unsupported_tool() -> None:
    with pytest.raises(RunnerError):
        codec.decode({**_POST_TOOL_USE, "tool_name": "WebFetch"})


def test_decode_requires_tool_response_text_and_exit_code() -> None:
    with pytest.raises(RunnerError):
        codec.decode({**_POST_TOOL_USE, "tool_response": {"text": "clean"}})
    with pytest.raises(RunnerError):
        codec.decode({**_POST_TOOL_USE, "tool_response": {"exitCode": 0}})


_OUTCOMES: list[tuple[dict[str, str], tuple[dict[str, Any], int]]] = [
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


@pytest.mark.parametrize(("outcome", "expected"), _OUTCOMES)
def test_encode_maps_every_outcome(
    outcome: dict[str, str], expected: tuple[dict[str, Any], int]
) -> None:
    assert codec.encode(outcome) == expected


def test_encode_rejects_unknown_outcome() -> None:
    with pytest.raises(RunnerError):
        codec.encode({"outcome": "modify"})
