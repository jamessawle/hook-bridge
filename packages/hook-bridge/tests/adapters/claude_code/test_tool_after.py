"""Interface tests for the claude-code `tool.after` normal-result Codec."""

from __future__ import annotations

from typing import Any

import pytest
from hook_bridge_runner.adapters.claude_code.tool_after import codec
from hook_bridge_runner.codec import RunnerError

_POST_TOOL_USE = {
    "session_id": "s1",
    "transcript_path": "/tmp/transcript.jsonl",
    "cwd": "/repo",
    "hook_event_name": "PostToolUse",
    "tool_name": "Bash",
    "tool_input": {"command": "git status"},
    "tool_response": {"output": "clean", "exitCode": 0},
    "tool_use_id": "toolu_1",
    "duration_ms": 12,
}


def test_declares_its_native_and_contract_events() -> None:
    assert codec.native_event == "PostToolUse"
    assert codec.contract_event == "tool.after"


def test_decode_preserves_terminal_native_data_and_normal_result() -> None:
    assert codec.decode(_POST_TOOL_USE) == {
        "event": "tool.after",
        "session_id": "s1",
        "cwd": "/repo",
        "tool": {
            "harness": "claude-code",
            "native": _POST_TOOL_USE,
            "projection": {"kind": "shell", "command": "git status"},
        },
        "observation": {
            "kind": "result",
            "output": {"output": "clean", "exitCode": 0},
        },
    }


@pytest.mark.parametrize(
    "response",
    [None, "text", ["heterogeneous", {"future": True}], {"structured": 1}],
    ids=["null", "string", "array", "object"],
)
def test_decode_accepts_every_json_result_shape(response: object) -> None:
    raw = {
        **_POST_TOOL_USE,
        "tool_name": "FutureBuiltIn",
        "tool_input": {"future": True},
        "tool_response": response,
    }
    decoded = codec.decode(raw)
    assert decoded["tool"] == {
        "harness": "claude-code",
        "native": raw,
        "projection": None,
    }
    assert decoded["observation"] == {"kind": "result", "output": response}


def test_decode_requires_session_id_and_cwd() -> None:
    with pytest.raises(RunnerError):
        codec.decode({**_POST_TOOL_USE, "session_id": None})


def test_decode_rejects_a_misrouted_event() -> None:
    with pytest.raises(RunnerError):
        codec.decode({**_POST_TOOL_USE, "hook_event_name": "PreToolUse"})


def test_decode_requires_tool_response_but_accepts_json_null() -> None:
    raw = dict(_POST_TOOL_USE)
    raw.pop("tool_response")
    with pytest.raises(RunnerError, match="missing 'tool_response'"):
        codec.decode(raw)

    assert codec.decode({**_POST_TOOL_USE, "tool_response": None})[
        "observation"
    ] == {"kind": "result", "output": None}


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
