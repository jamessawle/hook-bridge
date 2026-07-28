"""Composition root for the stub Harness Adapter."""

from __future__ import annotations

from typing import Any

from ...codec import HarnessAdapter, RunnerError
from .tool_before import codec as tool_before_codec


def _read_native_event(raw: dict[str, Any]) -> str:
    kind = raw.get("kind")
    if not isinstance(kind, str):
        raise RunnerError("stub native event missing 'kind'")
    return kind


stub_adapter = HarnessAdapter(
    name="stub",
    read_native_event=_read_native_event,
    codecs=[tool_before_codec],
)
