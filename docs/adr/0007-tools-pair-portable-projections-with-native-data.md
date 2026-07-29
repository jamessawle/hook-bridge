# Tools pair portable projections with Native data

- **Status**: Accepted; supersedes ADR-0001 where it prohibited all Harness-specific Contract data
- **Date**: 2026-07-29

Every Contract Tool pairs required, Adapter-discriminated Native data with an optional Tool projection. The Native variant faithfully represents that Harness's definition at the observed hook event and gives Hooks a deliberate portability escape hatch; the projection contains only Harness-independent semantics and is present only when the Adapter can populate every required field without guessing. This compromise keeps Harness-agnostic Hook authoring practical in most cases while preserving enough information for unknown and Harness-specific tools to remain useful.

Projection meaning is portable, but projection availability need not be shared by every Harness. Native variants need not share a universal payload shape, and neither Native data nor projections claim to reconstruct Harness state that its hook definition did not expose.
