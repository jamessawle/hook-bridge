"""The harness registry: `ADAPTERS[harness]` is the one `HarnessAdapter` for
that harness (#8).

v1 ships only the `stub` Adapter, which exists to prove the CLI & IO plumbing
(#11) moves bytes correctly across every seam. The real claude-code and codex
Adapters are sibling work (#12) and slot in here unchanged — adding a harness
never touches `cli.py` or `hook_process.py`.
"""

from __future__ import annotations

from ..codec import HarnessAdapter
from .stub import stub_adapter

ADAPTERS: dict[str, HarnessAdapter] = {
    "stub": stub_adapter,
}
