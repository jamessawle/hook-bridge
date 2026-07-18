"""The generic Contract: the harness-agnostic types a Hook is written against.

A Hook receives a `Context` and returns a `Verdict`, with **zero** knowledge of
which Harness invoked it (see ../../../../CONTEXT.md). Both are discriminated
unions of per-event types (#5): a `Context`'s `event` is the discriminator, and
code written for a given event can only construct the `Verdict` valid for that
event, so invalid event/verdict pairs are unrepresentable at authoring time.

No harness-specific vocabulary appears here — that is the whole point of the
Adapter boundary. This module holds only concepts that generalise across
harnesses; the runner's Adapters absorb everything else.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar, Literal

# ---------------------------------------------------------------------------
# Tool model — generic and normalised, never harness pass-through (#5).
# Discriminated on a generic `kind`; each Adapter maps its native tool name onto
# one of these members (v1: claude-code `Bash` / codex `shell` → `shell`).
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ShellTool:
    """A shell command invocation. v1's only tool kind."""

    command: str
    kind: Literal["shell"] = "shell"


# A union of one, in spirit: `tool` is discriminated on `.kind`, so new kinds
# (`file_edit`, `web_fetch`, …) slot in as additional members with no change to
# the Context type. Kept as an alias so the discriminated shape is explicit.
Tool = ShellTool


# ---------------------------------------------------------------------------
# Context — a discriminated union of per-event types. Common base + per-event
# subtype. `event` is a Literal discriminator carrying the canonical name.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Context:
    """Fields common to every event's Context.

    `event` is the canonical-name discriminator. It is a plain class constant
    (`ClassVar`), not an instance field: a Context type *owns* its own event
    name, so the runner learns a Hook's event with a bare attribute read and
    there is no Literal to reflect out. Each subtype sets its own value.
    """

    event: ClassVar[str]
    session_id: str
    cwd: str


@dataclass(frozen=True)
class ToolBeforeContext(Context):
    """The `tool.before` event: a tool is about to run."""

    event: ClassVar[str] = "tool.before"
    tool: Tool


# ---------------------------------------------------------------------------
# Verdict — symmetric per-event discriminated union. Code written for `tool.before`
# can only return a `ToolBeforeVerdict`, so event/verdict mismatches can't compile.
# ---------------------------------------------------------------------------


class Verdict:
    """Marker base for every event's Verdict type."""


ToolBeforeOutcome = Literal["allow", "deny", "ask", "defer"]


@dataclass(frozen=True)
class ToolBeforeVerdict(Verdict):
    """The Verdict for a `tool.before` event.

    Four generic outcomes (v1): `allow` (proceed, auto-approved), `deny` (block,
    with a mandatory reason), `ask` (prompt before proceeding, with a reason) and
    `defer` (no opinion — let the harness's normal permission flow decide).
    `modify` (updated tool input) is a documented seam, not yet built.

    Construct these via the `allow()` / `deny()` / `ask()` / `defer()` helpers
    rather than directly.
    """

    outcome: ToolBeforeOutcome
    reason: str | None = None

    @property
    def is_allow(self) -> bool:
        return self.outcome == "allow"

    @property
    def is_deny(self) -> bool:
        return self.outcome == "deny"

    @property
    def is_ask(self) -> bool:
        return self.outcome == "ask"

    @property
    def is_defer(self) -> bool:
        return self.outcome == "defer"


# ---------------------------------------------------------------------------
# Verdict helpers — the authoring surface. `deny`/`ask` require a reason (the
# Adapter maps it to each harness's reason field); `allow`/`defer` carry none.
# ---------------------------------------------------------------------------


def allow() -> ToolBeforeVerdict:
    """Proceed — auto-approve the tool call."""
    return ToolBeforeVerdict("allow")


def deny(reason: str) -> ToolBeforeVerdict:
    """Block the tool call. The reason is surfaced to the model/user."""
    return ToolBeforeVerdict("deny", reason)


def ask(reason: str) -> ToolBeforeVerdict:
    """Prompt for confirmation before the tool call proceeds."""
    return ToolBeforeVerdict("ask", reason)


def defer() -> ToolBeforeVerdict:
    """Express no opinion — the harness's normal permission flow decides."""
    return ToolBeforeVerdict("defer")
