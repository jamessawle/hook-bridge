"""The harness registry: `ADAPTERS[harness]` is the one `HarnessAdapter` for
that harness (#8).

`stub` exists only to prove the CLI & IO plumbing (#11) moves bytes correctly
across every seam. `claude-code` and `codex` (#12) are the real Adapters —
each slots in here unchanged, since adding a harness never touches `cli.py`
or `hook_process.py`.
"""

from __future__ import annotations

from ..codec import HarnessAdapter
from .claude_code import claude_code_adapter
from .codex import codex_adapter
from .stub import stub_adapter

ADAPTERS: dict[str, HarnessAdapter] = {
    "stub": stub_adapter,
    "claude-code": claude_code_adapter,
    "codex": codex_adapter,
}
