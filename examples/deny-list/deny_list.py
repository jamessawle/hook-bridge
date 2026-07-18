# /// script
# requires-python = ">=3.12"
# dependencies = ["hook-bridge-sdk"]
# ///
"""A minimal Hook: deny any shell command containing a blocklisted token.

The smallest useful shape — one rule, two outcomes (allow / deny). It exists to
show the SDK's authoring and testing story, not to be a real security policy: the
blocklist is deliberately tiny and static. Copy this file, swap the list for your
own rule, and you have a working Hook.

Run it as a subprocess (the harness path)::

    uv run ./deny_list.py < context.json

Test it with no harness present (see test_deny_list.py)::

    deny_list.dispatch(tool_before(shell("rm -rf /")))
"""

from __future__ import annotations

from hook_bridge import (
    ToolBeforeContext,
    ToolBeforeVerdict,
    allow,
    defer,
    deny,
    hook,
)

# Illustrative only — a real Hook would source its policy from somewhere sturdier.
BLOCKED = ("rm -rf /", ":(){:|:&};:")


@hook
def deny_list(ctx: ToolBeforeContext) -> ToolBeforeVerdict:
    # git-guard's forward-compatible pattern: only vouch for shell commands.
    if ctx.tool.kind != "shell":  # pyright: ignore[reportUnnecessaryComparison]
        return defer()
    for token in BLOCKED:
        if token in ctx.tool.command:
            return deny(f"blocked: command contains {token!r}")
    return allow()


if __name__ == "__main__":  # runnable as a subprocess AND importable in tests
    deny_list.run()
