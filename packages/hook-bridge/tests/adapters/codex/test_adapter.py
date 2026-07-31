"""Selection tests for the composed codex Harness Adapter."""

from __future__ import annotations

import pytest
from hook_bridge_runner.adapters.codex import codex_adapter
from hook_bridge_runner.adapters.codex.tool_after import codec as tool_after_codec
from hook_bridge_runner.adapters.codex.tool_before import codec as tool_before_codec
from hook_bridge_runner.codec import RunnerError


def test_selects_the_registered_codec_by_native_event() -> None:
    assert (
        codex_adapter.codec_for({"hook_event_name": "PreToolUse"})
        is tool_before_codec
    )
    assert (
        codex_adapter.codec_for({"hook_event_name": "PostToolUse"})
        is tool_after_codec
    )


def test_requires_a_native_event_name() -> None:
    with pytest.raises(RunnerError, match="missing 'hook_event_name'"):
        codex_adapter.codec_for({})


def test_rejects_an_unregistered_native_event() -> None:
    with pytest.raises(RunnerError, match="no codec for event 'Stop'"):
        codex_adapter.codec_for({"hook_event_name": "Stop"})
