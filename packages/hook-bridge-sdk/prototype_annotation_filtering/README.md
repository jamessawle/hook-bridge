# PROTOTYPE — annotation-driven Hook filtering

This throwaway prototype asks whether typed function parameters can serve as
both Hook filters and injected values. The first Context parameter fixes the
event; optional `Tool` projection, Terminal observation, Harness, and Native
parameters add AND-ed filters. A non-match returns that event's neutral Verdict,
while a match calls the function with the precise types it declared.

It also makes one composition choice concrete: composed Hooks are considered in
declaration order and the first matching Hook handles the Context. If no Hook
matches, composition returns the event-neutral Verdict. This avoids inventing a
Verdict-merging algebra; the terminal display makes overlaps visible so this
choice can be challenged.

Run it from the repository root:

```console
mise run prototype-annotation-filtering
```

Use the number keys to select scenarios. The screen shows the Context, each
Hook's annotation-derived filters, the match trace, the selected Hook, its
injected argument types, and the resulting Verdict.
