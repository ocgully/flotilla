# agentfactory-showcase

A working example of the AgentFactory ecosystem: **Mercator** (code map),
**Hopewell** (work ledger), **Pedia** (knowledge base) plus a core agent
bundle, multi-tool compatibility (Claude Code / Codex / OpenCode), and
git-hook-enforced quality gates. The notes CLI is the domain; everything
else is the setup you'd use for any project.

## Prerequisites (one-time)

- Python 3.10+
- git
- Optional: `gh` CLI (for GitHub integration)
- One of: Claude Code CLI / Codex / OpenCode

## Quickstart — 6 commands

```bash
git clone https://github.com/ocgully/agentfactory-showcase
cd agentfactory-showcase
pip install mercator hopewell pedia       # the three tools
pip install -e .                          # the toy notes CLI
bash scripts/bootstrap.sh                 # installs hooks, refreshes indexes
hopewell web --open                       # explore the canvas
```

That's it. The project is live. Try `pedia show --for HW-0001` to see what
Pedia pulls up for a work item.

## What's set up

- `.hopewell/` with 5 historical nodes + 2 open + 1 release
- `.pedia/` with 1 north-star, 1 constitution chapter, 1 spec, 1 decision, 1 PRD
- `.mercator/` with the notes CLI's systems map
- Git hooks: pre-commit (drift + HW-ref), commit-msg, post-commit (events), pre-push (release-score)
- `.claude/agents/` bundle composed from AgentFactory core

## Multi-tool support

- **Claude Code**: `hopewell hooks install --full --claude-code` wires hooks into `~/.claude/settings.json`; `.claude/agents/` holds the composed agent roster.
- **Codex**: reads `AGENTS.md` for agent aliases; shares the same `.hopewell/`, `.pedia/`, `.mercator/` CLIs.
- **OpenCode**: reads `AGENTS.md` as well; project-specific overrides can live under `.opencode/` if you want them.

See [`docs/multi-tool.md`](docs/multi-tool.md) for details.

## Try the loops

1. **Start a new feature**

   ```bash
   hopewell new --components work-item,deliverable --title "Tag notes with #hashtags"
   pedia show --for HW-0009
   ```

2. **Resolve a drift scenario** (edit the spec, commit, observe pre-commit block, resolve via reconcile)

   ```bash
   # Edit .pedia/specs/001-search/spec.md, then:
   git add .pedia/specs/001-search/spec.md
   git commit -m "Drift spec for HW-0003"   # pre-commit will flag
   hopewell reconcile                        # queues a downstream-review node
   ```

3. **Cut a release**

   ```bash
   hopewell release start v0.2.0 --scope HW-0006,HW-0007
   hopewell release score
   hopewell release finalize
   ```

## Layout

```
agentfactory-showcase/
├── notes/             # the toy domain (~230 LOC)
├── tests/             # stdlib unittest only
├── .hopewell/         # work ledger (agents query via `hopewell`, never read directly)
├── .pedia/            # knowledge base (agents query via `pedia`)
├── .mercator/         # code map (agents query via `mercator`)
├── .claude/agents/    # composed core-marketplace roster
├── docs/              # tutorial + release + multi-tool guides
└── scripts/bootstrap.sh
```

## Links

- [AgentFactory](https://github.com/ocgully/AgentFactory)
- [Hopewell](https://github.com/ocgully/Hopewell)
- [Pedia](https://github.com/ocgully/pedia)
- [Mercator](https://github.com/ocgully/mercator) (formerly codemap)
