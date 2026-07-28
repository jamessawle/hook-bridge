# Harness/event translations are independent, explicitly composed units

- **Status**: Accepted
- **Date**: 2026-07-28

Each supported Harness/event capability cell is translated by an independent
Codec and built-in Codecs are composed explicitly into their Harness Adapter.
This keeps changes local to one capability cell while making supported
translations, loading failures, and composition visible; individual mappings
and module layouts remain implementation choices.
