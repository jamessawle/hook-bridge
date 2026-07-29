"""PROTOTYPE: compare candidate tool.after terminal-payload models.

Question: which model lets a Hook handle every observable terminal case while
keeping portable cases convenient and making Harness-specific logic explicit?
This is a visualization of trade-offs, not a proposed production schema.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

Model = Literal["native-only", "observation-union", "typed-plus-native"]


@dataclass(frozen=True)
class Scenario:
    label: str
    harness: str
    tool: str
    observation: str
    native_shape: str
    json_response: str | None
    faithful_projection: str | None
    tool_projection: dict[str, Any] | None
    observation_value: Any


SCENARIOS = (
    Scenario(
        "Claude shell result",
        "claude-code",
        "shell",
        "ToolResult",
        '{"output": str, "exitCode": int, ...}',
        "object",
        "ShellResult(output: str)",
        {"kind": "shell", "command": "ruff check ."},
        {"output": "All checks passed", "exitCode": 0},
    ),
    Scenario(
        "Codex shell result",
        "codex",
        "shell",
        "ToolResult",
        "str",
        "string",
        "ShellResult(output: str)",
        {"kind": "shell", "command": "ruff check ."},
        "All checks passed",
    ),
    Scenario(
        "Claude Edit result",
        "claude-code",
        "file-edit",
        "ToolResult",
        "unconstrained object; first-party schemas conflict",
        "object",
        None,
        {"kind": "file-edit", "paths": ["/repo/pyproject.toml"]},
        {
            "message": "Updated file",
            "replacements": 1,
            "file_path": "/repo/pyproject.toml",
        },
    ),
    Scenario(
        "Codex apply_patch result",
        "codex",
        "file-edit",
        "ToolResult",
        "provider-formatted str",
        "string",
        None,
        {"kind": "file-edit", "paths": ["/repo/pyproject.toml"]},
        "Done!",
    ),
    Scenario(
        "Codex MCP error",
        "codex",
        "mcp",
        "ToolError",
        "CallToolResult with isError=true and arbitrary content",
        None,
        None,
        {"kind": "mcp", "name": "filesystem__read_file"},
        {
            "content": [{"type": "text", "text": "permission denied"}],
            "isError": True,
        },
    ),
    Scenario(
        "Unknown future tool result",
        "either",
        "unknown",
        "ToolResult",
        "arbitrary JSON",
        "any JSON",
        None,
        None,
        {"future": ["arbitrary", {"nested": True}]},
    ),
)

MODELS: tuple[Model, ...] = (
    "native-only",
    "observation-union",
    "typed-plus-native",
)


def assessment(model: Model, scenario: Scenario) -> tuple[str, str, str]:
    if model == "native-only":
        return (
            "yes",
            "no",
            f"inspect {scenario.harness} Native variant",
        )
    if model == "observation-union":
        if scenario.observation == "ToolError":
            return (
                "yes",
                "ToolError(error: JSON)",
                "inspect Native only for Harness-specific detail",
            )
        return (
            "yes",
            "ToolResult(output: JSON)",
            "inspect Native only for Harness-specific detail",
        )
    if scenario.faithful_projection is not None:
        return ("yes", scenario.faithful_projection, "no Harness branch")
    return ("yes", "classification/tool identity only", "inspect Native payload")


def concrete_hook_decision(scenario: Scenario) -> str:
    """A portable non-shell Hook: annotate successful protected-file edits."""
    projection = scenario.tool_projection
    if (
        scenario.observation != "ToolResult"
        or projection is None
        or projection.get("kind") != "file-edit"
    ):
        return "pass (not a successful projected file edit)"
    paths = projection.get("paths")
    if isinstance(paths, list) and "/repo/pyproject.toml" in paths:
        return "annotate (protected project configuration changed)"
    return "pass (file edit is not relevant)"


def render(scenario_index: int, model_index: int) -> None:
    scenario = SCENARIOS[scenario_index]
    model = MODELS[model_index]
    catchable, portable, hook_work = assessment(model, scenario)
    print("\033[2J\033[H", end="")
    print("\033[1mPROTOTYPE — tool.after payload models\033[0m")
    print("\n\033[1mScenario\033[0m")
    for field, value in scenario.__dict__.items():
        print(f"  {field}: {value}")
    print("\n\033[1mCandidate model\033[0m")
    print(f"  {model}")
    print("\n\033[1mHook experience\033[0m")
    print(f"  catchable: {catchable}")
    print(f"  portable data: {portable}")
    print(f"  payload work: {hook_work}")
    print("\n\033[1mConcrete non-shell Hook\033[0m")
    print("  target: successful file edits touching /repo/pyproject.toml")
    print(f"  verdict: {concrete_hook_decision(scenario)}")
    print("\n[s] next scenario  [m] next model  [q] quit")


def main() -> None:
    scenario_index = 0
    model_index = 0
    while True:
        render(scenario_index, model_index)
        command = input("> ").strip().lower()
        if command == "q":
            return
        if command == "s":
            scenario_index = (scenario_index + 1) % len(SCENARIOS)
        elif command == "m":
            model_index = (model_index + 1) % len(MODELS)


if __name__ == "__main__":
    main()
