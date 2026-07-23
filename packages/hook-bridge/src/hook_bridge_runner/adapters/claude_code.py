"""The claude-code harness Adapter (#12).

Owns every claude-code-specific detail of `PreToolUse`: the snake_case native
stdin payload, the `Bash -> shell` tool-name normalisation, and the
`hookSpecificOutput.permissionDecision` response shape. See
docs/research/claude-code-hook-api.md for the sourced facts this codes.
"""

from __future__ import annotations

from typing import Any

from ..codec import Codec, RunnerError

_NATIVE_EVENT = "PreToolUse"

# Inbound tool normalisation (#8): only known native tool names map onto a
# generic `kind`. Anything else is Unsupported, loud-fail, never pass-through.
_NORMALISE: dict[str, str] = {"Bash": "shell"}


class _ClaudeCodeToolBeforeCodec(Codec):
    def decode(self, raw: dict[str, Any]) -> dict[str, Any]:
        event = raw.get("hook_event_name")
        if event != _NATIVE_EVENT:
            raise RunnerError(
                f"claude-code tool.before codec received a misrouted event {event!r}"
            )
        session_id = raw.get("session_id")
        cwd = raw.get("cwd")
        if not isinstance(session_id, str) or not isinstance(cwd, str):
            raise RunnerError("claude-code PreToolUse payload missing 'session_id'/'cwd'")
        return {
            "event": "tool.before",
            "session_id": session_id,
            "cwd": cwd,
            "tool": _decode_tool(raw),
        }

    def encode(self, verdict: dict[str, Any]) -> tuple[dict[str, Any], int]:
        outcome = verdict.get("outcome")
        if outcome == "defer":
            # No opinion: emit nothing so claude-code's normal permission
            # flow decides, per #8's `defer` semantics.
            return {}, 0
        if outcome in ("allow", "deny", "ask"):
            hook_specific_output: dict[str, Any] = {
                "hookEventName": _NATIVE_EVENT,
                "permissionDecision": outcome,
            }
            if outcome in ("deny", "ask"):
                hook_specific_output["permissionDecisionReason"] = verdict.get("reason", "")
            return {"hookSpecificOutput": hook_specific_output}, 0
        raise RunnerError(f"claude-code codec cannot encode outcome {outcome!r}")


def _decode_tool(raw: dict[str, Any]) -> dict[str, Any]:
    tool_name = raw.get("tool_name")
    kind = _NORMALISE.get(tool_name) if isinstance(tool_name, str) else None
    if kind is None:
        raise RunnerError(f"claude-code tool {tool_name!r} has no generic kind (Unsupported)")
    tool_input = _require_mapping(raw.get("tool_input"))
    command = tool_input.get("command")
    if not isinstance(command, str):
        raise RunnerError("claude-code Bash tool_input missing 'command'")
    return {"kind": "shell", "command": command}


def _require_mapping(raw: object) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise RunnerError("claude-code Bash tool_input missing 'command'")
    return raw  # pyright: ignore[reportUnknownVariableType]


class _ClaudeCodeAdapter:
    codecs: dict[str, Codec] = {_NATIVE_EVENT: _ClaudeCodeToolBeforeCodec()}

    def native_event(self, raw: dict[str, Any]) -> str:
        event = raw.get("hook_event_name")
        if not isinstance(event, str):
            raise RunnerError("claude-code native event missing 'hook_event_name'")
        return event


claude_code_adapter = _ClaudeCodeAdapter()
