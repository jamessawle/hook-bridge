"""codex `PreToolUse` <-> Contract `tool.before` Codec."""

from __future__ import annotations

from typing import Any

from ...codec import Codec, RunnerError

_NORMALISE: dict[str, str] = {"Bash": "shell"}


class _CodexToolBeforeCodec:
    native_event = "PreToolUse"
    contract_event = "tool.before"

    def decode(self, raw: dict[str, Any]) -> dict[str, Any]:
        event = raw.get("hook_event_name")
        if event != self.native_event:
            raise RunnerError(
                f"codex {self.contract_event} codec received a misrouted event {event!r}"
            )
        session_id = raw.get("session_id")
        cwd = raw.get("cwd")
        if not isinstance(session_id, str) or not isinstance(cwd, str):
            raise RunnerError(
                "codex PreToolUse payload missing 'session_id'/'cwd'"
            )
        return {
            "event": self.contract_event,
            "session_id": session_id,
            "cwd": cwd,
            "tool": self._decode_tool(raw),
        }

    def encode(self, verdict: dict[str, Any]) -> tuple[dict[str, Any], int]:
        outcome = verdict.get("outcome")
        if outcome in ("allow", "ask", "defer"):
            return {}, 0
        if outcome == "deny":
            hook_specific_output = {
                "hookEventName": self.native_event,
                "permissionDecision": "deny",
                "permissionDecisionReason": verdict.get("reason", ""),
            }
            return {"hookSpecificOutput": hook_specific_output}, 0
        raise RunnerError(f"codex codec cannot encode outcome {outcome!r}")

    @staticmethod
    def _decode_tool(raw: dict[str, Any]) -> dict[str, Any]:
        tool_name = raw.get("tool_name")
        kind = _NORMALISE.get(tool_name) if isinstance(tool_name, str) else None
        if kind is None:
            raise RunnerError(
                f"codex tool {tool_name!r} has no generic kind (Unsupported)"
            )
        tool_input = _require_mapping(raw.get("tool_input"))
        command = tool_input.get("command")
        if not isinstance(command, str):
            raise RunnerError("codex Bash tool_input missing 'command'")
        return {"kind": kind, "command": command}


def _require_mapping(raw: object) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise RunnerError("codex Bash tool_input missing 'command'")
    return raw  # pyright: ignore[reportUnknownVariableType]


codec: Codec = _CodexToolBeforeCodec()
