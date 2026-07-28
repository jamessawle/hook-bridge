# Canonical event names use `category.moment` namespaces

- **Status**: Accepted
- **Date**: 2026-07-28

Contract event names use the stable `category.moment` form, separating the
kind of activity from when the Hook observes it. This gives event families a
predictable, Harness-independent namespace without elevating any individual
event name to an architectural decision.
