# ADR-0002: `tool.before` Verdict — four verbs, not two

- **Status**: Accepted
- **Date**: 2026-07-18
- **Amends**: the v1 slice locked by [Design: the generic hook Contract](https://github.com/jamessawle/hook-bridge/issues/5)
- **Surfaced by**: [Build: SDK + validate against a complex hook](https://github.com/jamessawle/hook-bridge/issues/9)

## Context

Issue #5 locked the v1 `tool.before` Verdict as two verbs — `allow()` and
`deny(reason)` — with `ask` and `modify` noted as documented-but-unbuilt seams.
That slice was sized against a toy hook ("deny force-push-to-protected, allow
everything else").

To pressure-test the authoring SDK against genuine complexity, #9 ported a real
hook (`git-guard`) against the Contract. A realistic guard has **four**
irreducible outcomes, not two:

- **deny** — a hard block (e.g. a forbidden action), with a reason.
- **ask** — proceed only after confirmation (e.g. a history-rewriting action).
- **allow** — auto-approve a vouched-for command.
- **defer** — express no opinion; let the harness's normal permission flow decide
  (e.g. an unrecognised command).

Collapsing four outcomes onto two verbs is lossy, and the lossy directions are
**unsafe**. Mapping `ask → allow` auto-approves the very actions that warranted a
prompt. Mapping `defer → allow` auto-approves unrecognised commands a guard
deliberately never vouches for. A guard that cannot say "ask" or "abstain" is a
weaker guard — so the two-verb slice was under-sized.

## Decision

The v1 `tool.before` Verdict has **four verbs**: `allow()`, `deny(reason)`,
`ask(reason)`, `defer()`.

- `deny` and `ask` carry a **mandatory reason**; `allow` and `defer` carry none.
- `defer` is distinct from `allow`: "no opinion" is not "approve".
- `modify` (updated tool input) **stays an unbuilt seam** — no realistic hook in
  scope needs it, and building it would require defining generic per-tool-kind
  "updated input" now for no benefit.

These are additive members of a per-event discriminated union, so the
extensibility model from #5 is unchanged.

## Consequences

- The four verbs are the durable outcome vocabulary a Hook author writes against.
- Mapping each generic verb onto a harness's native protocol is the **Adapter's**
  job (#8), and remains deferred to the runner/CLI work.
- **Amends #5**: `modify` is now the only unbuilt `ToolBeforeVerdict` seam.
- `git-guard` itself was a **validation probe**, not a shipped artifact — it
  proved the SDK holds up under real complexity and surfaced this decision, then
  was set aside. The repo ships the SDK plus illustrative examples (see
  [`examples/`](../../examples/)), not maintained hooks.
