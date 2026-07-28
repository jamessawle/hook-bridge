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
- **codex** — `--harness codex`. Handles `PreToolUse` input and faithfully
  encodes `deny`/`defer`. Codex rejects `permissionDecision: "allow"` without
  an input rewrite, so the Codec maps `allow` to empty output: the hook passes,
  but Codex's normal permission flow still applies. Codex rejects `ask`, so
  the Codec maps it to empty output too. Every generic Verdict therefore has
  valid Codex output, but `ask` cannot guarantee confirmation: Codex prompts
  only when its normal permission policy requires it. Native `PostToolUse` is
  still unsupported: its Bash `tool_response` is an output string with no exit
  status, so it cannot faithfully populate the generic `ToolResult`.

A `stub` Adapter also ships; it exists only to exercise the CLI/IO plumbing in
tests and is not a real harness.

Adding a harness or event only ever touches its own Adapter module —
`cli.py` is unchanged.

Dependency-free by design — the runner works in plain JSON-shaped dicts,
never the SDK's typed `Context`/`Verdict`.

See the [root README](../../README.md) for a worked example of wiring a Hook
into claude-code's `settings.json` or codex's `config.toml`.
