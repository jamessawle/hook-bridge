"""hook-bridge-runner — the `hook-bridge` CLI.

Translates a Harness's native hook protocol to and from the generic wire
Contract, running each Hook as a subprocess. See CONTEXT.md and
docs/adr/0003-runner-process-boundary.md at the repo root for the design.
"""

from __future__ import annotations

from .cli import main
from .codec import Codec, HarnessAdapter, RunnerError
from .hook_process import HookProcessError

__all__ = [
    "main",
    "Codec",
    "HarnessAdapter",
    "RunnerError",
    "HookProcessError",
]
