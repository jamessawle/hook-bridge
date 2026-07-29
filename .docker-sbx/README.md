# Docker Sandbox configuration

[`sandbox.sh`](sandbox.sh) composes the pinned community Mise kit with the
shared Mise Python/uv network, Python/uv workspace-isolation, and Codex harness
kits from `jamessawle/sbx-kits` v0.2.0.

The repository workspace is mounted directly so source edits remain visible
on the host. `UV_PROJECT_ENVIRONMENT` points uv at sandbox-local storage, so
the Linux virtual environment does not replace the host's macOS `.venv`.
`PYTHONPYCACHEPREFIX` likewise keeps compiled Python bytecode inside the VM.

| Command                     | Purpose                                        |
| --------------------------- | ---------------------------------------------- |
| `mise run sandbox`          | Refresh repository dependencies and attach     |
| `mise run sandbox rebuild`  | Replace the sandbox and apply the current kits |

The sandbox uses Codex and defaults to the name `hook-bridge`. Override the
sandbox name when needed:

```sh
SANDBOX_NAME=hook-bridge-alt mise run sandbox rebuild
SANDBOX_NAME=hook-bridge-alt mise run sandbox
```

Network policy is host-global and may affect unrelated sandboxes, so the Mise
task does not change it. Organisation governance may override local policy and
kit rules.
