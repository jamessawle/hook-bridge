"""Boundary schema validation for the generic wire Contract.

Per ADR-0001, the Contract crosses a process edge as JSON, so the seam is
stringly-typed. This module is the loud gate on that seam: it validates the
generic Context read from stdin and the generic Verdict written to stdout,
failing with a `BoundaryError` rather than passing garbage into (or out of) a
Hook.

This is the *generic* wire — the neutral Contract JSON, not any harness's native
protocol. Translating a harness's native shape to and from this wire is the
Adapter's job (a separate concern in the runner), never the Hook's or the SDK's.

Validation is hand-rolled and dependency-free on purpose: the v1 slice is small
(one event, one tool kind, four verdicts), and a lean SDK keeps `uv run`
materialisation fast.
"""

from __future__ import annotations

from typing import Any

from .contract import (
    Context,
    ShellTool,
    ToolAfterContext,
    ToolAfterOutcome,
    ToolAfterVerdict,
    ToolBeforeContext,
    ToolBeforeOutcome,
    ToolBeforeVerdict,
    ToolResult,
    Verdict,
)


class BoundaryError(Exception):
    """A payload crossing the wire boundary did not match the Contract.

    Raised on a malformed Context read from stdin or an un-encodable Verdict —
    the loud failure ADR-0001 mandates, never a silent pass-through.
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


def _require_int(mapping: dict[str, Any], key: str, what: str) -> int:
    if key not in mapping:
        raise BoundaryError(f"{what} is missing required field {key!r}")
    value = mapping[key]
    if not isinstance(value, int) or isinstance(value, bool):
        raise BoundaryError(f"{what} field {key!r} must be an int, got {type(value).__name__}")
    return value


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
    result = _decode_result(mapping.get("result"))
    return ToolAfterContext(session_id=session_id, cwd=cwd, tool=tool, result=result)


def _decode_tool(raw: object) -> ShellTool:
    mapping = _require_mapping(raw, "tool")
    kind = _require_str(mapping, "kind", "tool")
    if kind == "shell":
        command = _require_str(mapping, "command", "shell tool")
        return ShellTool(command=command)
    raise BoundaryError(f"unknown tool kind {kind!r}")


def _decode_result(raw: object) -> ToolResult:
    mapping = _require_mapping(raw, "result")
    text = _require_str(mapping, "text", "result")
    exit_code = _require_int(mapping, "exit_code", "result")
    return ToolResult(text=text, exit_code=exit_code)


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
