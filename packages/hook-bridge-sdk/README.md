# hook-bridge-sdk

The thin typed authoring SDK for [hook-bridge](../../README.md) Hooks.

Write a Hook once against the generic **Contract** — the harness-agnostic
`Context` it receives and the `Verdict` it returns — and test it in-process with
no harness present. `hook-bridge` (the runner, a separate package) adapts each
harness's native protocol to and from this Contract.

Each Contract `Tool` always carries lossless, Harness-discriminated Native data
and may also carry a Harness-independent typed projection. A projection type's
meaning and required shape follow the SDK compatibility policy; changing either
is a breaking Contract change. Its availability does not: projections are
best-effort runtime capabilities, so Hook code must handle `projection is None`
even for a tool that has projected successfully before.

Adapters tolerate unknown extra Native fields, but suppress a projection when
any required field is missing, changed, or ambiguous rather than guessing or
rejecting the Tool. Inspect `tool.native` when a projection is unavailable or
when a Hook deliberately needs Harness-specific information; Native data is
always preserved as the lossless fallback.

```python
# /// script
# dependencies = ["hook-bridge-sdk"]
# ///
from hook_bridge import hook, allow, deny, defer, ToolBeforeContext, ToolBeforeVerdict


@hook
def guard(ctx: ToolBeforeContext) -> ToolBeforeVerdict:  # pure logic, no IO
    if ctx.tool.kind != "shell":
        return defer()
    if "rm -rf /" in ctx.tool.command:
        return deny("that would delete everything")
    return allow()


if __name__ == "__main__":  # runnable as a subprocess AND importable in tests
    guard.run()
```

Harness-free test:

```python
from hook_bridge import tool_before, shell
from guard import guard

def test_denies_rm_rf() -> None:
    assert guard.dispatch(tool_before(shell("rm -rf /"))).is_deny
```

Runnable examples live in [`../../examples/`](../../examples/).

## Surface

- `@hook` decorator → `Hook[C, V]` with `.dispatch(ctx)` (pure test seam) and
  `.run()` (stdin JSON → dispatch → stdout JSON; exit code = health only).
- `run(*hooks)` to compose several events in one file (dispatch by `ctx.event`).
- `tool.before` Verdict helpers: `allow()`, `deny(reason)`, `ask(reason)`,
  `defer()`.
- `tool.after` Verdict helpers: `pass_()`, `block(message)`,
  `annotate(message)` (distinct from `tool.before`'s verbs, since the tool has
  already run by the time this event fires).
- Contract types: `ToolBeforeContext` (`.tool` discriminated on `.kind`; `shell`
  → `.command`) and `ToolBeforeVerdict` (`is_allow` / `is_deny` / `is_ask` /
  `is_defer` / `reason`); `ToolAfterContext` (adds `.result` — `.text` /
  `.exit_code`) and `ToolAfterVerdict` (`is_pass` / `is_block` /
  `is_annotate` / `message`).
- Boundary schema validation on the Context read and Verdict written
  (`BoundaryError`).
- Testing factories: `tool_before`, `tool_after`, `shell`, `result`.
