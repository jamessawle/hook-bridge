"""Interface tests for the codex `tool.after` Codec."""

from __future__ import annotations

from typing import Any

import pytest
from hook_bridge_runner.adapters.codex.tool_after import codec
from hook_bridge_runner.codec import RunnerError

_POST_TOOL_USE = {
    "session_id": "s1",
    "turn_id": "t1",
    "cwd": "/repo",
    "transcript_path": "/tmp/transcript.jsonl",
    "hook_event_name": "PostToolUse",
    "model": "gpt-test",
    "permission_mode": "default",
    "tool_name": "Bash",
    "tool_use_id": "call1",
    "tool_input": {"command": "git status"},
    "tool_response": "clean",
}


def _tool(raw: dict[str, Any], projection: dict[str, Any] | None) -> dict[str, Any]:
    return {
        "harness": "codex",
        "native": raw,
        "projection": projection,
    }


def test_declares_its_native_and_contract_events() -> None:
    assert codec.native_event == "PostToolUse"
    assert codec.contract_event == "tool.after"


def test_decode_preserves_terminal_native_data_without_inventing_shell_status() -> None:
    assert codec.decode(_POST_TOOL_USE) == {
        "event": "tool.after",
        "session_id": "s1",
        "cwd": "/repo",
        "tool": _tool(
            _POST_TOOL_USE,
            {"kind": "shell", "command": "git status"},
        ),
        "observation": {"kind": "result", "output": "clean"},
    }


@pytest.mark.parametrize(
    ("tool_name", "tool_input", "response"),
    [
        ("apply_patch", {"command": "*** Begin Patch"}, "Done!"),
        ("update_plan", {"plan": []}, [{"type": "input_text", "text": "done"}]),
        ("FutureBuiltIn", {"future": True}, {"isError": True, "message": "opaque"}),
        ("dynamic_tool", "unparsed arguments", None),
    ],
    ids=["apply-patch", "local-function", "unknown", "raw-input"],
)
def test_decode_preserves_normal_results_for_non_mcp_tools(
    tool_name: str, tool_input: object, response: object
) -> None:
    raw = {
        **_POST_TOOL_USE,
        "tool_name": tool_name,
        "tool_input": tool_input,
        "tool_response": response,
    }
    decoded = codec.decode(raw)
    assert decoded["tool"] == _tool(raw, None)
    assert decoded["observation"] == {"kind": "result", "output": response}


def test_decode_classifies_an_authoritative_mcp_error() -> None:
    response = {
        "content": [{"type": "text", "text": "permission denied"}],
        "isError": True,
        "_meta": {"requestId": "r1"},
    }
    raw = {
        **_POST_TOOL_USE,
        "tool_name": "mcp__filesystem__read_file",
        "tool_input": {"path": "/private/data"},
        "tool_response": response,
    }
    decoded = codec.decode(raw)
    assert decoded["tool"] == _tool(raw, None)
    assert decoded["observation"] == {"kind": "error", "error": response}


@pytest.mark.parametrize(
    "response",
    [
        {"content": [], "isError": False},
        {"content": []},
        {"content": [], "isError": "true"},
    ],
    ids=["explicit-normal", "missing-flag", "malformed-flag"],
)
def test_decode_does_not_infer_mcp_errors(response: object) -> None:
    raw = {
        **_POST_TOOL_USE,
        "tool_name": "mcp__filesystem__read_file",
        "tool_input": {"path": "/data"},
        "tool_response": response,
    }
    assert codec.decode(raw)["observation"] == {
        "kind": "result",
        "output": response,
    }


def test_decode_requires_session_id_and_cwd() -> None:
    with pytest.raises(RunnerError):
        codec.decode({**_POST_TOOL_USE, "session_id": None})


def test_decode_rejects_a_misrouted_event() -> None:
    with pytest.raises(RunnerError):
        codec.decode({**_POST_TOOL_USE, "hook_event_name": "PreToolUse"})


@pytest.mark.parametrize("field", ["tool_name", "tool_input", "tool_use_id"])
def test_decode_requires_the_native_tool_envelope(field: str) -> None:
    raw = dict(_POST_TOOL_USE)
    raw.pop(field)
    with pytest.raises(RunnerError):
        codec.decode(raw)


def test_decode_requires_tool_response_but_accepts_json_null() -> None:
    raw = dict(_POST_TOOL_USE)
    raw.pop("tool_response")
    with pytest.raises(RunnerError, match="missing 'tool_response'"):
        codec.decode(raw)

    assert codec.decode({**_POST_TOOL_USE, "tool_response": None})[
        "observation"
    ] == {"kind": "result", "output": None}


def test_decode_rejects_non_json_native_data() -> None:
    with pytest.raises(RunnerError, match="must be JSON"):
        codec.decode({**_POST_TOOL_USE, "tool_response": object()})


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
