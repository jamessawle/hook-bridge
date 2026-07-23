# hook-bridge-sdk

The thin typed authoring SDK for [hook-bridge](../../README.md) Hooks.

Write a Hook once against the generic **Contract** — the harness-agnostic
`Context` it receives and the `Verdict` it returns — and test it in-process with
no harness present. `hook-bridge` (the runner, a separate package) adapts each
harness's native protocol to and from this Contract.

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
- Verdict helpers: `allow()`, `deny(reason)`, `ask(reason)`, `defer()`.
- Contract types: `ToolBeforeContext` (`.tool` discriminated on `.kind`; `shell`
  → `.command`) and `ToolBeforeVerdict` (`is_allow` / `is_deny` / `is_ask` /
  `is_defer` / `reason`).
- Boundary schema validation on the Context read and Verdict written
  (`BoundaryError`).
- Testing factories: `tool_before`, `shell`.
