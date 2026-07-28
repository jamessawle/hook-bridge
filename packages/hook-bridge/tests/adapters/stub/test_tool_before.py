"""Interface tests for the stub `tool.before` Codec."""

from __future__ import annotations

import pytest
from hook_bridge_runner.adapters.stub.tool_before import codec
from hook_bridge_runner.codec import RunnerError


def test_declares_its_native_and_contract_events() -> None:
    assert codec.native_event == "before-tool"
    assert codec.contract_event == "tool.before"


def test_decode_builds_the_generic_wire_context() -> None:
    context = codec.decode(
        {
            "kind": "before-tool",
            "session": "s1",
            "directory": "/repo",
            "shell_command": "git status",
        }
    )
    assert context == {
        "event": "tool.before",
        "session_id": "s1",
        "cwd": "/repo",
        "tool": {"kind": "shell", "command": "git status"},
    }


def test_decode_requires_shell_command() -> None:
    with pytest.raises(RunnerError):
        codec.decode({"kind": "before-tool"})


@pytest.mark.parametrize(
    ("outcome", "expected"),
    [
        ({"outcome": "allow"}, ({"decision": "proceed"}, 0)),
        ({"outcome": "defer"}, ({"decision": "no-opinion"}, 0)),
        (
            {"outcome": "deny", "reason": "no"},
            ({"decision": "block", "why": "no"}, 0),
        ),
        (
            {"outcome": "ask", "reason": "confirm?"},
            ({"decision": "confirm", "why": "confirm?"}, 0),
        ),
    ],
)
def test_encode_maps_every_outcome(
    outcome: dict[str, str], expected: tuple[dict[str, str], int]
) -> None:
    assert codec.encode(outcome) == expected


def test_encode_rejects_unknown_outcome() -> None:
    with pytest.raises(RunnerError):
        codec.encode({"outcome": "modify"})
