"""codex `PostToolUse` <-> Contract `tool.after` Codec."""

from __future__ import annotations

from typing import Any

from ...codec import Codec, RunnerError
from .common import Json, decode_base, decode_tool, require_json


class _CodexToolAfterCodec:
    native_event = "PostToolUse"
    contract_event = "tool.after"

    def decode(self, raw: dict[str, Any]) -> dict[str, Any]:
        context = decode_base(
            raw,
            native_event=self.native_event,
            contract_event=self.contract_event,
        )
        context["tool"] = decode_tool(raw)
        if "tool_response" not in raw:
            raise RunnerError("codex PostToolUse payload missing 'tool_response'")
        response = require_json(raw["tool_response"], "codex tool_response")
        context["observation"] = self._decode_observation(raw, response)
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
        raise RunnerError(f"codex codec cannot encode outcome {outcome!r}")

    @staticmethod
    def _decode_observation(
        raw: dict[str, Any], response: Json
    ) -> dict[str, Any]:
        tool_name = raw.get("tool_name")
        is_authoritative_mcp_error = (
            isinstance(tool_name, str)
            and tool_name.startswith("mcp__")
            and isinstance(response, dict)
            and response.get("isError") is True
        )
        if is_authoritative_mcp_error:
            return {"kind": "error", "error": response}
        return {"kind": "result", "output": response}


codec: Codec = _CodexToolAfterCodec()
