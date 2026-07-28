"""Selection tests for the composed stub Harness Adapter."""

from __future__ import annotations

import pytest
from hook_bridge_runner.adapters.stub import stub_adapter
from hook_bridge_runner.adapters.stub.tool_before import codec as tool_before_codec
from hook_bridge_runner.codec import RunnerError


def test_selects_the_registered_codec_by_native_event() -> None:
    assert stub_adapter.codec_for({"kind": "before-tool"}) is tool_before_codec


def test_requires_a_native_event_name() -> None:
    with pytest.raises(RunnerError, match="missing 'kind'"):
        stub_adapter.codec_for({})


def test_rejects_an_unregistered_native_event() -> None:
    with pytest.raises(RunnerError, match="no codec for event 'prompt-submitted'"):
        stub_adapter.codec_for({"kind": "prompt-submitted"})
