# ADR-0004: Verdict verbs are scoped per event, reused only when semantics match

- **Status**: Accepted
- **Date**: 2026-07-24
- **Resolves**: [Support PostToolUse ("tool.after")](https://github.com/jamessawle/hook-bridge/issues/25)
- **Builds on**: ADR-0002 (`tool.before`'s four verbs), ADR-0003 (runner process boundary)

## Context

#25 asks for a second Contract event: `tool.after`, the generic form of
claude-code's and codex's native `PostToolUse`. Both harnesses fire it once a
tool call has already run, carrying the tool's result (`tool_response`) in
addition to the same `tool_name`/`tool_input`/`session_id`/`cwd` fields
`tool.before` already normalises. Confirmed against both harnesses' current
docs (code.claude.com/docs/en/hooks, learn.chatgpt.com/docs/hooks):

- Neither harness can undo a tool call from `PostToolUse` — the side effect
  already happened. `tool.before`'s Verdict (`allow`/`deny`/`ask`/`defer`) is
  entirely pre-execution permission vocabulary; none of it has a coherent
  meaning after the fact.
- Both harnesses do support the same two post-hoc levers instead: stopping
  further processing with a reason, and injecting context without stopping.
- Only claude-code documents rewriting the tool's own result
  (`updatedToolOutput`); codex's documented output shape has no equivalent.
  A hook that wants to redact or transform output (#25's motivating example)
  has no shared, faithful mapping across both harnesses today.

`tool.after` is the second event the Contract has ever needed. That makes it
the first real test of a question ADR-0002 left implicit: when a new event
arrives, does its Verdict reuse the vocabulary of events that came before it,
invent its own from scratch, or something in between? Getting this wrong in
either direction has a cost — reusing `deny` for `tool.after` would silently
imply a pre-execution control that no longer exists; inventing a wholly
separate vocabulary per event (or worse, per tool kind within an event) would
turn the Contract into an unbounded pile of near-duplicate verbs with no
shared mental model.

## Decision

**A Verdict's verbs are scoped to its event, sized to what that event can
actually do — a verb name is reused across events only when the semantics
genuinely coincide, and is never duplicated per tool kind within one event.**

Applied to `tool.after`:

1. It gets its **own** Verdict type, distinct from `ToolBeforeVerdict`. None
   of `allow`/`deny`/`ask`/`defer` survive the trip, because none of them
   describes a real post-execution lever — the new verbs (`pass_`/`block`/
   `annotate`; see `contract.py`) name the two levers both harnesses actually
   expose plus a no-opinion case. `ToolAfterContext` carries the tool's
   result alongside `Tool`, since that result is `tool.after`'s whole reason
   to exist.
2. Like `tool.before`, `tool.after`'s Verdict is **one type shared by every
   tool kind** in that event (today, just `shell`) — not a per-kind verb set.
   A future `file_edit` tool kind reasons about the same `pass_`/`block`/
   `annotate` outcomes as `shell`; it does not get its own `deny`.
3. Output-rewrite is a documented, **unbuilt seam** for v1, the same
   treatment ADR-0002 gave `tool.before`'s `modify`: shipping it now would
   give claude-code a faithful mapping and codex none, the lossy outcome
   ADR-0002 already ruled out.

## Consequences

- `ToolAfterVerdict` is a distinct member of the Verdict union, so a Hook
  written for `tool.after` cannot return a `tool.before` verdict by
  construction — the same event/verdict pairing safety `tool.before` already
  has.
- Future events follow the same test before adding or reusing a verb: does
  this outcome mean the same thing here as it did there? `tool.before`'s
  `allow`/`deny`/`ask`/`defer` and `tool.after`'s `pass_`/`block`/`annotate`
  are the durable precedent, not a one-off for either event.
- Mapping each event's Verdict onto a harness's native response is still the
  Adapter's job (#8/#12), unchanged by this ADR.
- Output rewrite stays out of scope until a harness-parity story exists for
  it (or a hook author's real need forces the question, the way #9's
  `git-guard` forced ADR-0002's four verbs).
