# hook-bridge

A framework that decouples agent-harness hook logic from the harness that
invokes it. Write a Hook once against a generic Contract; `hook-bridge`
translates each harness's native hook protocol to and from that contract, so
the same Hook file runs unchanged on multiple harnesses and can be tested
with no harness present at all.

Today it supports two harnesses — [claude-code](https://code.claude.com/docs/en/hooks.md)
and [codex](https://developers.openai.com/codex/hooks) — for two events:
`tool.before` (block/allow/ask a tool call before it runs, e.g. a shell
command) and `tool.after` (block further processing or annotate once a tool
call has already run).

A few terms recur throughout this repo: a **Harness** is the agent host that
fires hook events (claude-code, codex); a **Hook** is the user-authored logic
that reacts to one; the **Contract** is the harness-agnostic API a Hook is
written against (the generic **Context** it receives, the generic **Verdict**
it returns); and an **Adapter** is the harness-specific piece inside
hook-bridge that translates one Harness's native protocol to and from the
Contract.

## Two packages

| Package | What it is | Published as |
|---|---|---|
| [`hook-bridge-sdk`](packages/hook-bridge-sdk/) | The authoring SDK. What you import when *writing* a Hook: `@hook`, `allow()`/`deny()`/`ask()`/`defer()` for `tool.before`, `pass_()`/`block()`/`annotate()` for `tool.after`, the typed `Context`/`Verdict`. Dependency-free, harness-ignorant. | [PyPI](https://pypi.org/project/hook-bridge-sdk/) — a Hook declares it inline via [PEP 723](https://peps.python.org/pep-0723/), so you never `pip install` it yourself. |
| [`hook-bridge-runner`](packages/hook-bridge/) | The CLI a harness actually invokes. Translates the harness's native event JSON to the SDK's generic wire format, spawns the Hook, and translates its Verdict back. | [PyPI](https://pypi.org/project/hook-bridge-runner/) (`hook-bridge-runner`), or via the [Homebrew tap](https://github.com/jamessawle/homebrew-tap). |

A Hook only ever depends on `hook-bridge-sdk`. `hook-bridge-runner` has no
dependency on the SDK — it works in plain JSON, never the SDK's typed
objects — so it can be swapped for a different implementation without
touching a single Hook.

## Install the runner

```
brew install jamessawle/tap/hook-bridge-runner
```

or, without Homebrew:

```
uv tool install hook-bridge-runner
```

Either way you also need [`uv`](https://docs.astral.sh/uv/) on `PATH` — the
runner invokes each Hook as `uv run <hook>`, which is what lets a Hook declare
its own `hook-bridge-sdk` dependency inline and run with no separate install
step.

## Write a Hook

See [`packages/hook-bridge-sdk/`](packages/hook-bridge-sdk/) for the
authoring SDK and a minimal worked example, or [`examples/`](examples/) for
fuller, harness-free-tested Hooks you can copy.

## Wire it into a harness

`hook-bridge-runner` is what each harness actually spawns; it in turn spawns
your Hook. Point it at your Hook file with `--harness <claude-code|codex>`.

Wire a Hook to `PreToolUse` for `tool.before`, or `PostToolUse` for
`tool.after` — same `hook-bridge-runner` invocation either way, since the
runner reads the Hook's event straight off the native payload (ADR-0003).

### claude-code

In `.claude/settings.json` (or `~/.claude/settings.json`):

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "hook-bridge-runner --harness claude-code /path/to/guard.py"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "hook-bridge-runner --harness claude-code /path/to/audit.py"
          }
        ]
      }
    ]
  }
}
```

### codex

In `.codex/config.toml` (or `~/.codex/config.toml`):

```toml
[[hooks.PreToolUse]]
matcher = "^Bash$"

[[hooks.PreToolUse.hooks]]
type = "command"
command = "hook-bridge-runner --harness codex /path/to/guard.py"

[[hooks.PostToolUse]]
matcher = "^Bash$"

[[hooks.PostToolUse.hooks]]
type = "command"
command = "hook-bridge-runner --harness codex /path/to/audit.py"
```

Codex gates hook execution behind trust review (`/hooks`) and the
`[features] hooks = true` flag — see codex's own docs if the hook doesn't
appear to run.

## Harness parity — known gaps

`allow`/`deny` behave identically on both harnesses; `ask` currently does
not — see [`packages/hook-bridge/`](packages/hook-bridge/) for the adapter
details and the gap. For `tool.after`, codex's exact `tool_response` shape
for a Bash result isn't precisely documented; the codex Adapter assumes the
same `{text, exitCode}` shape claude-code documents, pending live
verification (see `adapters/codex.py`). Output-rewrite (redacting/replacing
a tool's result) is an unbuilt seam on both harnesses — see ADR-0004.

## Repo layout

```
packages/hook-bridge-sdk/   the authoring SDK (write Hooks against this)
packages/hook-bridge/       the runner CLI (hook-bridge-runner)
examples/                   runnable, harness-free-tested example Hooks
docs/adr/                   architecture decision records
```
