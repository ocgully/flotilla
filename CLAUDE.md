# CLAUDE.md — Flotilla

## Project posture

Flotilla is an AI-native SDLC **starter kit**. The notes CLI domain is
deliberately trivial (~230 LOC, stdlib-only); what you're meant to study is the
tooling trio around it. Keep the agent set minimal and the loops obvious.

## Tools in use

| Tool | Store | How to query |
|------|-------|---------------|
| Hopewell | `.hopewell/` | **CLI only** — `hopewell list`, `hopewell show`, `hopewell query ...`. Never read files here directly. |
| Pedia | `.pedia/` | **CLI only** — `pedia query "..."`, `pedia show --for HW-NNNN`, `pedia trace <block>`. |
| Mercator | `.mercator/` | **CLI only** — `mercator query systems`, `mercator query touches <path>`, `mercator query contract <sys>`. |

Install the trio once: `pip install mercator hopewell pedia`.

## Agent roster

Six slim agents live in `.claude/agents/`:

- `@architect` — structural decisions + ADRs + boundaries
- `@engineer` — implementation within the boundaries
- `@planner` — spec authoring (`pedia spec new` is the primary path)
- `@testing-qa` — tests + fitness checks + boundary gate
- `@release-engineer` — gitflow + release cutting via `hopewell release`
- `@orchestrator` — routes work through the Hopewell flow network

Extend by dropping your own domain agents alongside the core six. There is no
bundler — `.claude/agents/` is maintained per-project.

## Hook-driven invariants

Once `scripts/bootstrap.sh` runs, the following are enforced automatically:

- **commit-msg** — every commit references `HW-NNNN` (merges and fixups excepted)
- **pre-commit** — spec drift blocks the commit; resolve via `hopewell reconcile`
- **post-commit** — Mercator + Pedia incremental refresh; Hopewell event recorded
- **pre-push** — on `release/*` branches, release-score must meet threshold

Do not pass `--no-verify` unless you are fixing a broken hook. If a hook blocks
you, surface the message — don't bypass it.

## Query flows (how an agent starts a task)

```bash
hopewell resume                           # what am I working on?
hopewell ready                            # what's ready to pick up?
hopewell show HW-0006                     # what does this entail?
pedia show --for HW-0006                  # specs + decisions cited by this node
mercator query touches notes/store.py     # where does this file live?
mercator query contract notes             # what's public vs internal?
pedia query "small fast notes"            # prior art
```

## Session resume protocol

1. **Session start** — `hopewell resume`
2. **Mid-work pause** — `hopewell checkpoint HW-NNNN --next "..."`
3. **Session end** — include `fixes HW-NNNN` in your commit message, or
   `hopewell close HW-NNNN --commit <sha> --reason "..."`.

## Multi-tool note

Codex and OpenCode read [`AGENTS.md`](AGENTS.md). The three CLIs are the source
of truth across harnesses — any tool that can spawn a shell can participate.
See [`docs/multi-tool.md`](docs/multi-tool.md) for side-by-side commands.

## Never read `.hopewell/`, `.pedia/`, or `.mercator/` directly

These stores are managed by their CLIs. Browsing them by hand defeats the point
(token cost + non-determinism) and violations surface in review as "you read
`.hopewell/` — please re-do via the CLI."
