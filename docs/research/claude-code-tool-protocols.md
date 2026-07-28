# Claude Code tool hook protocols

Research for [Inventory Claude Code tool hook protocols](https://github.com/jamessawle/hook-bridge/issues/37), captured 2026-07-28.

## Answer

Claude Code gives `PreToolUse` and `PostToolUse` a stable *outer* envelope, but
does not give every possible tool a stable common payload schema:

- `PreToolUse` carries the exact received `tool_name`, a JSON object
  `tool_input`, and `tool_use_id`.
- `PostToolUse` carries those fields plus an unconstrained `tool_response` and,
  in recent versions, optional `duration_ms`. It fires only after successful
  execution; failures use `PostToolUseFailure` and carry a top-level error
  string instead of `tool_response`.
- Built-in tools use bare names. Custom in-process functions and external MCP
  tools both use `mcp__<server>__<tool>` and cannot be distinguished from the
  hook payload alone.
- A useful subset of built-ins has published input/output schemas, but the
  complete runtime tool set is version-, provider-, platform-, feature-, and
  settings-dependent. Several current first-party pages disagree on built-in
  output field names. Consequently, the only faithful general contract is to
  preserve the received name, input object, and response JSON without loss;
  typed projections such as “shell command” or “file write” must be optional
  refinements.

These conclusions follow directly from Anthropic's hook types, where
`tool_input` is `dict[str, Any]` and `tool_response` is `Any`, and from the
runtime-dependent tool-set warning in the tools reference.
([hook input types](https://code.claude.com/docs/en/agent-sdk/python#pretoolusehookinput);
[tool availability](https://code.claude.com/docs/en/tools-reference#check-which-tools-are-available))

## Documented hook envelope

All hook events may carry:

```text
session_id: string
transcript_path: string
cwd: string
hook_event_name: string
prompt_id?: string
permission_mode?: "default" | "plan" | "acceptEdits" | "auto" | "dontAsk" | "bypassPermissions"
effort?: { level: "low" | "medium" | "high" | "xhigh" | "max" }
agent_id?: string
agent_type?: string
```

Presence is conditional: `prompt_id` is absent before the first prompt;
`permission_mode` is not sent to every event; `effort` depends on the event and
model; and agent fields appear only for agent/subagent contexts. The transcript
is written asynchronously and may lag the in-memory conversation.
([common hook input fields](https://code.claude.com/docs/en/hooks#common-input-fields))

The event-specific contracts are:

```text
PreToolUse = Common & {
  hook_event_name: "PreToolUse"
  tool_name: string
  tool_input: object
  tool_use_id: string
}

PostToolUse = Common & {
  hook_event_name: "PostToolUse"
  tool_name: string
  tool_input: object
  tool_response: any
  tool_use_id: string
  duration_ms?: number
}

PostToolUseFailure = Common & {
  hook_event_name: "PostToolUseFailure"
  tool_name: string
  tool_input: object
  tool_use_id: string
  error: string
  is_interrupt?: boolean
  duration_ms?: number
}
```

The Agent SDK type reference deliberately leaves `tool_response` as `Any`.
The hook reference says `PostToolUse` runs only after success and
`PostToolUseFailure` handles thrown errors and MCP error results. Calls rejected
before execution because of an unknown name, invalid input, or permission
denial produce neither post-use event.
([PreToolUse and PostToolUse types](https://code.claude.com/docs/en/agent-sdk/python#pretoolusehookinput);
[PostToolUse](https://code.claude.com/docs/en/hooks#posttooluse);
[PostToolUseFailure](https://code.claude.com/docs/en/hooks#posttoolusefailure))

`PostToolUse` observes a completed side effect. Its output may change the
result Claude sees, but cannot undo the tool's work, and telemetry already
contains the original result.
([PostToolUse decision control](https://code.claude.com/docs/en/hooks#posttooluse-decision-control))

## Names Claude Code can expose

### Built-ins

The current tools reference publishes these exact bare names:

```text
Agent                    Artifact                 AskUserQuestion
Bash                     CronCreate               CronDelete
CronList                 Edit                     EndConversation
EnterPlanMode            EnterWorktree            ExitPlanMode
ExitWorktree             Glob                     Grep
ListMcpResourcesTool     LSP                      Monitor
NotebookEdit             PowerShell               PushNotification
Read                     ReadMcpResourceTool      RemoteTrigger
ReportFindings           ScheduleWakeup           SendMessage
SendUserFile             ShareOnboardingGuide     Skill
TaskCreate               TaskGet                  TaskList
TaskOutput               TaskStop                 TaskUpdate
TodoWrite                ToolSearch               WaitForMcpServers
WebFetch                 WebSearch                Workflow
Write
```

This is a current catalog, not a closed protocol enum. Anthropic states that
the exact loaded set depends on provider, platform, and settings; the table
also marks tools with explicit version, subscription, feature-flag, operating
system, or environment restrictions. The tools reference says these names are
the strings used in hook matchers, while the hooks reference's shorter
PreToolUse list names only core tools and MCP tools. Therefore an adapter must
accept any string and preserve unknown names rather than validate against the
catalog.
([complete tools reference](https://code.claude.com/docs/en/tools-reference);
[PreToolUse matcher values](https://code.claude.com/docs/en/hooks#pretooluse);
[runtime availability](https://code.claude.com/docs/en/tools-reference#check-which-tools-are-available))

There are compatibility aliases: `Task` is accepted for `Agent` and is still
reported in one initialization surface; `BashOutput` aliases `TaskOutput`; and
`KillShell`/`KillBash` alias `TaskStop`. The documentation does not guarantee
that hooks canonicalize an alias before exposing `tool_name`, so consumers
should preserve the actual received string.
([Agent schema](https://code.claude.com/docs/en/agent-sdk/python#agent);
[TaskOutput schema](https://code.claude.com/docs/en/agent-sdk/python#taskoutput);
[TaskStop schema](https://code.claude.com/docs/en/agent-sdk/python#taskstop))

### MCP and local-function tools

External MCP tools are exposed as:

```text
mcp__<configured-server-name>__<tool-name>
```

Plugin-bundled servers use a scoped segment:
`mcp__plugin_<plugin-name>_<server-name>__<tool-name>`. The exact input is the
arguments object for that server tool, whose shape is defined by the tool's
JSON Schema `inputSchema`; that schema is not embedded in the hook event.
([MCP hook names](https://code.claude.com/docs/en/hooks#match-mcp-tools);
[MCP Tool definition](https://modelcontextprotocol.io/specification/2025-06-18/server/tools#tool))

An Agent SDK “local function” is not a third hook category. The SDK wraps the
function in an in-process MCP server, and the key used in `mcpServers` becomes
the server segment of the same `mcp__<server>__<tool>` name. Thus hooks cannot
faithfully normalize provenance to `local-function` versus `external-MCP`:
both have the same namespace and payload model.
([custom in-process tools](https://code.claude.com/docs/en/agent-sdk/custom-tools);
[custom-tool name format](https://code.claude.com/docs/en/agent-sdk/custom-tools#tool-name-format))

MCP tool results are `CallToolResult` objects. The protocol permits a
heterogeneous `content` array (text, image, audio, resource link, or embedded
resource), optional JSON-object `structuredContent`, optional `isError`, and
general result metadata. A tool may publish an `outputSchema` for
`structuredContent`, but neither it nor `inputSchema` rides in the hook
payload. Claude Code says MCP output passes through its PostToolUse replacement
path without schema validation. An MCP result with `isError: true` is a failed
tool call and goes to `PostToolUseFailure`, not successful `PostToolUse`.
([MCP tool result](https://modelcontextprotocol.io/specification/2025-06-18/server/tools#tool-result);
[MCP output schemas](https://modelcontextprotocol.io/specification/2025-06-18/server/tools#output-schema);
[Claude custom result blocks](https://code.claude.com/docs/en/agent-sdk/custom-tools#return-images-and-resources);
[PostToolUse MCP handling](https://code.claude.com/docs/en/hooks#posttooluse-decision-control);
[PostToolUseFailure](https://code.claude.com/docs/en/hooks#posttoolusefailure))

The TypeScript in-process SDK can return `structuredContent`; the Python
`@tool` adapter currently forwards only `content` and `is_error`, requiring a
standalone MCP server for structured content. That is an SDK implementation
limit, not a hook-level distinction.
([structured custom-tool results](https://code.claude.com/docs/en/agent-sdk/custom-tools#return-structured-data))

## Published built-in input/output shapes

The Python Agent SDK reference explicitly describes the following as the
schemas of tool inputs and outputs in messages. `?` below means optional or
nullable. Nested members are shown where they carry semantics Hook Bridge may
otherwise lose. The linked reference is the first-party canonical detail for
each shape.
([Tool Input/Output Types](https://code.claude.com/docs/en/agent-sdk/python#tool-input-output-types))

| Tool | `tool_input` | Successful structured output documented by the SDK |
|---|---|---|
| [`Agent`](https://code.claude.com/docs/en/agent-sdk/python#agent) | `{description, prompt, subagent_type?, model?, run_in_background?, name?, team_name?, mode?, isolation?}` | Union on `status`: `completed` includes `agentId`, `agentType?`, text `content[]`, model/token/usage/tool statistics, prompt, and optional worktree data; `async_launched` includes `agentId`, description/model data and prompt; `remote_launched` includes `taskId`, `sessionUrl`, description, prompt and `outputFile`. |
| [`AskUserQuestion`](https://code.claude.com/docs/en/agent-sdk/python#askuserquestion) | `{questions: [{question, header, options: [{label, description, preview?}], multiSelect}], answers?, annotations?, metadata?}` | `{questions, answers: object<string,string>, response?, annotations?, afkTimeoutMs?}` |
| [`Bash`](https://code.claude.com/docs/en/agent-sdk/python#bash) | `{command, timeout?, description?, run_in_background?}` | `{output, exitCode, killed?, shellId?}` |
| [`Monitor`](https://code.claude.com/docs/en/agent-sdk/python#monitor) | Exactly one source: `{command?, ws?: {url, protocols?}, description, timeout_ms?, persistent?}` | `{taskId, timeoutMs, persistent?}` |
| [`Edit`](https://code.claude.com/docs/en/agent-sdk/python#edit) | `{file_path, old_string, new_string, replace_all?}` | `{message, replacements, file_path}` |
| [`Read`](https://code.claude.com/docs/en/agent-sdk/python#read) | `{file_path, offset?, limit?}` | Text: `{content, total_lines, lines_returned}`; image: `{image, mime_type, file_size}` |
| [`Write`](https://code.claude.com/docs/en/agent-sdk/python#write) | `{file_path, content}` | `{message, bytes_written, file_path}` |
| [`Glob`](https://code.claude.com/docs/en/agent-sdk/python#glob) | `{pattern, path?}` | `{matches: string[], count, search_path}` |
| [`Grep`](https://code.claude.com/docs/en/agent-sdk/python#grep) | `{pattern, path?, glob?, type?, output_mode?, "-i"?, "-n"?, "-B"?, "-A"?, "-C"?, head_limit?, multiline?}` | Content mode: `{matches: [{file, line_number?, line, before_context?, after_context?}], total_matches}`; files mode: `{files, count}`. The reference does not publish a separate count-mode output object. |
| [`NotebookEdit`](https://code.claude.com/docs/en/agent-sdk/python#notebookedit) | `{notebook_path, cell_id?, new_source, cell_type?: "code" \| "markdown", edit_mode?: "replace" \| "insert" \| "delete"}` | `{message, edit_type, cell_id?, total_cells}` |
| [`WebFetch`](https://code.claude.com/docs/en/agent-sdk/python#webfetch) | `{url, prompt}` | `{bytes, code, codeText, result, durationMs, url}` |
| [`WebSearch`](https://code.claude.com/docs/en/agent-sdk/python#websearch) | `{query, allowed_domains?, blocked_domains?}` | `{query, results: (string \| {tool_use_id, content: [{title,url}]})[], durationSeconds}` |
| [`TodoWrite`](https://code.claude.com/docs/en/agent-sdk/python#todowrite) | `{todos: [{content, status: "pending" \| "in_progress" \| "completed", activeForm}]}` | `{message, stats: {total, pending, in_progress, completed}}` |
| [`TaskCreate`](https://code.claude.com/docs/en/agent-sdk/python#taskcreate) | `{subject, description, activeForm?, metadata?}` | `{task: {id, subject}}` |
| [`TaskUpdate`](https://code.claude.com/docs/en/agent-sdk/python#taskupdate) | `{taskId, status?, subject?, description?, activeForm?, addBlocks?, addBlockedBy?, owner?, metadata?}` | `{success, taskId, updatedFields, error?, statusChange?: {from,to}}` |
| [`TaskGet`](https://code.claude.com/docs/en/agent-sdk/python#taskget) | `{taskId}` | `{task?: {id, subject, description, status, blocks, blockedBy}}` |
| [`TaskList`](https://code.claude.com/docs/en/agent-sdk/python#tasklist) | `{}` | `{tasks: [{id, subject, status, owner?, blockedBy}]}` |
| [`TaskOutput`](https://code.claude.com/docs/en/agent-sdk/python#taskoutput) | `{task_id, block, timeout}` | `{retrieval_status: "success" \| "timeout" \| "not_ready", task?: object}`; task is deliberately open and may have type-specific fields such as `exitCode`. |
| [`TaskStop`](https://code.claude.com/docs/en/agent-sdk/python#taskstop) | `{task_id?, shell_id?}` | `{message, task_id, task_type, command?}` |
| [`ExitPlanMode`](https://code.claude.com/docs/en/agent-sdk/python#exitplanmode) | `{plan}` | `{message, approved?}` |
| [`ListMcpResourcesTool`](https://code.claude.com/docs/en/agent-sdk/python#listmcpresources) | `{server?}` | `{resources: [{uri, name, description?, mimeType?, server}], total}` |
| [`ReadMcpResourceTool`](https://code.claude.com/docs/en/agent-sdk/python#readmcpresource) | `{server, uri}` | `{contents: [{uri, mimeType?, text?, blob?}], server}` |

The broader tools reference currently names many additional built-ins for
which the Agent SDK I/O section publishes no exact schema: `Artifact`,
`CronCreate`, `CronDelete`, `CronList`, `EndConversation`, `EnterPlanMode`,
`EnterWorktree`, `ExitWorktree`, `LSP`, `PowerShell`, `PushNotification`,
`RemoteTrigger`, `ReportFindings`, `ScheduleWakeup`, `SendMessage`,
`SendUserFile`, `ShareOnboardingGuide`, `Skill`, `ToolSearch`,
`WaitForMcpServers`, and `Workflow`. Their names are documented; their complete
hook payload shapes are not. This is another reason not to make the current
published subset a closed union.
([tools catalog](https://code.claude.com/docs/en/tools-reference);
[SDK I/O catalog](https://code.claude.com/docs/en/agent-sdk/python#tool-input-output-types))

## First-party documentation conflicts and unstable detail

The current first-party pages do not define one consistent built-in
`tool_response` wire schema:

- The hook reference's `Write` PostToolUse example is
  `{filePath, success}`, while the SDK reference documents
  `{message, bytes_written, file_path}`.
- The hook reference's valid `Bash` replacement is
  `{stdout, stderr, interrupted, isImage}`, while the SDK reference documents
  `{output, exitCode, killed?, shellId?}`.
- The hook reference says `ExitPlanMode` hooks receive injected
  `{plan, planFilePath, allowedPrompts?}` and PostToolUse receives
  `{plan, filePath, ...internalStatusFlags}`, while the SDK reference documents
  input `{plan}` and output `{message, approved?}`.

These are documented contradictions, not runtime observations. Together with
the SDK's `tool_response: Any` type, they mean a Hook Bridge codec must not
claim any one of those output objects as a cross-version Claude Code guarantee.
([Write PostToolUse example](https://code.claude.com/docs/en/hooks#posttooluse-input);
[Write SDK schema](https://code.claude.com/docs/en/agent-sdk/python#write);
[Bash replacement example](https://code.claude.com/docs/en/hooks#posttooluse-decision-control);
[Bash SDK schema](https://code.claude.com/docs/en/agent-sdk/python#bash);
[ExitPlanMode hook fields](https://code.claude.com/docs/en/hooks#pretooluse-input);
[ExitPlanMode SDK schema](https://code.claude.com/docs/en/agent-sdk/python#exitplanmode))

No live payload observation was added to this note. The local binary reported
Claude Code 2.1.220, but the non-interactive probe could not authenticate.
That absence matters: examples above remain documentation claims and are not
presented as measurements of 2.1.220.

## Information that cannot be normalized faithfully

1. **A closed tool enum.** The loaded built-in set changes with runtime
   version and environment, while MCP names are open-ended.
2. **Local versus remote provenance.** Local Agent SDK functions and external
   MCP tools have the same `mcp__server__tool` shape.
3. **A universal typed input.** Built-in inputs are heterogeneous; MCP inputs
   are arbitrary JSON objects whose `inputSchema` is not present in the event.
4. **A universal text/exit-code result.** Most tools do not have process exit
   codes. Results may be structured objects, variants, text, images, audio,
   base64 data, resource links, embedded resources, or structured JSON.
5. **A universal “result status” on successful PostToolUse.** Failure is a
   separate event, and an MCP `isError` result follows that failure path.
6. **A stable per-built-in response object.** First-party references disagree
   today, and the public hook type intentionally uses `Any`.
7. **Tool schema from the hook alone.** Neither an MCP tool's `inputSchema` nor
   its optional `outputSchema` is carried alongside the invocation.
8. **Reversibility.** `PostToolUse` feedback can affect what Claude sees next,
   but cannot undo the completed side effect.

## Consequence for Hook Bridge

The portable floor should be lossless and open:

```text
Tool {
  name: string
  input: JSON object
}

SuccessfulToolResult {
  output: JSON value
}
```

The native payload (or every unknown field needed to reconstruct it) should
remain available. Shell-specific accessors may project `command`, output text,
and exit status when the harness/version actually supplies them, but those
fields cannot be requirements of generic `Tool` or generic successful
`ToolResult`. Likewise, `mcp__...` parsing can expose a *hint* about the server
and tool segments without asserting transport or provenance.

Faithful failure support is a separate lifecycle decision: Claude Code exposes
`PostToolUseFailure`, not a failed `PostToolUse`. If Hook Bridge wants one
portable `tool.after` event for both outcomes, that merge must be an explicit
semantic choice rather than an assumed property of the Claude protocol.

## Newly surfaced decisions

- **Define the portable tool-failure lifecycle.** Decide whether
  `PostToolUseFailure` maps to `tool.after`, to a distinct portable event, or
  remains unsupported; specify how it correlates with `tool_use_id` and what
  becomes of MCP `isError`.
- **Set a compatibility policy for known built-in projections.** Decide
  whether Claude-specific typed projections are version-gated, best-effort
  decoders with raw fallback, or omitted until first-party response schemas
  converge.
