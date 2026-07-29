"""PROTOTYPE: test whether tool.after filtering needs richer domain entities.

Question: can Tool, Observation type, and Harness be three independent
selectors over one Context, while Native data and projections remain payload
details rather than additional filtering concepts?
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Literal

Harness = Literal["claude-code", "codex"]
Observation = Literal["result", "error"]


@dataclass(frozen=True)
class Context:
    harness: Harness
    tool: str
    observation: Observation
    projection: str | None
    native_summary: str


@dataclass(frozen=True)
class HookFilter:
    tool: str | None = None
    observation: Observation | None = None
    harness: Harness | None = None

    def matches(self, context: Context) -> bool:
        return (
            (self.tool is None or self.tool == context.tool)
            and (
                self.observation is None
                or self.observation == context.observation
            )
            and (self.harness is None or self.harness == context.harness)
        )


SCENARIOS = (
    Context("claude-code", "shell", "result", "ShellResult", "exitCode=0"),
    Context("codex", "shell", "result", "ShellResult", "output string"),
    Context("claude-code", "file-edit", "error", None, "failure string"),
    Context("codex", "mcp", "error", None, "isError=true"),
    Context("codex", "unknown-native-tool", "result", None, "arbitrary JSON"),
)


def toggle_filter(current: HookFilter, axis: str, context: Context) -> HookFilter:
    value = getattr(current, axis)
    return replace(current, **{axis: None if value is not None else getattr(context, axis)})


def render(index: int, hook_filter: HookFilter) -> None:
    context = SCENARIOS[index]
    print("\033[2J\033[H", end="")
    print("\033[1mPROTOTYPE — tool.after filtering\033[0m")
    print("\n\033[1mCurrent context\033[0m")
    for field, value in context.__dict__.items():
        print(f"  {field}: {value}")
    print("\n\033[1mHook filter\033[0m")
    for field, value in hook_filter.__dict__.items():
        print(f"  {field}: {value or '*'}")
    print(f"\n\033[1mInvoked:\033[0m {hook_filter.matches(context)}")
    print("\n[s] next scenario  [t] toggle Tool  [o] toggle Observation")
    print("[h] toggle Harness  [q] quit")


def main() -> None:
    index = 0
    hook_filter = HookFilter()
    while True:
        render(index, hook_filter)
        command = input("> ").strip().lower()
        if command == "q":
            return
        if command == "s":
            index = (index + 1) % len(SCENARIOS)
        elif command == "t":
            hook_filter = toggle_filter(hook_filter, "tool", SCENARIOS[index])
        elif command == "o":
            hook_filter = toggle_filter(
                hook_filter, "observation", SCENARIOS[index]
            )
        elif command == "h":
            hook_filter = toggle_filter(hook_filter, "harness", SCENARIOS[index])


if __name__ == "__main__":
    main()
