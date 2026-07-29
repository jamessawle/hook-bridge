# Repository guidance

- Use `mise run setup` to install the pinned toolchain and locked dependencies.
- Use `mise run validate` to run all repository checks, and run it before
  handing off changes.
- Declare Python dependencies in the relevant `pyproject.toml` and commit the
  updated `uv.lock`; Mise manages toolchain versions, not Python packages.
- Architecture decisions live in `docs/adr/`.
- Do not create an ADR without explicit human approval in the current
  conversation. Before requesting approval, present evidence for every
  criterion in [When to offer an ADR](.agents/skills/domain-modeling/ADR-FORMAT.md#when-to-offer-an-adr),
  including the family of implementations the decision constrains. Resolving a
  Wayfinder ticket does not itself authorize an ADR.
