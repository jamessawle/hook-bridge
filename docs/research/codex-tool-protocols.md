# Codex tool hook protocols

Research completed 28 July 2026 for
[Inventory Codex tool hook protocols](https://github.com/jamessawle/hook-bridge/issues/38).

## Question

Using primary sources, what native tool names and exact input and result shapes
can Codex expose through `PreToolUse` and `PostToolUse`, including shell,
`apply_patch`, local-function, and MCP tools? Which facts are documented
guarantees, which are observations or unstable implementation details, and
which information cannot be normalized faithfully?

## Source boundary

The [official Hooks guide](https://learn.chatgpt.com/docs/hooks) is the release
behavior reference. It explicitly says that generated schemas on `main` can
contain unreleased fields, so source observations below use the latest released
Codex version at the time of research,
[`rust-v0.145.0`](https://github.com/openai/codex/releases/tag/rust-v0.145.0),
at commit
[`25af12f`](https://github.com/openai/codex/tree/25af12f7e61572b0bc18ddb1008be543b91519b0).
Those observations describe that release, not a promise that future releases
will retain the same tool-specific encodings.

## Answer in brief

Codex does **not** expose a closed, exhaustively typed inventory of tools.
It exposes one stable hook envelope containing a canonical `tool_name`, an
arbitrary JSON `tool_input`, and, after execution, an arbitrary JSON
`tool_response`. The Hooks guide only gives a fixed inner shape to shell and
`apply_patch` input: `{"command": string}`. MCP and other local-function inputs
are their arguments; results are explicitly tool-specific. The official
coverage table also says hosted tools are absent and specialized local paths
may opt out, so hooks are not a complete enforcement boundary
([tool coverage](https://learn.chatgpt.com/docs/hooks#tool-coverage)).

Therefore a faithful bridge needs to preserve the emitted name and opaque JSON
values. A normalized shell command, text output, or error flag can be an
optional projection, but cannot replace those raw fields without losing
information.

## Documented wire contract

Every command hook receives the common fields `session_id: string`,
`transcript_path: string | null`, `cwd: string`, `hook_event_name: string`, and
the Codex extension `model: string`. Tool hooks additionally receive
`permission_mode`, whose documented values are `default`, `acceptEdits`,
`plan`, `dontAsk`, and `bypassPermissions`; turn-scoped hooks also receive the
Codex extension `turn_id`
([common input fields](https://learn.chatgpt.com/docs/hooks#common-input-fields)).
The transcript itself is explicitly not a stable hook interface.

`PreToolUse` adds:

```json
{
  "hook_event_name": "PreToolUse",
  "tool_name": "string",
  "tool_use_id": "string",
  "tool_input": "<any JSON value>"
}
```

`PostToolUse` adds the same fields and:

```json
{
  "hook_event_name": "PostToolUse",
  "tool_response": "<any JSON value>"
}
```

The guide defines `tool_input` and `tool_response` as tool-specific JSON values,
not objects with a common nested schema
([`PreToolUse`](https://learn.chatgpt.com/docs/hooks#pretooluse),
[`PostToolUse`](https://learn.chatgpt.com/docs/hooks#posttooluse)).
The released generated schemas likewise accept any JSON at those properties,
require the documented common and event fields, reject unknown top-level
properties, and additionally allow optional `agent_id` and `agent_type`
([pre schema](https://github.com/openai/codex/blob/25af12f7e61572b0bc18ddb1008be543b91519b0/codex-rs/hooks/schema/generated/pre-tool-use.command.input.schema.json#L1-L70),
[post schema](https://github.com/openai/codex/blob/25af12f7e61572b0bc18ddb1008be543b91519b0/codex-rs/hooks/schema/generated/post-tool-use.command.input.schema.json#L1-L72)).
Because the Hooks guide does not document the two agent fields, consumers
should treat them as optional Codex extensions rather than required portable
data.

## Tool identity and payload matrix

| Tool path | Canonical hook `tool_name` | `tool_input` | `tool_response` |
| --- | --- | --- | --- |
| shell, including `shell_command` | `Bash` | `{"command": string}` | tool-specific JSON; released implementation emits a string |
| unified exec `exec_command` | `Bash` | `{"command": string}` | released implementation emits a string after the original process completes |
| `write_stdin` | no independent `PreToolUse`; may finish the original `Bash` call | n/a as a separate hook call | delivered as the original command's `PostToolUse` |
| `apply_patch` | `apply_patch` | `{"command": string}` where the string is the patch | released implementation emits a string |
| MCP tool | e.g. `mcp__filesystem__read_file` | the MCP arguments JSON | the MCP call result JSON |
| other local function | function tool name, e.g. `update_plan` | the function arguments JSON | normally the model-facing result, but handler-specific |
| hosted tool, e.g. `WebSearch` | not exposed | not exposed | not exposed |

The names and coverage in this table are documented, including the fact that
`apply_patch` also matches the aliases `Edit` and `Write`, and `spawn_agent`
also matches `Agent`. Those aliases select hooks; they are not serialized as
`tool_name`
([matcher patterns](https://learn.chatgpt.com/docs/hooks#matcher-patterns),
[tool coverage](https://learn.chatgpt.com/docs/hooks#tool-coverage)).
The released implementation keeps canonical payload names and aliases separate:
the serialized values remain `Bash`, `apply_patch`, and `spawn_agent`
([source](https://github.com/openai/codex/blob/25af12f7e61572b0bc18ddb1008be543b91519b0/codex-rs/core/src/tools/hook_names.rs#L28-L65)).

This is a naming rule, not an exhaustive list of built-ins. Local functions,
extension tools, dynamic tools, enabled MCP servers, feature flags, and the
active model can change the available set. The only future-safe discriminator
provided by the hook is the emitted `tool_name` string.

## Shell and unified exec

### Documented guarantee

Both ordinary shell and unified `exec_command` calls are reported as `Bash`.
Their hook input is exactly the small projection:

```json
{"command": "the command string"}
```

A `write_stdin` call does not run `PreToolUse` again; when it observes the
process finish, it can deliver the original command's `PostToolUse`
([tool coverage](https://learn.chatgpt.com/docs/hooks#tool-coverage)).
`PostToolUse` also runs for a supported Bash command that exits non-zero
([`PostToolUse`](https://learn.chatgpt.com/docs/hooks#posttooluse)).

### Released implementation observation

Both legacy shell and unified exec deliberately discard all hook-facing input
except the command string. In particular, unified exec converts its model
argument `cmd` to hook field `command`
([legacy shell source](https://github.com/openai/codex/blob/25af12f7e61572b0bc18ddb1008be543b91519b0/codex-rs/core/src/tools/handlers/shell/shell_command.rs#L249-L290),
[unified exec source](https://github.com/openai/codex/blob/25af12f7e61572b0bc18ddb1008be543b91519b0/codex-rs/core/src/tools/handlers/unified_exec/exec_command.rs#L408-L448)).

The released `tool_response` is a JSON string containing collected output,
subject to the model-output truncation policy. Although the internal exec
result has `wall_time`, `process_id`, `exit_code`, token count, and other
metadata, the hook response serializes only the truncated output string. A
running process emits no response yet, and a later completion reuses the
original event call id
([source](https://github.com/openai/codex/blob/25af12f7e61572b0bc18ddb1008be543b91519b0/codex-rs/core/src/tools/context.rs#L314-L373)).

### Fidelity limit

From these hooks alone it is impossible to recover the distinction between
legacy shell and `exec_command`, or the original unified-exec fields such as
working directory, shell/login mode, TTY mode, timeout/yield limit, requested
permissions, or approval justification. `PostToolUse` tells a consumer that a
command completed, including non-zero completion, but the released response
does not provide a structured exit status, duration, process id, or separate
stdout/stderr streams. Truncated bytes are also unrecoverable.

## `apply_patch`

### Documented guarantee

The canonical payload name is `apply_patch`, even if a matcher used `Edit` or
`Write`, and the input is:

```json
{"command": "*** Begin Patch\n..."}
```

The returned value is only documented as tool-specific JSON
([`PreToolUse`](https://learn.chatgpt.com/docs/hooks#pretooluse),
[`PostToolUse`](https://learn.chatgpt.com/docs/hooks#posttooluse)).

### Released implementation observation and fidelity limit

The released adapter sends the patch text in `command` and serializes the
provider-formatted tool output as a JSON string
([handler](https://github.com/openai/codex/blob/25af12f7e61572b0bc18ddb1008be543b91519b0/codex-rs/core/src/tools/handlers/apply_patch.rs#L503-L539),
[output type](https://github.com/openai/codex/blob/25af12f7e61572b0bc18ddb1008be543b91519b0/codex-rs/core/src/tools/context.rs#L242-L278)).
There is no structured list of changed files, operation kinds, hunks, or a
separate success/error field in the hook payload. A bridge may parse the text
as a release-specific convenience, but cannot treat that parse as a faithful
or stable protocol.

## Other local function tools

### Documented guarantee

Most local function tools report the function tool name, send their arguments
as `tool_input`, and normally send their model-facing output as
`tool_response`. Specialized paths can opt out, so even local-function coverage
is not guaranteed to be complete
([tool coverage](https://learn.chatgpt.com/docs/hooks#tool-coverage)).

### Released implementation observation

The default adapter uses the flattened function name. It parses a non-empty
argument string as JSON, maps an empty argument string to `{}`, and falls back
to a JSON string when parsing fails
([source](https://github.com/openai/codex/blob/25af12f7e61572b0bc18ddb1008be543b91519b0/codex-rs/core/src/tools/registry.rs#L723-L741)).

For results, a handler can supply any explicit JSON hook response. Otherwise
the adapter serializes only the body of the model-facing function result
([source](https://github.com/openai/codex/blob/25af12f7e61572b0bc18ddb1008be543b91519b0/codex-rs/core/src/tools/registry.rs#L72-L114)).
That fallback body is either a string or an array of tagged content items:
`input_text`, `input_image`, `input_audio`, or `encrypted_content`
([content item source](https://github.com/openai/codex/blob/25af12f7e61572b0bc18ddb1008be543b91519b0/codex-rs/protocol/src/models.rs#L1820-L1843),
[body serialization](https://github.com/openai/codex/blob/25af12f7e61572b0bc18ddb1008be543b91519b0/codex-rs/protocol/src/models.rs#L1900-L2000)).
The result's internal `success` metadata is intentionally not part of that
serialized body.

### Fidelity limit

There is no universal local-function result schema and no universal success
flag. A string response may be successful output or an error message; an
object/array may be a handler's explicit shape or model-facing content.
Flattened `tool_name` also does not expose a separate tool kind or namespace.
A bridge must keep both the name and JSON value opaque unless it has a
versioned, tool-specific decoder.

## MCP tools

### Documented guarantee

MCP tools use a name such as `mcp__filesystem__read_file`; `tool_input` is the
MCP arguments and `tool_response` is the MCP call result
([`PreToolUse`](https://learn.chatgpt.com/docs/hooks#pretooluse),
[`PostToolUse`](https://learn.chatgpt.com/docs/hooks#posttooluse)).
The guide does not promise a finite catalog of names or a more specific
result schema.

### Released implementation observation

The release constructs a hook name by adding `mcp__` when needed and joining
the callable namespace and tool name with `__`
([source](https://github.com/openai/codex/blob/25af12f7e61572b0bc18ddb1008be543b91519b0/codex-rs/core/src/tools/handlers/mcp.rs#L29-L69)).
Inputs follow the same empty/JSON/raw-string conversion as other functions.
The post hook receives the arguments actually sent downstream and the serialized
MCP result
([handler](https://github.com/openai/codex/blob/25af12f7e61572b0bc18ddb1008be543b91519b0/codex-rs/core/src/tools/handlers/mcp.rs#L180-L264),
[output adapter](https://github.com/openai/codex/blob/25af12f7e61572b0bc18ddb1008be543b91519b0/codex-rs/core/src/tools/context.rs#L72-L114)).

In this release that result has:

```json
{
  "content": ["<arbitrary JSON MCP content blocks>"],
  "structuredContent": "<optional arbitrary JSON>",
  "isError": "<optional boolean>",
  "_meta": "<optional arbitrary JSON>"
}
```

`content` is required; the other three fields are omitted when absent
([Codex MCP protocol type](https://github.com/openai/codex/blob/25af12f7e61572b0bc18ddb1008be543b91519b0/codex-rs/protocol/src/mcp.rs#L149-L163)).
This is the strongest result shape available in the current first-party
source, but it remains a release observation because the Hooks guide only
guarantees “the MCP call result.”

Two transformations make the hook result differ from the server's original
wire data:

1. Apps-style file arguments can be uploaded and rewritten before the MCP call;
   `PostToolUse.tool_input` then contains those rewritten arguments rather than
   necessarily matching `PreToolUse.tool_input`
   ([source](https://github.com/openai/codex/blob/25af12f7e61572b0bc18ddb1008be543b91519b0/codex-rs/core/src/mcp_tool_call.rs#L385-L420)).
2. If the active model lacks image or audio input, Codex replaces corresponding
   MCP content blocks with text omission markers before the value reaches the
   tool output and hook
   ([call path](https://github.com/openai/codex/blob/25af12f7e61572b0bc18ddb1008be543b91519b0/codex-rs/core/src/mcp_tool_call.rs#L585-L624),
   [sanitizer](https://github.com/openai/codex/blob/25af12f7e61572b0bc18ddb1008be543b91519b0/codex-rs/core/src/mcp_tool_call.rs#L808-L845)).

### Fidelity limit

The hook does not carry MCP server id and original tool name as separate fields;
it only carries the flattened `mcp__...__...` string. It cannot recover original
file-path arguments after a post-call rewrite or media content replaced by the
model-capability sanitizer. Since MCP content blocks, `structuredContent`, and
`_meta` are arbitrary JSON, converting them to text also discards structure and
possibly non-text media. Preserve the complete response object and regard
`isError` as meaningful only when it is actually present.

## What a faithful bridge can and cannot normalize

| Candidate normalized fact | Faithful? | Reason |
| --- | --- | --- |
| canonical emitted tool name | yes | present verbatim as `tool_name` |
| call correlation | yes | `tool_use_id` is present in both events |
| opaque input JSON | yes | present verbatim for that hook stage |
| opaque post response JSON | yes | present verbatim after Codex's own transformations |
| shell command string | yes for `Bash` | documented `tool_input.command` |
| patch text | yes for `apply_patch` | documented `tool_input.command` |
| native tool kind (`exec_command` vs legacy shell) | no | both are `Bash` |
| shell exit status/success | no | no structured status in the hook response |
| stdout versus stderr | no | hook response is one output string |
| complete untruncated shell output | no | release applies truncation |
| structured patch effects | no | response is provider-formatted text |
| universal local-function success/error | no | result is handler-specific; fallback omits internal success |
| original MCP identity components | not reliably | only a flattened name is exposed |
| original MCP input/result before Codex rewrites | no | file arguments and unsupported media can be transformed |
| exhaustive observation of all Codex tools | no | hosted tools are absent and specialized paths may opt out |

## Design consequences for hook-bridge

1. Model a generic tool as at least `name` plus opaque JSON `input`; do not make
   a fixed union of Codex's current built-ins the canonical representation.
2. Model a post result with opaque JSON `response`. Text and explicit error
   projections can be optional conveniences, but the raw value must remain
   available and absence of an error flag must not be treated as proof of
   success.
3. Keep `tool_use_id` for correlation. Do not require post input to equal pre
   input, because MCP execution can legitimately rewrite it.
4. Preserve Codex's canonical emitted names. Do not serialize matcher aliases
   (`Edit`, `Write`, `Agent`) as tool identities, and do not relabel `Bash` as
   `exec_command` when the hook does not establish that distinction.
5. Treat tool-specific decoders and fixtures as adapter-version knowledge, not
   as the cross-provider domain contract.

## Remaining decision, not missing research

The primary sources settle what data exists. They do not decide the product
interface: hook-bridge still needs to choose whether opaque provider JSON is
the primary `ToolResult` representation or an escape hatch alongside
convenience fields. That is a design decision, not another protocol-research
question.
