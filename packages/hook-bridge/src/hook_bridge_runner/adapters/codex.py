"""The codex harness Adapter (#12).

Codex's hook system was deliberately modelled on claude-code's — same
`hook_event_name`/`tool_name`/`tool_input` field names on the way in, same
`hookSpecificOutput.permissionDecision` shape on the way out. Confirmed live
against codex-cli 0.145.0 (#13): codex's own embedded output JSON Schema
marks `hookSpecificOutput.hookEventName` as **required** — omitting it makes
the whole response schema-invalid, so codex silently discards the decision
(logged as `hook: PreToolUse Failed`) and lets the command through regardless
of `permissionDecision`. `ask` is parsed but not yet honoured by codex even
with a schema-valid response (tracked in #18). See
https://developers.openai.com/codex/hooks for the native protocol this codes.
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
        if outcome == "defer":
            # No opinion: emit nothing so codex's normal permission flow
            # decides, per #8's `defer` semantics.
            return {}, 0
        if outcome in ("allow", "deny", "ask"):
            hook_specific_output: dict[str, Any] = {
                "hookEventName": _NATIVE_EVENT,
                "permissionDecision": outcome,
            }
            if outcome in ("deny", "ask"):
                hook_specific_output["permissionDecisionReason"] = verdict.get("reason", "")
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
