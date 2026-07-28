"""The codex harness Adapter (#12).

Codex's `PreToolUse` input maps cleanly to the generic `tool.before` Context,
but its output semantics overlap only partly. `deny` maps to
`permissionDecision: "deny"` and `defer` to empty output. Codex rejects
`permissionDecision: "allow"` unless it accompanies an input rewrite, and
still runs the normal permission flow afterward, so this Codec conservatively
maps `allow` to empty output too: the command can proceed, but is not
auto-approved. Codex also rejects `ask`, so the Codec maps that to empty
output as well. This keeps the Codec total, but cannot guarantee a prompt:
Codex applies its normal permission policy instead (tracked in #18).

Codex requires `hookSpecificOutput.hookEventName` on the supported deny
response. See https://developers.openai.com/codex/hooks for the native
protocol this codes.
"""

from __future__ import annotations

from typing import Any

from ..codec import Codec, RunnerError

_NATIVE_EVENT = "PreToolUse"

# Inbound tool normalisation (#8): only known native tool names map onto a
# generic `kind`. Anything else is Unsupported, loud-fail, never pass-through.
_NORMALISE: dict[str, str] = {"Bash": "shell"}


class _CodexToolBeforeCodec(Codec):
    def decode(self, raw: dict[str, Any]) -> dict[str, Any]:
        event = raw.get("hook_event_name")
        if event != _NATIVE_EVENT:
            raise RunnerError(f"codex tool.before codec received a misrouted event {event!r}")
        session_id = raw.get("session_id")
        cwd = raw.get("cwd")
        if not isinstance(session_id, str) or not isinstance(cwd, str):
            raise RunnerError("codex PreToolUse payload missing 'session_id'/'cwd'")
        return {
            "event": "tool.before",
            "session_id": session_id,
            "cwd": cwd,
            "tool": _decode_tool(raw),
        }

    def encode(self, verdict: dict[str, Any]) -> tuple[dict[str, Any], int]:
        outcome = verdict.get("outcome")
        if outcome in ("allow", "ask", "defer"):
            # Codex cannot auto-approve from PreToolUse. Empty output lets the
            # command continue through its normal permission flow: faithful
            # for defer, but a lossy degradation for allow and ask. In
            # particular, ask does not guarantee that Codex will prompt.
            return {}, 0
        if outcome == "deny":
            hook_specific_output = {
                "hookEventName": _NATIVE_EVENT,
                "permissionDecision": "deny",
                "permissionDecisionReason": verdict.get("reason", ""),
            }
            return {"hookSpecificOutput": hook_specific_output}, 0
        raise RunnerError(f"codex codec cannot encode outcome {outcome!r}")


def _decode_tool(raw: dict[str, Any]) -> dict[str, Any]:
    tool_name = raw.get("tool_name")
    kind = _NORMALISE.get(tool_name) if isinstance(tool_name, str) else None
    if kind is None:
        raise RunnerError(f"codex tool {tool_name!r} has no generic kind (Unsupported)")
    tool_input = _require_mapping(raw.get("tool_input"))
    command = tool_input.get("command")
    if not isinstance(command, str):
        raise RunnerError("codex Bash tool_input missing 'command'")
    return {"kind": "shell", "command": command}


def _require_mapping(raw: object) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise RunnerError("codex Bash tool_input missing 'command'")
    return raw  # pyright: ignore[reportUnknownVariableType]


class _CodexAdapter:
    codecs: dict[str, Codec] = {_NATIVE_EVENT: _CodexToolBeforeCodec()}

    def native_event(self, raw: dict[str, Any]) -> str:
        event = raw.get("hook_event_name")
        if not isinstance(event, str):
            raise RunnerError("codex native event missing 'hook_event_name'")
        return event


codex_adapter = _CodexAdapter()
