"""PROTOTYPE: pure annotation-driven Hook filtering logic."""

from __future__ import annotations

import inspect
import types
import typing
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any, ClassVar, Literal, TypeVar

Json = None | bool | int | float | str | list["Json"] | dict[str, "Json"]


@dataclass(frozen=True)
class ClaudeCode:
    name: ClassVar[Literal["claude-code"]] = "claude-code"


@dataclass(frozen=True)
class Codex:
    name: ClassVar[Literal["codex"]] = "codex"


Harness = ClaudeCode | Codex


@dataclass(frozen=True)
class ClaudeCodeTool:
    tool_name: str
    tool_input: dict[str, Json]


@dataclass(frozen=True)
class CodexTool:
    tool_name: str
    tool_input: dict[str, Json]


NativeTool = ClaudeCodeTool | CodexTool


@dataclass(frozen=True)
class ShellTool:
    command: str


@dataclass(frozen=True)
class FileEditTool:
    path: str
    content: str


ToolProjection = ShellTool | FileEditTool


@dataclass(frozen=True)
class Tool:
    harness: Harness
    native: NativeTool
    projection: ToolProjection | None


@dataclass(frozen=True)
class ToolResult:
    value: Json


@dataclass(frozen=True)
class ToolError:
    error: Json


TerminalObservation = ToolResult | ToolError


@dataclass(frozen=True)
class ToolBeforeVerdict:
    outcome: Literal["allow", "deny", "ask", "defer"]
    message: str | None = None


@dataclass(frozen=True)
class ToolAfterVerdict:
    outcome: Literal["pass", "block", "annotate"]
    message: str | None = None


Verdict = ToolBeforeVerdict | ToolAfterVerdict


@dataclass(frozen=True)
class ToolBeforeContext:
    event: ClassVar[Literal["tool.before"]] = "tool.before"
    tool: Tool


@dataclass(frozen=True)
class ToolAfterContext:
    event: ClassVar[Literal["tool.after"]] = "tool.after"
    tool: Tool
    observation: TerminalObservation


Context = ToolBeforeContext | ToolAfterContext
C = TypeVar("C", bound=Context)
V = TypeVar("V", bound=Verdict)


def neutral(ctx: Context) -> Verdict:
    if isinstance(ctx, ToolBeforeContext):
        return ToolBeforeVerdict("defer")
    return ToolAfterVerdict("pass")


@dataclass(frozen=True)
class Match:
    matched: bool
    checks: tuple[str, ...]
    arguments: tuple[object, ...]


class Hook(typing.Generic[C, V]):
    def __init__(self, fn: Callable[..., V]) -> None:
        self.fn = fn
        self.name = fn.__name__
        signature = inspect.signature(fn)
        self.parameter_names = tuple(signature.parameters)
        hints = typing.get_type_hints(fn)
        self.parameter_types = tuple(hints[name] for name in self.parameter_names)
        context_types = [t for t in self.parameter_types if t in (ToolBeforeContext, ToolAfterContext)]
        if len(context_types) != 1:
            raise TypeError("a Hook needs exactly one ToolBeforeContext or ToolAfterContext parameter")
        self.context_type: type[Context] = context_types[0]

    @property
    def signature(self) -> str:
        return f"{self.name}{inspect.signature(self.fn)}"

    def match(self, ctx: Context) -> Match:
        checks: list[str] = []
        arguments: list[object] = []
        for annotation in self.parameter_types:
            value, reason = _resolve(annotation, ctx)
            checks.append(reason)
            if value is _NO_MATCH:
                return Match(False, tuple(checks), ())
            arguments.append(value)
        return Match(True, tuple(checks), tuple(arguments))

    def dispatch(self, ctx: Context) -> V | Verdict:
        match = self.match(ctx)
        if not match.matched:
            return neutral(ctx)
        return self.fn(*match.arguments)


def hook(fn: Callable[..., V]) -> Hook[Any, V]:
    return Hook(fn)


_NO_MATCH = object()


def _resolve(annotation: object, ctx: Context) -> tuple[object, str]:
    if annotation in (ToolBeforeContext, ToolAfterContext):
        if isinstance(ctx, annotation):
            return ctx, f"event: {annotation.event} ✓"
        return _NO_MATCH, f"event: {annotation.event} ✗"
    if annotation is Tool:
        return ctx.tool, "Tool envelope: any Tool ✓"
    if annotation in (ShellTool, FileEditTool):
        if isinstance(ctx.tool.projection, annotation):
            return ctx.tool.projection, f"projection: {annotation.__name__} ✓"
        actual = type(ctx.tool.projection).__name__ if ctx.tool.projection is not None else "absent"
        return _NO_MATCH, f"projection: {annotation.__name__} ✗ ({actual})"
    if annotation in (ToolResult, ToolError):
        observation = ctx.observation if isinstance(ctx, ToolAfterContext) else None
        if isinstance(observation, annotation):
            return observation, f"observation: {annotation.__name__} ✓"
        actual = type(observation).__name__ if observation is not None else "not a terminal event"
        return _NO_MATCH, f"observation: {annotation.__name__} ✗ ({actual})"
    if annotation in (ClaudeCode, Codex):
        if isinstance(ctx.tool.harness, annotation):
            return ctx.tool.harness, f"Harness: {annotation.name} ✓"
        return _NO_MATCH, f"Harness: {annotation.name} ✗ ({ctx.tool.harness.name})"
    if annotation in (ClaudeCodeTool, CodexTool):
        if isinstance(ctx.tool.native, annotation):
            return ctx.tool.native, f"Native data: {annotation.__name__} ✓"
        return _NO_MATCH, f"Native data: {annotation.__name__} ✗"
    return _NO_MATCH, f"unsupported annotation: {annotation!r} ✗"


@dataclass(frozen=True)
class DispatchTrace:
    hook: Hook[Any, Any]
    match: Match


@dataclass(frozen=True)
class CompositionResult:
    traces: tuple[DispatchTrace, ...]
    selected: Hook[Any, Any] | None
    injected_types: tuple[str, ...]
    verdict: Verdict


def dispatch_first(hooks: Sequence[Hook[Any, Any]], ctx: Context) -> CompositionResult:
    traces: list[DispatchTrace] = []
    for candidate in hooks:
        match = candidate.match(ctx)
        traces.append(DispatchTrace(candidate, match))
        if match.matched:
            verdict = candidate.fn(*match.arguments)
            return CompositionResult(
                tuple(traces),
                candidate,
                tuple(type(value).__name__ for value in match.arguments),
                verdict,
            )
    return CompositionResult(tuple(traces), None, (), neutral(ctx))


def union_members(annotation: object) -> tuple[object, ...]:
    if isinstance(annotation, types.UnionType):
        return typing.get_args(annotation)
    return (annotation,)
