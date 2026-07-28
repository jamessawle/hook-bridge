"""claude-code `PreToolUse` <-> Contract `tool.before` Codec."""

from __future__ import annotations

from typing import Any

from ...codec import Codec, RunnerError
from .common import decode_base, decode_tool


class _ClaudeCodeToolBeforeCodec:
    native_event = "PreToolUse"
    contract_event = "tool.before"

    def decode(self, raw: dict[str, Any]) -> dict[str, Any]:
        context = decode_base(
            raw,
            native_event=self.native_event,
            contract_event=self.contract_event,
        )
        context["tool"] = decode_tool(raw)
        return context

    def encode(self, verdict: dict[str, Any]) -> tuple[dict[str, Any], int]:
        outcome = verdict.get("outcome")
        if outcome == "defer":
            return {}, 0
        if outcome in ("allow", "deny", "ask"):
            hook_specific_output: dict[str, Any] = {
                "hookEventName": self.native_event,
                "permissionDecision": outcome,
            }
            if outcome in ("deny", "ask"):
                hook_specific_output["permissionDecisionReason"] = verdict.get(
                    "reason", ""
                )
            return {"hookSpecificOutput": hook_specific_output}, 0
        raise RunnerError(f"claude-code codec cannot encode outcome {outcome!r}")


codec: Codec = _ClaudeCodeToolBeforeCodec()
