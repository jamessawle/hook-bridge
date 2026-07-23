"""The Codec seam: harness-native JSON <-> generic wire JSON.

A `Codec` is a pure `decode`/`encode` pair for one `(harness, native event)`
cell (#8). The runner has no dependency on the SDK (#7) — it never imports
`hook_bridge`'s typed `Context`/`Verdict`, only the plain dicts that match the
generic wire JSON shape the SDK's own `decode_context`/`encode_verdict`
validate on the Hook's side of the pipe.

`decode` takes the harness's native payload and returns a dict shaped exactly
like the generic wire Context (what the Hook subprocess reads on stdin).
`encode` takes the generic wire Verdict dict the Hook subprocess printed to
stdout and returns the harness's native response body plus the exit code the
harness expects — the Adapter owns the exit code (#8).
"""

from __future__ import annotations

from typing import Any, Protocol


class Codec(Protocol):
    def decode(self, raw: dict[str, Any]) -> dict[str, Any]: ...
    def encode(self, verdict: dict[str, Any]) -> tuple[dict[str, Any], int]: ...


class HarnessAdapter(Protocol):
    """Everything the runner needs for one harness.

    `native_event` is the wiring-time peek (#8, #11): it reads only the
    native event name out of an arbitrary raw payload, before any Codec has
    run, so `codecs` can be looked up without having decoded (or even fully
    validated) the payload yet. `codecs` is keyed by that native event name.
    """

    codecs: dict[str, Codec]

    def native_event(self, raw: dict[str, Any]) -> str: ...


class RunnerError(Exception):
    """A loud failure at a runner-owned boundary (#8's loud-fail principle):
    an unknown harness, a harness with no Codec for this native event, or a
    Codec rejecting a payload it cannot faithfully translate."""
