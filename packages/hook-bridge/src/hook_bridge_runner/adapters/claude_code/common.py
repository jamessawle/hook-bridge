"""Native claude-code decoding shared by more than one Codec."""

from __future__ import annotations

from typing import Any, cast

from ...codec import RunnerError

type Json = None | bool | int | float | str | list[Json] | dict[str, Json]


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
    tool_use_id = raw.get("tool_use_id")
    if not isinstance(tool_name, str) or not isinstance(tool_use_id, str):
        raise RunnerError("claude-code tool payload missing 'tool_name'/'tool_use_id'")
    tool_input = require_mapping(
        raw.get("tool_input"), "claude-code tool_input"
    )
    native = require_json_mapping(raw, "claude-code Native Tool data")
    return {
        "harness": "claude-code",
        "native": native,
        "projection": decode_projection(tool_name, tool_input),
    }


def decode_projection(
    tool_name: str, tool_input: dict[str, Any]
) -> dict[str, Any] | None:
    """Return only projections whose required fields are faithfully present."""
    if tool_name != "Bash":
        return None
    command = tool_input.get("command")
    if not isinstance(command, str):
        return None
    return {"kind": "shell", "command": command}


def require_mapping(raw: object, what: str) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise RunnerError(f"{what} missing or malformed")
    return raw  # pyright: ignore[reportUnknownVariableType]


def require_json(raw: object, what: str) -> Json:
    """Validate and copy a JSON value before it crosses the generic wire."""
    if raw is None or isinstance(raw, (bool, int, float, str)):
        return raw
    if isinstance(raw, list):
        return [
            require_json(item, f"{what} item")
            for item in cast(list[object], raw)
        ]
    if isinstance(raw, dict):
        result: dict[str, Json] = {}
        for key, item in cast(dict[object, object], raw).items():
            if not isinstance(key, str):
                raise RunnerError(f"{what} keys must be strings")
            result[key] = require_json(item, f"{what} field {key!r}")
        return result
    raise RunnerError(f"{what} must be JSON")


def require_json_mapping(raw: object, what: str) -> dict[str, Json]:
    value = require_json(raw, what)
    if not isinstance(value, dict):
        raise RunnerError(f"{what} must be a JSON object")
    return cast(dict[str, Json], value)
