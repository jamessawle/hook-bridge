"""Native claude-code decoding shared by more than one Codec."""

from __future__ import annotations

from typing import Any

from ...codec import RunnerError

_NORMALISE: dict[str, str] = {"Bash": "shell"}


def decode_base(
    raw: dict[str, Any],
    *,
    native_event: str,
    contract_event: str,
) -> dict[str, Any]:
    event = raw.get("hook_event_name")
    if event != native_event:
        raise RunnerError(
            f"claude-code {contract_event} codec received a misrouted event {event!r}"
        )
    session_id = raw.get("session_id")
    cwd = raw.get("cwd")
    if not isinstance(session_id, str) or not isinstance(cwd, str):
        raise RunnerError(
            f"claude-code {native_event} payload missing 'session_id'/'cwd'"
        )
    return {
        "event": contract_event,
        "session_id": session_id,
        "cwd": cwd,
    }


def decode_tool(raw: dict[str, Any]) -> dict[str, Any]:
    tool_name = raw.get("tool_name")
    kind = _NORMALISE.get(tool_name) if isinstance(tool_name, str) else None
    if kind is None:
        raise RunnerError(
            f"claude-code tool {tool_name!r} has no generic kind (Unsupported)"
        )
    tool_input = require_mapping(
        raw.get("tool_input"), "claude-code Bash tool_input"
    )
    command = tool_input.get("command")
    if not isinstance(command, str):
        raise RunnerError("claude-code Bash tool_input missing 'command'")
    return {"kind": kind, "command": command}


def require_mapping(raw: object, what: str) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise RunnerError(f"{what} missing or malformed")
    return raw  # pyright: ignore[reportUnknownVariableType]
