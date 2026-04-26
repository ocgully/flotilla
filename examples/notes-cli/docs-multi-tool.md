# Multi-tool integration

This project is deliberately **tool-agnostic**. The three ecosystem CLIs
(`taskflow`, `pedia`, `codeatlas`) are just shell commands; any agent
harness that can spawn a process can drive them.

## Claude Code

**Setup:**

```bash
taskflow hooks install --full --claude-code
```

That single command:

1. Installs git hooks (pre-commit, commit-msg, post-commit, pre-push)
2. Writes entries into `~/.claude/settings.json` so the Claude Code harness
   dispatches the same events through `taskflow claude-hooks`.

**Agent roster:** `.claude/agents/` — six slim agents maintained directly in
the repo (no bundler).

**Queries (identical to the others):**

```bash
taskflow show HW-0003
pedia show --for HW-0003
codeatlas query touches notes/store.py
```

## Codex

**Setup:**

```bash
taskflow hooks install --full
# (no --claude-code flag — Codex discovers agents via AGENTS.md)
```

**Agent roster:** [`AGENTS.md`](../AGENTS.md) in the repo root. Codex reads
the alias list and maps `@architect`, `@planner`, etc., onto its own runner.

**Differences from Claude Code:**

- No `~/.claude/settings.json` mutation.
- No `.claude/hooks/` directory needed — git hooks do the enforcement; the
  harness doesn't need to fire parallel events.
- Specs, nodes, and the code map live in the same `.hopewell/` / `.pedia/` /
  `.mercator/` directories (legacy on-disk paths read transparently by the
  renamed tools).

## OpenCode

**Setup:** same as Codex.

```bash
taskflow hooks install --full
```

OpenCode also reads `AGENTS.md`. If you want project-scoped OpenCode
settings, drop them under `.opencode/` (not committed by default).

## What's identical across all three

- The three CLIs (`taskflow`, `pedia`, `codeatlas`) are the source of truth.
- Git hooks enforce invariants below the harness — no matter which agent
  tool is driving.
- Work-item IDs (`HW-NNNN`) are the cross-tool reference key.

## What differs

| Capability | Claude Code | Codex | OpenCode |
|-----------|-------------|-------|----------|
| Native hook dispatch | via `~/.claude/settings.json` | via git hooks only | via git hooks only |
| Agent discovery | `.claude/agents/` | `AGENTS.md` | `AGENTS.md` |
| Harness-level context awareness | CLAUDE.md + .claudeignore | AGENTS.md | AGENTS.md + .opencode/ |

## When adding tool-specific config

- **Claude Code** → `.claude/` (committed) or `~/.claude/settings.json` (user-scope)
- **Codex** → `AGENTS.md` is usually enough; if not, add a `.codex/` dir
- **OpenCode** → `.opencode/` for project overrides
