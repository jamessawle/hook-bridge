# /// script
# requires-python = ">=3.12"
# dependencies = ["hook-bridge-sdk"]
# ///
"""A fuller Hook: a four-outcome command policy over shell commands.

Where deny-list shows the minimum, this shows the whole `tool.before` Verdict
surface — allow / deny / ask / defer — plus decomposing logic into helpers and
narrowing on the tool kind. It's the shape a real guard takes (this is roughly
what a git-guard-style Hook looks like structurally), without the brittle,
degrades-over-time CLI parsing: the rules here are deliberately synthetic
substring/prefix tables, so the example stays a stable teaching reference.

The four outcomes:

  - DEFER on a non-shell tool or an empty command — no opinion.
  - DENY  a command matching the block table — hard block, with a reason.
  - ASK   a command matching the review table — proceed only after confirmation.
  - ALLOW a command on the vouched-for prefix table — auto-approve.
  - DEFER anything else — let the harness's normal permission flow decide.

Deny beats ask beats allow: the checks run in that order, so the most protective
outcome wins.
"""

from __future__ import annotations

from hook_bridge import (
    ToolBeforeContext,
    ToolBeforeVerdict,
    allow,
    ask,
    defer,
    deny,
    hook,
)

# Illustrative rule tables — swap these for your own policy. Kept as plain
# substrings/prefixes on purpose: no shell tokenising, no shelling out, nothing
# that rots as an underlying CLI changes.
BLOCKED = ("rm -rf /", "mkfs", "dd if=")  # never allowed
NEEDS_REVIEW = ("--force", "--hard", "sudo ")  # allowed only after confirmation
VOUCHED = ("git status", "git diff", "git log", "ls", "cat ")  # known-safe prefixes


def _contains_any(command: str, tokens: tuple[str, ...]) -> bool:
    return any(token in command for token in tokens)


def _starts_with_any(command: str, prefixes: tuple[str, ...]) -> bool:
    stripped = command.strip()
    return any(stripped.startswith(prefix) for prefix in prefixes)


@hook
def command_policy(ctx: ToolBeforeContext) -> ToolBeforeVerdict:
    if ctx.tool.kind != "shell":  # pyright: ignore[reportUnnecessaryComparison]
        return defer()
    command = ctx.tool.command
    if not command.strip():
        return defer()

    if _contains_any(command, BLOCKED):
        return deny(f"blocked by policy: {command!r}")
    if _contains_any(command, NEEDS_REVIEW):
        return ask("this command needs confirmation before it runs")
    if _starts_with_any(command, VOUCHED):
        return allow()
    return defer()  # unrecognised — no opinion, defer to the harness


if __name__ == "__main__":  # runnable as a subprocess AND importable in tests
    command_policy.run()
