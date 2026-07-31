"""Boundary schema validation for the generic wire Contract.

Per ADR-0003, the Contract crosses a process edge as JSON, so the seam is
stringly-typed. This module is the loud gate on that seam: it validates the
generic Context read from stdin and the generic Verdict written to stdout,
failing with a `BoundaryError` rather than passing garbage into (or out of) a
Hook.

This is the *generic* wire — the neutral Contract JSON, not any harness's native
protocol. Translating a harness's native shape to and from this wire is the
Adapter's job (a separate concern in the runner), never the Hook's or the SDK's.

Validation is hand-rolled and dependency-free on purpose, and a lean SDK keeps
`uv run` materialisation fast.
"""

from __future__ import annotations

from typing import Any, cast

from .contract import (
    ClaudeCode,
    ClaudeCodeTool,
    Codex,
    CodexTool,
    Context,
    Json,
    ShellTool,
    TerminalObservation,
    Tool,
    ToolAfterContext,
    ToolAfterOutcome,
    ToolAfterVerdict,
    ToolBeforeContext,
    ToolBeforeOutcome,
    ToolBeforeVerdict,
    ToolError,
    ToolResult,
    Verdict,
)


class BoundaryError(Exception):
    """A payload crossing the wire boundary did not match the Contract.

    Raised on a malformed Context read from stdin or an un-encodable Verdict —
    the loud failure ADR-0003 mandates, never a silent pass-through.
    """


# ---------------------------------------------------------------------------
# Small validation primitives — each names the field so the error points at it.
# ---------------------------------------------------------------------------


def _require_mapping(raw: object, what: str) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise BoundaryError(f"{what} must be a JSON object, got {type(raw).__name__}")
    return raw  # pyright: ignore[reportUnknownVariableType]


def _require_str(mapping: dict[str, Any], key: str, what: str) -> str:
    if key not in mapping:
        raise BoundaryError(f"{what} is missing required field {key!r}")
    value = mapping[key]
    if not isinstance(value, str):
        raise BoundaryError(f"{what} field {key!r} must be a string, got {type(value).__name__}")
    return value


def _require_json(value: object, what: str) -> Json:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, list):
        return [_require_json(item, f"{what} item") for item in cast(list[object], value)]
    if isinstance(value, dict):
        result: dict[str, Json] = {}
        for key, item in cast(dict[object, object], value).items():
            if not isinstance(key, str):
                raise BoundaryError(f"{what} keys must be strings")
            result[key] = _require_json(item, f"{what} field {key!r}")
        return result
    raise BoundaryError(f"{what} must be JSON, got {type(value).__name__}")


def _require_field(mapping: dict[str, Any], key: str, what: str) -> object:
    if key not in mapping:
        raise BoundaryError(f"{what} is missing required field {key!r}")
    return mapping[key]


# ---------------------------------------------------------------------------
# Context: wire dict -> typed Context. Dispatches on the `event` discriminator
# and builds the concrete per-event type, so a Hook never sees a Context whose
# event it can't consume.
# ---------------------------------------------------------------------------

def decode_context(raw: object) -> Context:
    mapping = _require_mapping(raw, "Context")
    event = _require_str(mapping, "event", "Context")
    if event == "tool.before":
        return _decode_tool_before(mapping)
    if event == "tool.after":
        return _decode_tool_after(mapping)
    raise BoundaryError(f"unknown event {event!r}")


def _decode_tool_before(mapping: dict[str, Any]) -> ToolBeforeContext:
    session_id = _require_str(mapping, "session_id", "ToolBeforeContext")
    cwd = _require_str(mapping, "cwd", "ToolBeforeContext")
    tool = _decode_tool(mapping.get("tool"))
    return ToolBeforeContext(session_id=session_id, cwd=cwd, tool=tool)


def _decode_tool_after(mapping: dict[str, Any]) -> ToolAfterContext:
    session_id = _require_str(mapping, "session_id", "ToolAfterContext")
    cwd = _require_str(mapping, "cwd", "ToolAfterContext")
    tool = _decode_tool(mapping.get("tool"))
    observation = _decode_observation(mapping.get("observation"))
    return ToolAfterContext(
        session_id=session_id, cwd=cwd, tool=tool, observation=observation
    )


def _decode_tool(raw: object) -> Tool:
    mapping = _require_mapping(raw, "tool")
    harness_name = _require_str(mapping, "harness", "tool")
    native = _require_mapping(mapping.get("native"), "tool Native data")
    data = _require_json(native, "tool Native data")
    assert isinstance(data, dict)
    if harness_name == ClaudeCode.name:
        harness, native_tool = ClaudeCode(), ClaudeCodeTool(data)
    elif harness_name == Codex.name:
        harness, native_tool = Codex(), CodexTool(data)
    else:
        raise BoundaryError(f"unknown Harness {harness_name!r}")
    projection = _decode_projection(mapping.get("projection"))
    return Tool(harness=harness, native=native_tool, projection=projection)


def _decode_projection(raw: object) -> ShellTool | None:
    if raw is None:
        return None
    mapping = _require_mapping(raw, "Tool projection")
    kind = _require_str(mapping, "kind", "Tool projection")
    if kind == "shell":
        return ShellTool(command=_require_str(mapping, "command", "shell projection"))
    raise BoundaryError(f"unknown Tool projection kind {kind!r}")


def _decode_observation(raw: object) -> TerminalObservation:
    mapping = _require_mapping(raw, "Terminal observation")
    kind = _require_str(mapping, "kind", "Terminal observation")
    if kind == "result":
        return ToolResult(_require_json(_require_field(mapping, "output", "ToolResult"), "ToolResult output"))
    if kind == "error":
        return ToolError(_require_json(_require_field(mapping, "error", "ToolError"), "ToolError error"))
    raise BoundaryError(f"unknown Terminal observation kind {kind!r}")


# ---------------------------------------------------------------------------
# Verdict: typed Verdict -> wire dict. deny/ask carry a mandatory reason;
# allow/defer never carry one.
# ---------------------------------------------------------------------------


def encode_verdict(verdict: Verdict) -> dict[str, Any]:
    if isinstance(verdict, ToolBeforeVerdict):
        return _encode_tool_before(verdict)
    if isinstance(verdict, ToolAfterVerdict):
        return _encode_tool_after(verdict)
    raise BoundaryError(f"cannot encode verdict of type {type(verdict).__name__}")


def _encode_tool_before(verdict: ToolBeforeVerdict) -> dict[str, Any]:
    outcome: ToolBeforeOutcome = verdict.outcome
    body: dict[str, Any] = {"outcome": outcome}
    if outcome in ("deny", "ask"):
        if not verdict.reason:
            raise BoundaryError(f"a {outcome!r} verdict requires a reason")
        body["reason"] = verdict.reason
    return body


def _encode_tool_after(verdict: ToolAfterVerdict) -> dict[str, Any]:
    outcome: ToolAfterOutcome = verdict.outcome
    body: dict[str, Any] = {"outcome": outcome}
    if outcome in ("block", "annotate"):
        if not verdict.message:
            raise BoundaryError(f"a {outcome!r} verdict requires a message")
        body["message"] = verdict.message
    return body
