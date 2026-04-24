# Agents in this project

Six slim agents live in `.claude/agents/`. Aliases recognised by Codex and OpenCode:

- `@architect` — structural decisions + ADRs + boundaries
- `@engineer` — implementation within the boundaries
- `@planner` — spec authoring (`pedia spec new` is the primary path)
- `@testing-qa` — tests + fitness checks + boundary gate
- `@release-engineer` — gitflow + release cutting via `hopewell release`
- `@orchestrator` — routes work through the Hopewell flow network

For Hopewell + Pedia + Mercator CLI commands every agent can run, see
[`CLAUDE.md`](CLAUDE.md) and [`docs/multi-tool.md`](docs/multi-tool.md).

## Minimum capabilities every agent must have

- Execute shell commands (for the three CLIs)
- Read project files (but NOT `.hopewell/`, `.pedia/`, `.mercator/` directly —
  use the CLIs)
- Write files under `notes/`, `tests/`, and `docs/`

## Tool-specific notes

- **Claude Code** — full hook integration via `hopewell hooks install --full --claude-code`; agents in `.claude/agents/`
- **Codex** — reads this file; run `hopewell` / `pedia` / `mercator` CLIs as shell commands
- **OpenCode** — reads this file; same shell-CLI pattern as Codex
