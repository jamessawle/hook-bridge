"""Stub `before-tool` <-> Contract `tool.before` Codec."""

from __future__ import annotations

from typing import Any

from ...codec import Codec, RunnerError


class _StubToolBeforeCodec:
    native_event = "before-tool"
    contract_event = "tool.before"

    def decode(self, raw: dict[str, Any]) -> dict[str, Any]:
        command = raw.get("shell_command")
        if not isinstance(command, str):
            raise RunnerError("stub tool.before payload missing 'shell_command'")
        return {
            "event": self.contract_event,
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
            return {
                "decision": "block" if outcome == "deny" else "confirm",
                "why": verdict.get("reason", ""),
            }, 0
        raise RunnerError(f"stub codec cannot encode outcome {outcome!r}")


codec: Codec = _StubToolBeforeCodec()
