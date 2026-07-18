# Examples

hook-bridge is a framework for **building** hooks — the product is the SDK (and,
later, the runner), not the hooks themselves. These examples exist to show how to
author and test a Hook against the generic [Contract](../CONTEXT.md); they are
**illustrative, not maintained policies**. Their rules are deliberately synthetic
(small static tables, no real CLI parsing), so nothing here rots as an underlying
tool evolves. Copy one as a starting point and replace its logic with your own.

| Example | Shows |
|---|---|
| [`deny-list/`](deny-list/) | The minimum: one `@hook`, one rule, two outcomes (`allow` / `deny`). |
| [`command-policy/`](command-policy/) | The full `tool.before` Verdict surface — `allow` / `deny` / `ask` / `defer` — with logic split into helpers. |

Each example is a [PEP 723](https://peps.python.org/pep-0723/) script: it declares
`hook-bridge-sdk` inline and runs as a subprocess (`uv run ./<example>.py`), and
its `test_*.py` imports the Hook and drives `dispatch(...)` directly — the
harness-free testing story the SDK exists to enable.

> A more complex, real-world Hook (`git-guard`, with quote-aware tokenising and
> git shell-outs) was ported against the SDK during development to prove the
> authoring surface holds up under genuine complexity. That was a validation
> probe, not a shipped artifact — exactly the kind of evolving logic these
> examples avoid baking in. See [ADR-0002](../docs/adr/0002-tool-before-verdict-verbs.md).
