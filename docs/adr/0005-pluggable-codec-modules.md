# ADR-0005: Codecs are self-describing modules composed explicitly per Harness

- **Status**: Accepted
- **Date**: 2026-07-28
- **Builds on**: ADR-0003 (runner process boundary and Codec selection)

## Context

ADR-0003 established one `Codec` per `(Harness, native event)` cell, but the
initial implementation placed every Codec for a Harness in one Adapter module.
That was adequate for the first event. Once claude-code supported both
`PreToolUse` and `PostToolUse`, adding or changing one Codec required editing
an accumulating Harness-sized implementation and test file.

The Codec seam is real: several Harnesses and events now vary independently.
The physical module structure should preserve that independence so a Codec's
translation, identity, and tests remain local.

Two loading models were considered:

1. Dynamically discover every module in an Adapter package.
2. Have each Codec describe itself and compose the built-in Codecs explicitly.

Dynamic discovery would remove one registration line, but make supported
events, import failures, packaging, and type checking less explicit. Built-in
Codecs are released together with the runner, so runtime discovery provides no
current user capability.

## Decision

**Each `(Harness, native event)` Codec lives in its own module, declares its
`native_event` and `contract_event`, and is explicitly composed into its
Harness Adapter.**

Each Harness is a package:

```text
adapters/
  claude_code/
    adapter.py
    common.py
    tool_before.py
    tool_after.py
  codex/
    adapter.py
    tool_before.py
```

The `Codec` interface contains two identity fields and the existing pure
translation pair:

```python
class Codec(Protocol):
    native_event: str
    contract_event: str

    def decode(self, raw: dict[str, Any]) -> dict[str, Any]: ...
    def encode(self, verdict: dict[str, Any]) -> tuple[dict[str, Any], int]: ...
```

`HarnessAdapter` accepts a native-event reader and an iterable of Codecs,
validates their registration, builds the private lookup map, and exposes one
selection method:

```python
codec = adapter.codec_for(raw)
```

The runner no longer reads `adapter.codecs` or separately calls
`adapter.native_event`; those are Adapter implementation details.

## Consequences

- Changing a Codec edits its module and its interface tests.
- Adding Harness support for an existing Contract event adds one Codec module,
  one explicit composition entry, and its tests. Existing Codec modules remain
  unchanged.
- Duplicate native-event registrations and missing event metadata fail during
  Adapter construction.
- Shared native decoding may live in a Harness-private module once at least
  two of that Harness's Codecs use it.
- Adding a new Contract event still changes the SDK Contract and needs one new
  Codec per supporting Harness. This decision localises those cells; it does
  not pretend that a public Contract change is runner-only.
- Third-party Codec discovery is not implemented. If external packages need to
  provide Codecs later, Python package entry points should be evaluated as a
  separate public extension seam.
