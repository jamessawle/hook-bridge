"""claude-code `PostToolUse` <-> Contract `tool.after` Codec."""

from __future__ import annotations

from typing import Any

from ...codec import Codec, RunnerError
from .common import decode_base, decode_tool, require_mapping


class _ClaudeCodeToolAfterCodec:
    native_event = "PostToolUse"
    contract_event = "tool.after"

    def decode(self, raw: dict[str, Any]) -> dict[str, Any]:
        context = decode_base(
            raw,
            native_event=self.native_event,
            contract_event=self.contract_event,
        )
        context["tool"] = decode_tool(raw)
        context["result"] = self._decode_result(raw)
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

    @staticmethod
    def _decode_result(raw: dict[str, Any]) -> dict[str, Any]:
        tool_response = require_mapping(
            raw.get("tool_response"), "claude-code tool_response"
        )
        text = tool_response.get("text")
        exit_code = tool_response.get("exitCode")
        if not isinstance(text, str):
            raise RunnerError("claude-code tool_response missing 'text'")
        if not isinstance(exit_code, int) or isinstance(exit_code, bool):
            raise RunnerError("claude-code tool_response missing 'exitCode'")
        return {"text": text, "exit_code": exit_code}


codec: Codec = _ClaudeCodeToolAfterCodec()
