# Repository guidance

- Use `mise run setup` to install the pinned toolchain and locked dependencies.
- Use `mise run validate` to run all repository checks, and run it before
  handing off changes.
- Declare Python dependencies in the relevant `pyproject.toml` and commit the
  updated `uv.lock`; Mise manages toolchain versions, not Python packages.
- Architecture decisions live in `docs/adr/`.
