"""Interface tests for the claude-code `tool.after` failure Codec."""

from __future__ import annotations

from typing import Any

import pytest
from hook_bridge_runner.adapters.claude_code.tool_after_failure import codec
from hook_bridge_runner.codec import RunnerError

_POST_TOOL_USE_FAILURE = {
    "session_id": "s1",
    "transcript_path": "/tmp/transcript.jsonl",
    "cwd": "/repo",
    "hook_event_name": "PostToolUseFailure",
    "tool_name": "mcp__filesystem__read_file",
    "tool_input": {"path": "/private/data"},
    "tool_use_id": "toolu_1",
    "error": "permission denied",
    "is_interrupt": False,
    "duration_ms": 12,
}


def test_declares_its_native_and_contract_events() -> None:
    assert codec.native_event == "PostToolUseFailure"
    assert codec.contract_event == "tool.after"


def test_decode_preserves_terminal_native_data_and_error() -> None:
    assert codec.decode(_POST_TOOL_USE_FAILURE) == {
        "event": "tool.after",
        "session_id": "s1",
        "cwd": "/repo",
        "tool": {
            "harness": "claude-code",
            "native": _POST_TOOL_USE_FAILURE,
            "projection": None,
        },
        "observation": {"kind": "error", "error": "permission denied"},
    }


def test_decode_projects_failed_bash_from_its_input() -> None:
    raw = {
        **_POST_TOOL_USE_FAILURE,
        "tool_name": "Bash",
        "tool_input": {"command": "pytest"},
    }
    decoded = codec.decode(raw)
    assert decoded["tool"] == {
        "harness": "claude-code",
        "native": raw,
        "projection": {"kind": "shell", "command": "pytest"},
    }


def test_decode_requires_an_authoritative_error_string() -> None:
    with pytest.raises(RunnerError, match="missing 'error'"):
        codec.decode({**_POST_TOOL_USE_FAILURE, "error": None})


def test_decode_rejects_a_misrouted_event() -> None:
    with pytest.raises(RunnerError):
        codec.decode(
            {**_POST_TOOL_USE_FAILURE, "hook_event_name": "PostToolUse"}
        )


_OUTCOMES: list[tuple[dict[str, str], tuple[dict[str, Any], int]]] = [
    ({"outcome": "pass"}, ({}, 0)),
    (
        {"outcome": "block", "message": "fix permissions"},
        ({"decision": "block", "reason": "fix permissions"}, 0),
    ),
    (
        {"outcome": "annotate", "message": "read from the mirror"},
        (
            {
                "hookSpecificOutput": {
                    "hookEventName": "PostToolUseFailure",
                    "additionalContext": "read from the mirror",
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
