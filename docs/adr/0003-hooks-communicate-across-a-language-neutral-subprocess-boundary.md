# Hooks communicate across a language-neutral subprocess boundary

- **Status**: Accepted
- **Date**: 2026-07-28

hook-bridge invokes each Hook as a separate process and exchanges validated
Context and Verdict data over a language-neutral wire Contract. The process
boundary costs an extra spawn, but lets runner and SDK implementations vary
independently, keeps Harness translation out of Hooks, and permits future Hook
languages without changing the Contract.
