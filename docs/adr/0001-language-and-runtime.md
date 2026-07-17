# ADR-0001: Language & runtime for hook-bridge

- **Status**: Accepted
- **Date**: 2026-07-17
- **Resolves**: [Decide: language & runtime for hook-bridge](https://github.com/jamessawle/hook-bridge/issues/4)

## Context

hook-bridge decouples a Hook from the Harness that invokes it: a Hook is authored
once against a generic Contract, and hook-bridge adapts each Harness's native
protocol to and from that Contract (see [CONTEXT.md](../../CONTEXT.md)). Two
questions had to be locked before any code: how hook-bridge **invokes** a Hook,
and what **language/runtime** the runner and Hooks use.

The reference Hook, `git-guard`, is ~200 lines of **Python**: quote-aware
tokenising (`shlex`), regex flag-matching, and a shell-out to `git` to resolve the
current branch. Today claude-code invokes it as a subprocess — event JSON on
stdin, Verdict on stdout/exit code — and its tests drive it the same way, which is
already a harness-free test through a process boundary.

The stated priority is **DevX** across three axes: developing a Hook (including
pulling in third-party packages), distributing the framework (including inside a
plugin), and triggering the Hook from a Harness.

## Decision

**Invocation model — subprocess.** hook-bridge spawns the Hook as a separate
process, passing the generic Context as JSON on stdin and reading the Verdict from
stdout / exit code. The Contract is a **language-neutral wire format**.

This is augmented by two things that address the wire boundary's weakness
(stringly-typed data crossing a process edge):

- A **thin typed authoring SDK** per language (v1: Python) that parses Context into
  a typed object and serialises the Verdict, so authors never hand-roll JSON. This
  is the useful half of an AWS-Powertools-style wrapper **without** a compile step
  — the Hook still ships as source.
- **Schema validation at the boundary**: the runner validates the Context it emits
  and the Verdict it reads against the Contract, failing loudly rather than passing
  garbage through.

**Hook language (v1) — Python**, with the wire Contract defined language-neutrally
so additional languages are additive (a new SDK) rather than a rewrite.

**Runner language (v1) — Python**, in a **single-language monorepo** (a `uv`
workspace) holding the runner, the SDK, and the shared Contract types as a single
source of truth.

**Runtime — Python 3.12 floor, managed with `uv`.** Distributed as
`uvx hook-bridge` / `pipx install hook-bridge`; triggered from a Harness config as
e.g. `uvx hook-bridge --harness claude-code ./git-guard.py`.

## Consequences

- The tracer bullet stays a **port**, not a reimplementation: git-guard keeps its
  Python logic (`shlex`/`re`/`subprocess`), changing only which JSON shape it reads
  and writes. Its `3.7` version guard is dropped.
- Portability and harness-free testability — the two proof-points — become nearly
  free: portability is "adapt two native shapes to one wire Contract," and
  harness-free testing is essentially what the existing tests already do.
- Hooks pull in third-party packages natively (`pip`/`uv`), because a Hook is just
  an ordinary program in its language. (This is what ruled out an embedded Lua VM,
  where packages are painful, and a same-language compiled-library model, where the
  Hook becomes a build artifact.)
- One shared Contract definition lives in the monorepo — the runner validates
  against it and the SDK types against it — avoiding schema drift across languages.
- **Cost accepted**: one extra process spawn per event (Harness → hook-bridge →
  Hook) over today's single hop; negligible given git-guard already shells out to
  `git`. And distribution assumes Python is present — a non-constraint for a
  Python-Hook tracer, since the Hook needs Python regardless.
- **Kept open**: because the seam is a wire Contract, the runner can later be
  swapped for a compiled binary (Go/Rust) with **no change to any Hook** — a clean
  follow-on effort, not a rewrite.
