# hook-bridge

A framework that decouples agent-harness hook logic from the harness that invokes it. Hooks are authored once against a generic contract; `hook-bridge` translates each harness's native hook protocol to and from that contract, so one hook runs on many harnesses and can be tested with no harness present.

## Language

**Harness**:
An agent host that fires hook events and expects hook responses in its own native protocol — e.g. claude-code, codex.
_Avoid_: Agent, host, tool, client

**Hook**:
User-authored logic that reacts to a harness event and returns a Verdict. Written once against the generic Contract, ignorant of which Harness invoked it.
_Avoid_: Plugin, handler, script

**hook-bridge**:
The CLI that sits between a Harness and a Hook: it converts a Harness's native event into generic Context, invokes the Hook, and converts the Hook's Verdict back into the Harness's native response. Published on PyPI as `hook-bridge-runner`; invoked as `hook-bridge-runner --harness <harness> <hook>`.

**Contract**:
The harness-agnostic API a Hook is written against — the generic Context it receives and the Verdict it returns. The heart of the framework.
_Avoid_: Interface, schema, protocol (reserve "protocol" for the harness-native side)

**Context**:
The generic, harness-agnostic representation of a hook event that a Hook receives as input.
_Avoid_: Input, payload, event data

**Verdict**:
The generic, harness-agnostic response a Hook returns (e.g. allow / deny / modify), which hook-bridge translates into the Harness's native response.
_Avoid_: Result, output, decision, response

**Adapter**:
The harness-specific component inside hook-bridge that translates one Harness's native protocol to and from the generic Contract. One Adapter per Harness.
_Avoid_: Driver, plugin, connector
