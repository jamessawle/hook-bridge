"""The generic Contract: the harness-agnostic types a Hook is written against.

A Hook receives a `Context` and returns a `Verdict` (see ../../../../CONTEXT.md).
Both are discriminated unions of per-event types (#5): a `Context`'s `event` is
the discriminator, and code written for a given event can only construct the
`Verdict` valid for that event, so invalid event/verdict pairs are
unrepresentable at authoring time.

Portable projections are the ordinary Harness-agnostic authoring path. Every
Tool also retains explicitly Harness-specific Native data so unknown Tools and
schema drift remain observable; inspecting it deliberately trades portability
for fidelity (ADR-0007).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar, Literal

# ---------------------------------------------------------------------------
# Tool model — a required, lossless Native view paired with an optional portable
# projection (ADR-0007 and ADR-0008).
# ---------------------------------------------------------------------------

type Json = None | bool | int | float | str | list[Json] | dict[str, Json]


@dataclass(frozen=True)
class ClaudeCode:
    """The Claude Code Harness discriminator."""

    name: ClassVar[Literal["claude-code"]] = "claude-code"


@dataclass(frozen=True)
class Codex:
    """The Codex Harness discriminator."""

    name: ClassVar[Literal["codex"]] = "codex"


Harness = ClaudeCode | Codex


@dataclass(frozen=True)
class ClaudeCodeTool:
    """Claude Code's complete Tool view at the observed hook event."""

    data: dict[str, Json]


@dataclass(frozen=True)
class CodexTool:
    """Codex's complete Tool view at the observed hook event."""

    data: dict[str, Json]


NativeTool = ClaudeCodeTool | CodexTool


@dataclass(frozen=True)
class ShellTool:
    """The portable projection of a shell command invocation."""

    command: str
    kind: Literal["shell"] = "shell"


ToolProjection = ShellTool


@dataclass(frozen=True)
class Tool:
    """A Tool's trusted Harness identity, Native data, and optional projection."""

    harness: Harness
    native: NativeTool
    projection: ToolProjection | None = None

    def __post_init__(self) -> None:
        mismatched = (
            isinstance(self.harness, ClaudeCode) and isinstance(self.native, CodexTool)
        ) or (isinstance(self.harness, Codex) and isinstance(self.native, ClaudeCodeTool))
        if mismatched:
            raise ValueError("Tool harness and Native data must describe the same Harness")


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


@dataclass(frozen=True)
class ToolResult:
    """A response delivered through a Harness's normal result path."""

    output: Json


@dataclass(frozen=True)
class ToolError:
    """An error authoritatively identified by a Harness."""

    error: Json


TerminalObservation = ToolResult | ToolError


@dataclass(frozen=True)
class ToolAfterContext(Context):
    """The `tool.after` event: a tool has already run."""

    event: ClassVar[str] = "tool.after"
    tool: Tool
    observation: TerminalObservation


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


# ---------------------------------------------------------------------------
# `tool.after` Verdict (ADR-0006): a tool has already run, so permission
# verbs (`allow`/`deny`/`ask`) have no meaning. Three verbs instead: `pass_`
# (no opinion), `block` (stop the agent proceeding, with a reason),
# `annotate` (inject context without blocking).
# ---------------------------------------------------------------------------

ToolAfterOutcome = Literal["pass", "block", "annotate"]


@dataclass(frozen=True)
class ToolAfterVerdict(Verdict):
    """The Verdict for a `tool.after` event.

    Three generic outcomes (v1): `pass_` (no opinion), `block` (stop the
    agent from proceeding, with a mandatory reason) and `annotate` (inject
    context for the agent without blocking, with mandatory content).
    Rewriting the tool's own output is a documented, unbuilt seam.

    Construct these via the `pass_()` / `block()` / `annotate()` helpers
    rather than directly.
    """

    outcome: ToolAfterOutcome
    message: str | None = None

    @property
    def is_pass(self) -> bool:
        return self.outcome == "pass"

    @property
    def is_block(self) -> bool:
        return self.outcome == "block"

    @property
    def is_annotate(self) -> bool:
        return self.outcome == "annotate"


def pass_() -> ToolAfterVerdict:
    """Express no opinion — nothing is surfaced to the harness."""
    return ToolAfterVerdict("pass")


def block(reason: str) -> ToolAfterVerdict:
    """Stop the agent from proceeding. The reason is surfaced to the model/user."""
    return ToolAfterVerdict("block", reason)


def annotate(context: str) -> ToolAfterVerdict:
    """Inject context for the agent, without blocking."""
    return ToolAfterVerdict("annotate", context)
