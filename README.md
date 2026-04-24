# Flotilla

**An AI-native SDLC starter kit.** Clone → install three tools → bootstrap → ship.

Flotilla gives you the three tools every AI-native project needs, pre-wired and ready:
- **Mercator** — code map (what lives where, what depends on what)
- **Hopewell** — work ledger (typed nodes, flow network, release scoring)
- **Pedia** — knowledge base (block-indexed specs + decisions + north stars)

Plus a minimal six-agent bundle, pre-initialized stores, git hooks, and a trivial
notes CLI as the domain so the tooling is what you study, not the business logic.

## Prerequisites (one-time)

- Python 3.10+
- git
- Optional: `gh` CLI (for GitHub integration)
- One of: Claude Code CLI / Codex / OpenCode

## Quickstart — 6 commands

```bash
git clone https://github.com/ocgully/flotilla
cd flotilla
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
- `.claude/agents/` with six slim agents: architect, engineer, planner, testing-qa, release-engineer, orchestrator

## Multi-tool support

- **Claude Code**: `hopewell hooks install --full --claude-code` wires hooks into `~/.claude/settings.json`; `.claude/agents/` holds the agent roster.
- **Codex**: reads `AGENTS.md` for agent aliases; shares the same `.hopewell/`, `.pedia/`, `.mercator/` CLIs.
- **OpenCode**: reads `AGENTS.md` as well; project-specific overrides can live under `.opencode/` if you want them.

See [`docs/multi-tool.md`](docs/multi-tool.md) for details.

## The orchestrator-first convention

Flotilla projects route every Claude Code request through `@orchestrator` by default. The
SessionStart hook (installed by `scripts/bootstrap.sh`) injects a preamble reminding the
session of this convention. You invoke work via a slash command, not by naming a specific
agent:

```
/o  add a tag field to notes with search support
/orchestrate  cut a v0.2 release once HW-0006 and HW-0007 are done
```

`@orchestrator` composes the full context bundle (Hopewell state, Pedia-cited specs, Mercator
systems view, active claims) and dispatches to `@engineer` / `@architect` / `@planner` /
`@testing-qa` / `@release-engineer` with that bundle already in hand — so downstream agents
don't re-discover state.

If you genuinely need to bypass the orchestrator (e.g. you know the exact specialist and have
the context), pass `--direct`:

```
/engineer --direct  fix the typo in notes/store.py line 42
```

Direct invocation should be the exception, not the default. Spotty output across a long
session is almost always the signature of skipped orchestration.

## Try the loops

1. **Start a new feature** (via `/o`)

   ```
   /o  add tag support to notes with #hashtag indexing
   ```

   Or, if you just want the Hopewell node without engaging an agent yet:

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
flotilla/
├── notes/             # the toy domain (~230 LOC)
├── tests/             # stdlib unittest only
├── .hopewell/         # work ledger (agents query via `hopewell`, never read directly)
├── .pedia/            # knowledge base (agents query via `pedia`)
├── .mercator/         # code map (agents query via `mercator`)
├── .claude/agents/    # six slim core agents, maintained in-repo
├── docs/              # tutorial + release + multi-tool guides
└── scripts/bootstrap.sh
```

## Links

- [Hopewell](https://github.com/ocgully/Hopewell)
- [Pedia](https://github.com/ocgully/pedia)
- [Mercator](https://github.com/ocgully/mercator)
