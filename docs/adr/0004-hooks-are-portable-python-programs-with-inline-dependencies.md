# Hooks are portable Python programs with inline dependencies

- **Status**: Accepted
- **Date**: 2026-07-28

Hooks are distributed as Python programs whose dependencies are declared
inline with PEP 723 and resolved by `uv`. Requiring a Python runtime is an
accepted portability constraint in exchange for source-level distribution,
native access to Python packages, and no separate build or installation step
for each Hook.
