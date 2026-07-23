"""The `stub` harness Adapter — not a real harness.

It exists only to prove the CLI & IO plumbing (#11) end-to-end: native JSON
-> generic Context -> Hook subprocess -> generic Verdict -> native JSON. Its
wire shape is deliberately different from the generic Contract's (different
field names, no `event`/`kind` discriminators reused) so a passthrough bug
could never accidentally pass this test. Real claude-code and codex Adapters
are sibling work (#12).
"""

from __future__ import annotations

from typing import Any

from ..codec import Codec, RunnerError


class _StubToolBeforeCodec(Codec):
    def decode(self, raw: dict[str, Any]) -> dict[str, Any]:
        command = raw.get("shell_command")
        if not isinstance(command, str):
            raise RunnerError("stub tool.before payload missing 'shell_command'")
        return {
            "event": "tool.before",
            "session_id": raw.get("session", "stub-session"),
            "cwd": raw.get("directory", "."),
            "tool": {"kind": "shell", "command": command},
        }

    def encode(self, verdict: dict[str, Any]) -> tuple[dict[str, Any], int]:
        outcome = verdict.get("outcome")
        if outcome == "allow":
            return {"decision": "proceed"}, 0
        if outcome == "defer":
            return {"decision": "no-opinion"}, 0
        if outcome in ("deny", "ask"):
            return {"decision": "block" if outcome == "deny" else "confirm", "why": verdict.get("reason", "")}, 0
        raise RunnerError(f"stub codec cannot encode outcome {outcome!r}")


class _StubAdapter:
    codecs: dict[str, Codec] = {"before-tool": _StubToolBeforeCodec()}

    def native_event(self, raw: dict[str, Any]) -> str:
        kind = raw.get("kind")
        if not isinstance(kind, str):
            raise RunnerError("stub native event missing 'kind'")
        return kind


stub_adapter = _StubAdapter()
