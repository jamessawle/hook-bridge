"""Unit tests on the codex Adapter's decode/encode/native_event, isolated
from any subprocess — the fast, harness-free layer of this test suite."""

from __future__ import annotations

from typing import Any

import pytest
from hook_bridge_runner.adapters.codex import codex_adapter
from hook_bridge_runner.codec import RunnerError

_PRE_TOOL_USE = {
    "session_id": "s1",
    "turn_id": "t1",
    "cwd": "/repo",
    "transcript_path": "/tmp/transcript.jsonl",
    "hook_event_name": "PreToolUse",
    "model": "gpt-test",
    "permission_mode": "default",
    "tool_name": "Bash",
    "tool_use_id": "call1",
    "tool_input": {"command": "git status"},
}


def test_native_event_reads_hook_event_name() -> None:
    assert codex_adapter.native_event(_PRE_TOOL_USE) == "PreToolUse"


def test_native_event_requires_hook_event_name() -> None:
    with pytest.raises(RunnerError):
        codex_adapter.native_event({})


def test_decode_builds_the_generic_wire_context() -> None:
    codec = codex_adapter.codecs["PreToolUse"]
    assert codec.decode(_PRE_TOOL_USE) == {
        "event": "tool.before",
        "session_id": "s1",
        "cwd": "/repo",
        "tool": {"kind": "shell", "command": "git status"},
    }


def test_decode_requires_session_id_and_cwd() -> None:
    codec = codex_adapter.codecs["PreToolUse"]
    with pytest.raises(RunnerError):
        codec.decode({**_PRE_TOOL_USE, "cwd": None})


def test_decode_rejects_a_misrouted_event() -> None:
    codec = codex_adapter.codecs["PreToolUse"]
    with pytest.raises(RunnerError):
        codec.decode({**_PRE_TOOL_USE, "hook_event_name": "PostToolUse"})


def test_decode_rejects_an_unsupported_tool() -> None:
    codec = codex_adapter.codecs["PreToolUse"]
    with pytest.raises(RunnerError):
        codec.decode({**_PRE_TOOL_USE, "tool_name": "apply_patch"})


def test_decode_requires_the_command_field() -> None:
    codec = codex_adapter.codecs["PreToolUse"]
    with pytest.raises(RunnerError):
        codec.decode({**_PRE_TOOL_USE, "tool_input": {}})


_VALID_CODEX_ENCODINGS: list[tuple[dict[str, str], tuple[dict[str, Any], int]]] = [
    ({"outcome": "allow"}, ({}, 0)),
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
        ({}, 0),
    ),
]


@pytest.mark.parametrize(("outcome", "expected"), _VALID_CODEX_ENCODINGS)
def test_encode_maps_every_v1_outcome_to_valid_codex_output(
    outcome: dict[str, str], expected: tuple[dict[str, Any], int]
) -> None:
    codec = codex_adapter.codecs["PreToolUse"]
    assert codec.encode(outcome) == expected


def test_encode_rejects_unknown_outcome() -> None:
    codec = codex_adapter.codecs["PreToolUse"]
    with pytest.raises(RunnerError):
        codec.encode({"outcome": "modify"})


def test_post_tool_use_is_not_registered_without_a_faithful_result_mapping() -> None:
    # Codex 0.145.0 sends Bash tool_response as the output string alone. The
    # generic ToolResult also requires exit_code, so an Adapter would have to
    # invent data. Leave the event unsupported and let the CLI fail loudly.
    assert codex_adapter.native_event({"hook_event_name": "PostToolUse"}) == "PostToolUse"
    assert "PostToolUse" not in codex_adapter.codecs
