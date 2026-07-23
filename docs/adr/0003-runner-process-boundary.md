# ADR-0003: The runner's process boundary — where translation lives, and how bytes cross it

- **Status**: Accepted
- **Date**: 2026-07-23
- **Resolves**: [Build: CLI & IO plumbing (the runner)](https://github.com/jamessawle/hook-bridge/issues/11)
- **Builds on**: ADR-0001 (subprocess invocation model), [Design: the HarnessAdapter model](https://github.com/jamessawle/hook-bridge/issues/8)

## Context

ADR-0001 locked the invocation model: hook-bridge spawns a Hook as a
subprocess (`uv run <hook>`), passing the generic Context as JSON on stdin
and reading the Verdict from stdout/exit code. #8 locked the Adapter model:
a `Codec` per `(harness, event)` cell, *chosen* — Hook-primary, by
`(harness flag, hook.event)` — before any payload is read, so a Context the
Hook can't consume is unrepresentable. #8 explicitly deferred one question to
this ticket: where does `run()` / Codec selection **physically** live —
inside the Hook's own `uv run` process, or a separate `hook-bridge` process —
and how do the Context/Verdict bytes cross that edge?

This matters because the SDK already ships a fixed shell (`Hook.run()`,
#6/#9): it reads *generic* Context JSON from stdin and writes generic Verdict
JSON to stdout, with zero harness knowledge. Any design has to route around
that fixed shape, and around two more constraints:

- **#7**: the runner package has no dependency on the SDK, so it cannot
  `import` a Hook module to read `hook.event` — the Hook's own third-party and
  SDK-typed imports only resolve inside its own `uv run` environment.
- Selecting `(harness, hook.event)` *before any payload is read* would require
  hook-bridge to learn `hook.event` from a process it hasn't started yet.

The naive fix — hook-bridge spawns the Hook once just to announce its event,
then again to actually run it, or interleaves an announce line ahead of the
Context JSON — either doubles the process-spawn cost ADR-0001 already
budgeted for, or invents a new wire protocol nobody asked for.

## Decision

**hook-bridge is a genuine translating process — one per event, exactly as
ADR-0001 costed — and it selects the Codec by peeking the *native* payload's
own event field, not by introspecting the Hook.**

Concretely:

1. hook-bridge reads the harness's native JSON from stdin.
2. It peeks that payload's own native event name (a per-Adapter concern —
   e.g. `raw["kind"]` for the `stub` Adapter) and looks up the `Codec`
   registered for `(harness, native event)`. Unknown harness or no Codec for
   this event is a loud, wiring-time failure, before the payload is decoded
   any further.
3. `Codec.decode` builds the generic wire Context — a plain dict shaped
   exactly like what the SDK's `decode_context` parses — and hook-bridge
   spawns `uv run <hook>` **once**, writing that JSON to its stdin.
4. The Hook process's own `hook.run()` — **unchanged by this ticket** — reads
   it, dispatches, and writes the generic Verdict JSON to stdout. Its
   existing dispatch-by-`ctx.event` check is what catches a misrouted payload
   (a Context whose event doesn't match the Hook's own): this is the
   `Misrouted` case #8 named, just detected one process-hop downstream of
   hook-bridge rather than inside it.
5. hook-bridge reads that Verdict JSON, and `Codec.encode` produces the
   native response body + exit code.

The runner never imports the SDK's typed `Context`/`Verdict` — it works
entirely in JSON-shaped dicts matching the shared wire schema (#7). The Hook
contract (`hook.run()`/`_run_io`, #6/#9) is **unchanged**: it still speaks
only the generic wire, with zero harness knowledge, so it needed no revision
to support this.

## Consequences

- **One process spawn per event** (Harness → hook-bridge → `uv run <hook>`),
  matching the cost ADR-0001 already accepted — no double-spawn, no announce
  protocol, no extra printing to stdout beyond the one JSON line each side
  already emits.
- hook-bridge remains the meaningful, harness-aware translator CONTEXT.md
  describes — not a thin exec-launcher — which is what keeps ADR-0001's
  "runner swappable for a compiled binary, no Hook changes" option open: the
  translation logic that would need porting still lives entirely in the
  runner.
- Codec selection is keyed by the **native payload's own event field**,
  not `hook.event` read via introspection. This is a deliberate, narrower
  reading of #8's "Hook-primary, not payload-primary" principle: the concern
  #8 raised was building a Context of the *wrong shape* from ambiguous
  payload dispatch; keying strictly on each harness's one-to-one native event
  name never risks that, and the Hook's own existing event check still
  catches a genuinely *misrouted* Hook (the wrong Hook wired to the wrong
  event) — just downstream rather than pre-spawn.
- Adding a harness or event only ever touches its Adapter module (`native_event`
  + its `Codec`s) — `cli.py` and `hook_process.py` are unchanged. The real
  claude-code and codex Adapters (#12) slot in exactly like the `stub`
  Adapter built to prove this ticket.
