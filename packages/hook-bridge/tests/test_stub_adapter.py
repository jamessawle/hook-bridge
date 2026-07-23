"""Unit tests on the stub Adapter's decode/encode/native_event, isolated from
any subprocess — the fast, harness-free layer of this test suite."""

from __future__ import annotations

import pytest
from hook_bridge_runner.adapters.stub import stub_adapter
from hook_bridge_runner.codec import RunnerError


def test_native_event_reads_the_kind_field() -> None:
    assert stub_adapter.native_event({"kind": "before-tool"}) == "before-tool"


def test_native_event_requires_kind() -> None:
    with pytest.raises(RunnerError):
        stub_adapter.native_event({})


def test_decode_builds_the_generic_wire_context() -> None:
    codec = stub_adapter.codecs["before-tool"]
    context = codec.decode(
        {"kind": "before-tool", "session": "s1", "directory": "/repo", "shell_command": "git status"}
    )
    assert context == {
        "event": "tool.before",
        "session_id": "s1",
        "cwd": "/repo",
        "tool": {"kind": "shell", "command": "git status"},
    }


def test_decode_requires_shell_command() -> None:
    codec = stub_adapter.codecs["before-tool"]
    with pytest.raises(RunnerError):
        codec.decode({"kind": "before-tool"})


@pytest.mark.parametrize(
    ("outcome", "expected"),
    [
        ({"outcome": "allow"}, ({"decision": "proceed"}, 0)),
        ({"outcome": "defer"}, ({"decision": "no-opinion"}, 0)),
        ({"outcome": "deny", "reason": "no"}, ({"decision": "block", "why": "no"}, 0)),
        ({"outcome": "ask", "reason": "confirm?"}, ({"decision": "confirm", "why": "confirm?"}, 0)),
    ],
)
def test_encode_maps_every_v1_outcome(
    outcome: dict[str, str], expected: tuple[dict[str, str], int]
) -> None:
    codec = stub_adapter.codecs["before-tool"]
    assert codec.encode(outcome) == expected


def test_encode_rejects_unknown_outcome() -> None:
    codec = stub_adapter.codecs["before-tool"]
    with pytest.raises(RunnerError):
        codec.encode({"outcome": "modify"})
