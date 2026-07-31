"""Composition root for the codex Harness Adapter."""

from __future__ import annotations

from typing import Any

from ...codec import HarnessAdapter, RunnerError
from .tool_after import codec as tool_after_codec
from .tool_before import codec as tool_before_codec


def _read_native_event(raw: dict[str, Any]) -> str:
    event = raw.get("hook_event_name")
    if not isinstance(event, str):
        raise RunnerError("codex native event missing 'hook_event_name'")
    return event


codex_adapter = HarnessAdapter(
    name="codex",
    read_native_event=_read_native_event,
    codecs=[tool_before_codec, tool_after_codec],
)
