# The Contract admits only Harness-independent concepts

- **Status**: Accepted
- **Date**: 2026-07-28

The Contract contains only concepts a Hook can use independently of the
Harness that invoked it. Harness-specific names, payload shapes, quirks, and
unsupported capabilities terminate at the Adapter boundary; translation must
not invent information a Harness does not provide. This keeps Hooks portable
and makes unsupported capability cells explicit instead of silently lossy.
