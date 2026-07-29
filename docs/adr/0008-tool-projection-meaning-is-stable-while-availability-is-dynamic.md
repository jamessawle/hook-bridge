# Tool projection meaning is stable while availability is dynamic

- **Status**: Accepted
- **Date**: 2026-07-29

Typed Tool projections are best-effort runtime capabilities with stable,
Harness-independent meaning, paired with lossless Native data. An Adapter emits
a projection only when every required field can be derived faithfully: unknown
extra Native fields are tolerated, while missing, changed, or ambiguous required
fields make the projection absent rather than guessed. Hooks must therefore
handle an absent projection even for a Tool that was projected previously,
because availability may change independently of the hook-bridge version as a
Harness evolves.

Existing projection types and required fields follow the SDK's compatibility
policy; changing their meaning or required shape is a breaking Contract change,
while adding a new projection type is compatible. This preserves useful typed
authoring without promising stability that upstream, unversioned Tool schemas
cannot provide, and Native data keeps unknown Tools and schema drift observable.
