# hook-bridge-runner

The runner: the CLI a Harness actually invokes. It sits between a Harness and a
Hook, translating the Harness's native hook protocol to and from the generic
Contract a Hook is written against.

```
hook-bridge-runner --harness <harness> <hook>
```

- Reads the harness's native event JSON from stdin.
- Peeks its native event name and selects the `Codec` registered for
  `(harness, native event)`.
- `decode`s it into the generic wire Context JSON and spawns the Hook
  (`uv run <hook>`), writing that JSON to its stdin — exactly what the SDK's
  `hook.run()` already reads.
- Reads the generic wire Verdict JSON the Hook printed to stdout, `encode`s it
  into the harness's native response body + exit code, and writes both back.

## Adapters

Two real harness Adapters ship today, both proven end-to-end against a live
`command-policy` example hook run through this runner:

- **claude-code** — `--harness claude-code`. Handles `PreToolUse`, normalises
  the `Bash` tool to the generic `shell` kind, and encodes Verdicts via
  `hookSpecificOutput.permissionDecision` (`allow`/`deny`/`ask`; `defer` emits
  nothing so claude-code's own permission flow decides). Also handles
  `PostToolUse` (`tool.after`): `pass_` emits nothing, `block` maps to
  `decision: "block"` + `reason`, `annotate` maps to
  `hookSpecificOutput.additionalContext`.
- **codex** — `--harness codex`. Same `PreToolUse`/`PostToolUse` shapes and
  encoding as claude-code, with one required extra field: codex's own output
  JSON Schema marks `hookSpecificOutput.hookEventName` as required, so the
  codex Codec always includes it (omitting it makes codex silently discard
  the decision and let the command through). **Known gaps:** codex parses
  `ask` but does not yet act on it — a Hook returning `ask()` blocks on
  claude-code but runs unconfirmed on codex. For `PostToolUse`, codex's exact
  `tool_response` shape for a Bash result isn't precisely documented; the
  codex Codec assumes the same `{text, exitCode}` shape claude-code
  documents, pending live verification.

A `stub` Adapter also ships; it exists only to exercise the CLI/IO plumbing in
tests and is not a real harness.

Adding a harness or event only ever touches its own Adapter module —
`cli.py` is unchanged.

Dependency-free by design — the runner works in plain JSON-shaped dicts,
never the SDK's typed `Context`/`Verdict`.

See the [root README](../../README.md) for a worked example of wiring a Hook
into claude-code's `settings.json` or codex's `config.toml`.
