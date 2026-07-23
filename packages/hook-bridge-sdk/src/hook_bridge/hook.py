"""The `@hook` decorator and the IO shell.

One Hook = one event (per CONTEXT.md: a Hook reacts to *a* harness event). The
author decorates one annotated function; the decorated function *becomes* the Hook
— a `Hook[C, V]`. There is no router, registry, event string, or overload table
(#6): the event identity rides on the annotated `Context` type.

`hook.dispatch(ctx)` is the pure, harness-free test seam. `hook.run()` is only
its stdin/stdout shell — generic Context JSON in, generic Verdict JSON out. The
exit code reports Hook **health** (0 = a Verdict was emitted; nonzero = crash or
boundary-validation failure), never allow/deny.
"""

from __future__ import annotations

import inspect
import json
import sys
import typing
from collections.abc import Callable
from typing import Any, Generic, TypeVar

from .contract import Context, Verdict
from .wire import BoundaryError, decode_context, encode_verdict

C = TypeVar("C", bound=Context)
V = TypeVar("V", bound=Verdict)


class Hook(Generic[C, V]):
    """A single-event Hook: a pure function plus the IO shell that runs it.

    `event` is intrinsic — a one-event Hook *is* its event. It is read once, at
    decoration time, from the `Context` type the function is annotated with (the
    same annotation #6 already requires to validate the signature). The Context
    type exposes `event` as a plain attribute, so there is nothing magical to
    reflect — just an attribute read.
    """

    def __init__(self, fn: Callable[[C], V]) -> None:
        self._fn = fn
        self.event: str = _event_of(fn)

    def dispatch(self, ctx: C) -> V:
        """Run the pure function. The harness-free test seam — no IO, no JSON."""
        return self._fn(ctx)

    def run(self) -> None:
        """Read one generic Context from stdin, dispatch, write the Verdict to
        stdout. Exits nonzero on a boundary failure or an error in the Hook
        (health only)."""
        _run_io([self])


def hook(fn: Callable[[C], V]) -> Hook[C, V]:
    """Turn a pure, annotated function into a runnable, testable Hook."""
    return Hook(fn)


def run(*hooks: Hook[Any, Any]) -> None:
    """Compose several one-event Hooks in a single file. The incoming Context's
    event selects which Hook handles it — an explicit compose at the entrypoint,
    still with no global registry."""
    _run_io(list(hooks))


def _event_of(fn: Callable[..., object]) -> str:
    """Read a function's event from the `Context` type its first parameter is
    annotated with. Raises if the annotation is missing (#6: annotations are
    required — an unannotated ctx is a Hook the runner cannot place)."""
    params = list(inspect.signature(fn).parameters)
    if not params:
        raise TypeError("@hook function must take a Context parameter")
    hints = typing.get_type_hints(fn)
    ctx_type: object = hints.get(params[0])
    if ctx_type is None:
        raise TypeError("@hook function must annotate its Context parameter")
    event: object = getattr(ctx_type, "event", None)
    if not isinstance(event, str):
        raise TypeError(f"Context type {ctx_type!r} must define a string `event`")
    return event


def _run_io(hooks: list[Hook[Any, Any]]) -> None:
    """The shared stdin→dispatch→stdout shell for `Hook.run()` and `run(*hooks)`.

    Any failure crossing the boundary — unreadable JSON, a Context that matches
    no composed Hook, or a validation error — exits nonzero with the reason on
    stderr. A clean dispatch writes the Verdict JSON and exits 0.
    """
    try:
        raw: object = json.loads(sys.stdin.read())
        ctx = decode_context(raw)
        selected = next((h for h in hooks if h.event == ctx.event), None)
        if selected is None:
            raise BoundaryError(f"no hook composed for event {ctx.event!r}")
        verdict = selected.dispatch(ctx)
        body = encode_verdict(verdict)
    except json.JSONDecodeError as exc:
        _fail(f"could not parse Context JSON from stdin: {exc}")
    except BoundaryError as exc:
        _fail(f"boundary validation failed: {exc}")
    else:
        print(json.dumps(body))


def _fail(message: str) -> typing.NoReturn:
    print(message, file=sys.stderr)
    raise SystemExit(1)
