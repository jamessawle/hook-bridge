"""Selection tests for the composed claude-code Harness Adapter."""

from __future__ import annotations

import pytest
from hook_bridge_runner.adapters.claude_code import claude_code_adapter
from hook_bridge_runner.adapters.claude_code.tool_after import (
    codec as tool_after_codec,
)
from hook_bridge_runner.adapters.claude_code.tool_after_failure import (
    codec as tool_after_failure_codec,
)
from hook_bridge_runner.adapters.claude_code.tool_before import (
    codec as tool_before_codec,
)
from hook_bridge_runner.codec import RunnerError


def test_selects_each_registered_codec_by_native_event() -> None:
    assert (
        claude_code_adapter.codec_for({"hook_event_name": "PreToolUse"})
        is tool_before_codec
    )
    assert (
        claude_code_adapter.codec_for({"hook_event_name": "PostToolUse"})
        is tool_after_codec
    )
    assert (
        claude_code_adapter.codec_for({"hook_event_name": "PostToolUseFailure"})
        is tool_after_failure_codec
    )


def test_requires_a_native_event_name() -> None:
    with pytest.raises(RunnerError, match="missing 'hook_event_name'"):
        claude_code_adapter.codec_for({})


def test_rejects_an_unregistered_native_event() -> None:
    with pytest.raises(RunnerError, match="no codec for event 'Notification'"):
        claude_code_adapter.codec_for({"hook_event_name": "Notification"})
