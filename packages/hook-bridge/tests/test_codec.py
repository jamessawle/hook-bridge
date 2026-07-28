"""Composition tests for the Codec and Harness Adapter interfaces."""

from __future__ import annotations

from typing import Any

import pytest
from hook_bridge_runner.codec import Codec, HarnessAdapter, RunnerError


class _Codec:
    native_event = "NativeEvent"
    contract_event = "contract.event"

    def decode(self, raw: dict[str, Any]) -> dict[str, Any]:
        return raw

    def encode(self, verdict: dict[str, Any]) -> tuple[dict[str, Any], int]:
        return verdict, 0


codec: Codec = _Codec()


class _CodecWithoutNativeEvent(_Codec):
    native_event = ""


class _CodecWithoutContractEvent(_Codec):
    contract_event = ""


def _read_event(raw: dict[str, Any]) -> str:
    event = raw.get("event")
    if not isinstance(event, str):
        raise RunnerError("missing event")
    return event


def test_selects_a_registered_codec() -> None:
    adapter = HarnessAdapter(
        name="test",
        read_native_event=_read_event,
        codecs=[codec],
    )
    assert adapter.codec_for({"event": "NativeEvent"}) is codec


def test_rejects_duplicate_native_event_registrations() -> None:
    with pytest.raises(ValueError, match="duplicate Codec registration"):
        HarnessAdapter(
            name="test",
            read_native_event=_read_event,
            codecs=[codec, codec],
        )


@pytest.mark.parametrize(
    ("invalid_codec", "field"),
    [
        (_CodecWithoutNativeEvent(), "native_event"),
        (_CodecWithoutContractEvent(), "contract_event"),
    ],
)
def test_requires_codec_event_metadata(invalid_codec: Codec, field: str) -> None:
    with pytest.raises(ValueError, match=field):
        HarnessAdapter(
            name="test",
            read_native_event=_read_event,
            codecs=[invalid_codec],
        )
