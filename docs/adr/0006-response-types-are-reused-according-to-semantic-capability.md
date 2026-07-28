# Response types are reused according to semantic capability

- **Status**: Accepted
- **Date**: 2026-07-28

Contract events reuse a response type only when they expose the same semantic
capabilities; genuinely different capabilities receive distinct response
types. This avoids both misleading reuse and an unbounded type per event or
tool, while leaving individual Verdict names and authoring helpers to
implementation time.
