# Agents in this project

Core agents are defined in `.claude/agents/` (composed from AgentFactory core).
Aliases recognised by Codex and OpenCode:

- `@vision-keeper` → product vision
- `@architect` → design + decomposition
- `@planner` → spec authoring
- `@orchestrator` → dispatch + gate management
- `@engineer` → (no core engineer; use project-local if declared)
- `@testing-qa` → test discipline
- `@technical-writer` → user-facing docs
- `@documentary` → progress narrative
- `@release-engineer` → gitflow + release cutting
- `@mercator-keeper` → code-map upkeep

For Hopewell + Pedia + Mercator CLI commands every agent can run, see
[`CLAUDE.md`](CLAUDE.md) and [`docs/multi-tool.md`](docs/multi-tool.md).

## Minimum capabilities every agent must have

- Execute shell commands (for the three CLIs)
- Read project files (but NOT `.hopewell/`, `.pedia/`, `.mercator/` directly —
  use the CLIs)
- Write files under `notes/`, `tests/`, and `docs/`

## Tool-specific notes

- **Claude Code** — full hook integration via `hopewell hooks install --full --claude-code`
- **Codex** — reads this file; run `hopewell` / `pedia` / `mercator` CLIs as shell commands
- **OpenCode** — reads this file; same shell-CLI pattern as Codex
