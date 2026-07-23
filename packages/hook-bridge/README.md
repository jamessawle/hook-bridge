# hook-bridge

The runner: the CLI a Harness actually invokes. It sits between a Harness and a
Hook — see [CONTEXT.md](../../CONTEXT.md) and
[ADR-0003](../../docs/adr/0003-runner-process-boundary.md) for how bytes cross
the process edge.

```
hook-bridge --harness <harness> <hook>
```

- Reads the harness's native event JSON from stdin.
- Peeks its native event name and selects the `Codec` registered for
  `(harness, native event)`.
- `decode`s it into the generic wire Context JSON and spawns the Hook
  (`uv run <hook>`), writing that JSON to its stdin — exactly what the SDK's
  `hook.run()` already reads.
- Reads the generic wire Verdict JSON the Hook printed to stdout, `encode`s it
  into the harness's native response body + exit code, and writes both back.

v1 ships only the `stub` harness Adapter, which exists to prove this plumbing
end-to-end. The real claude-code and codex Adapters are sibling work (#12).

Dependency-free by design (#7: no runner→SDK dependency) — the runner works in
plain JSON-shaped dicts, never the SDK's typed `Context`/`Verdict`.
