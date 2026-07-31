"""claude-code `PostToolUseFailure` <-> Contract `tool.after` Codec."""

from __future__ import annotations

from typing import Any

from ...codec import Codec, RunnerError
from .common import decode_base, decode_tool


class _ClaudeCodeToolAfterFailureCodec:
    native_event = "PostToolUseFailure"
    contract_event = "tool.after"

    def decode(self, raw: dict[str, Any]) -> dict[str, Any]:
        context = decode_base(
            raw,
            native_event=self.native_event,
            contract_event=self.contract_event,
        )
        context["tool"] = decode_tool(raw)
        error = raw.get("error")
        if not isinstance(error, str):
            raise RunnerError(
                "claude-code PostToolUseFailure payload missing 'error'"
            )
        context["observation"] = {"kind": "error", "error": error}
        return context

    def encode(self, verdict: dict[str, Any]) -> tuple[dict[str, Any], int]:
        outcome = verdict.get("outcome")
        if outcome == "pass":
            return {}, 0
        if outcome == "block":
            return {"decision": "block", "reason": verdict.get("message", "")}, 0
        if outcome == "annotate":
            hook_specific_output = {
                "hookEventName": self.native_event,
                "additionalContext": verdict.get("message", ""),
            }
            return {"hookSpecificOutput": hook_specific_output}, 0
        raise RunnerError(f"claude-code codec cannot encode outcome {outcome!r}")


codec: Codec = _ClaudeCodeToolAfterFailureCodec()
