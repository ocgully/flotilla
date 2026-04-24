# CLAUDE.md — agentfactory-showcase

## Project stance

This repository is a **showcase**. The notes CLI domain is deliberately
trivial (~230 LOC, stdlib-only); everything interesting is the ecosystem
setup around it.

If you're an agent landing here, your job is to **demonstrate the loops**,
not to build a production product. The tooling is the product.

## Where things live

| What | Path | How to read it |
|------|------|---------------|
| Work ledger | `.hopewell/` | **CLI only** — `hopewell list`, `hopewell show`, `hopewell query ...`. NEVER read files here directly. |
| Knowledge base | `.pedia/` | **CLI only** — `pedia query "..."`, `pedia show --for HW-NNNN`, `pedia trace <block>`. |
| Code map | `.mercator/` | **CLI only** — `mercator query systems`, `mercator query touches <path>`, `mercator query contract <sys>`. |
| Agent roster | `.claude/agents/` | Composed from AgentFactory core via `bash ../AgentFactory/scripts/build-bundle.sh`. |
| Portable aliases | [`AGENTS.md`](AGENTS.md) | Read by Codex and OpenCode. |

## Agent roster (source: AgentFactory/marketplaces/core)

Consult `.claude/agents/` for the full set. The usual suspects:

- `@vision-keeper` — product vision + north-star
- `@architect` — decomposition + design
- `@planner` — SpecKit authoring
- `@orchestrator` — route dispatch + gate management
- `@testing-qa` — test discipline
- `@release-engineer` — gitflow + release cutting
- `@technical-writer` — user-facing docs
- `@documentary` — progress narrative (internal)
- `@mercator-keeper` — keeps the code map honest

## Hook-driven invariants

Once `scripts/bootstrap.sh` runs, the following are **enforced automatically**:

- **commit-msg** — every commit references `HW-NNNN` (or is a merge/fixup)
- **pre-commit** — spec drift blocks the commit; resolve via `hopewell reconcile`
- **post-commit** — Mercator + Pedia incremental refresh; Hopewell event recorded
- **pre-push** — release-score gate on release branches

Do **not** pass `--no-verify` unless an invariant is broken and you're fixing
it. If a hook blocks you, surface the message — don't bypass it.

## Query flows (how an agent starts a task)

```bash
# "What am I working on?"
hopewell resume

# "What's ready for me to pick up?"
hopewell ready

# "What does HW-0006 entail?"
hopewell show HW-0006
pedia show --for HW-0006         # specs + decisions + PRDs cited by this node

# "Where does `store` live?"
mercator query touches notes/store.py
mercator query contract notes    # public surface

# "What are we trying to build?"
pedia query "small fast notes"
```

## Multi-tool notes

- Codex and OpenCode read `AGENTS.md` and the same three CLIs. The protocols
  below are portable: any agent harness that can exec a shell can participate.
- Claude Code hook integration lives in `~/.claude/settings.json` (user scope)
  wired by `hopewell hooks install --full --claude-code`.
- See [`docs/multi-tool.md`](docs/multi-tool.md) for side-by-side commands.

## Session resume protocol

1. **Session start** — `hopewell resume`
2. **Mid-work pause** — `hopewell checkpoint HW-NNNN --note "..."`
3. **Session end** — include `fixes HW-NNNN` in commit message, or
   `hopewell close HW-NNNN --commit <sha> --reason "..."`.

## Hopewell — do not read `.hopewell/` directly

`.hopewell/` holds the work graph (tickets, edges, events, attestations).
Agents must NOT read files in that directory during research. Use the
`hopewell query <...>` CLI (or the `hopewell` Python library) for any
lookup. Tree-browsing `.hopewell/` defeats the point of the tool (tokens
+ non-determinism). Violations surface in reviews as "you read
.hopewell/ — please re-do via the CLI."
