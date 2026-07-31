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
The API a Hook is written against — the generic Context it receives and the Verdict it returns. Its normalized concepts let Hooks remain Harness-agnostic in most cases; clearly identified native data may enrich decisions when a Hook deliberately accepts reduced portability. The heart of the framework.
_Avoid_: Interface, schema, protocol (reserve "protocol" for the harness-native side)

**Native data**:
Harness-specific source data preserved by the Bridge and paired with a formal Harness discriminator supplied by the Adapter. On a Tool, Native data faithfully preserves the Harness's view of that Tool at the observed hook event, including terminal-event data when present; it cannot recover hidden original execution intent. A Hook may inspect Native data when it needs information outside the portable Contract, deliberately accepting that this logic may not work with another Harness.
_Avoid_: Raw data, generic data

**Context**:
The generic, harness-agnostic representation of a hook event that a Hook receives as input.
_Avoid_: Input, payload, event data

**Tool**:
The Contract envelope describing the Tool as observed at one hook event. It always preserves that event's Native data and may also carry a Tool projection; a Tool observed at one lifecycle moment is not guaranteed to equal a Tool observed at another.

**Tool projection**:
An optional, normalized view of a Tool expressed only in Harness-independent concepts. Hooks use Tool projections for portable decisions; absence means hook-bridge cannot faithfully project that Tool into a supported shared model. A projection may be emitted by only one Harness: portability guarantees stable meaning when present, not availability from every Harness.
_Avoid_: Normalized tool, generic tool

**Terminal observation**:
The discriminated `ToolResult | ToolError` value delivered to a `tool.after` Hook after a Harness reports the end of a tool attempt. The Adapter coalesces each Harness's native normal and failure paths into these two portable cases.

**ToolResult**:
A Terminal observation returned through the Harness's normal result path, carrying the Harness-exposed response as a JSON value. ToolResult does not promise that the Tool succeeded when the Harness provides no authoritative success status.

**ToolError**:
A Terminal observation carrying the Harness-exposed error as a JSON value, authoritatively classified as erroneous by the Harness or deterministically derived from its documented semantics. Adapters never create ToolErrors from assumptions or heuristics.

**Verdict**:
The generic, harness-agnostic response a Hook returns (e.g. allow / deny / modify), which hook-bridge translates into the Harness's native response.
_Avoid_: Result, output, decision, response

**Adapter**:
The harness-specific component inside hook-bridge that translates one Harness's native protocol to and from the generic Contract. One Adapter per Harness.
_Avoid_: Driver, plugin, connector
