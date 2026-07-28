"""The Codec and Harness Adapter seams.

A `Codec` is a pure `decode`/`encode` pair for one `(harness, native event)`
cell (#8). Each Codec declares both sides of that cell with `native_event` and
`contract_event`, so it can be registered without repeating its identity in a
Harness-sized mapping.

`decode` takes the harness's native payload and returns a dict shaped exactly
like the generic wire Context (what the Hook subprocess reads on stdin).
`encode` takes the generic wire Verdict dict the Hook subprocess printed to
stdout and returns the harness's native response body plus the exit code the
harness expects — the Adapter owns the exit code (#8).
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Any, Protocol


class Codec(Protocol):
    """One pluggable `(Harness, native event)` translation."""

    native_event: str
    contract_event: str

    def decode(self, raw: dict[str, Any]) -> dict[str, Any]: ...
    def encode(self, verdict: dict[str, Any]) -> tuple[dict[str, Any], int]: ...


NativeEventReader = Callable[[dict[str, Any]], str]


class HarnessAdapter:
    """Selects one Harness's explicitly registered Codecs.

    The lookup map is an implementation detail. Callers provide the native
    payload and receive the matching Codec through `codec_for`; they do not
    need to know how the Harness identifies or indexes its native events.
    """

    def __init__(
        self,
        *,
        name: str,
        read_native_event: NativeEventReader,
        codecs: Iterable[Codec],
    ) -> None:
        self.name = name
        self._read_native_event = read_native_event
        self._codecs = self._index_codecs(codecs)

    def codec_for(self, raw: dict[str, Any]) -> Codec:
        native_event = self._read_native_event(raw)
        codec = self._codecs.get(native_event)
        if codec is None:
            raise RunnerError(
                f"harness {self.name!r} has no codec for event {native_event!r}"
            )
        return codec

    @staticmethod
    def _index_codecs(codecs: Iterable[Codec]) -> dict[str, Codec]:
        indexed: dict[str, Codec] = {}
        for codec in codecs:
            if not codec.native_event:
                raise ValueError("a Codec must declare a non-empty native_event")
            if not codec.contract_event:
                raise ValueError("a Codec must declare a non-empty contract_event")
            if codec.native_event in indexed:
                raise ValueError(
                    f"duplicate Codec registration for native event {codec.native_event!r}"
                )
            indexed[codec.native_event] = codec
        return indexed


class RunnerError(Exception):
    """A loud failure at a runner-owned boundary (#8's loud-fail principle):
    an unknown harness, a harness with no Codec for this native event, or a
    Codec rejecting a payload it cannot faithfully translate."""
