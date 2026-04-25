# Flotilla

**Plugin marketplace for AI-native projects.** Flotilla is a CLI that
installs plugins — each one a git repo or pip package — and composes
their contributions (Claude Code agents, skills, commands, hooks, MCP
servers) into your project's `.claude/` directory.

```bash
pip install flotilla
flotilla init
flotilla install hopewell pedia mercator slim-agents
```

That's it. Your project now has the four canonical Flotilla tools wired
in — work ledger, knowledge base, codemap, and a slim 6-agent bundle —
each pinned to a version, each upgradeable independently with
`flotilla upgrade`, each removable cleanly with `flotilla remove`.

## What is a plugin?

A **Flotilla plugin** is any git repo (or pip package) that contains a
`flotilla.yaml` manifest at the root declaring its contributions:

```yaml
name: hopewell
version: 0.16.0
kind: tool                    # "tool" (pip) or "agent-pack" (git-clone)
python_package:
  name: hopewell
contributes:
  agents:    plugin/agents/   # drop-in .md files for Claude Code
  commands:  plugin/commands/ # /slash-command .md files
  hooks:     plugin/hooks.yaml
  mcp:       plugin/mcp.yaml
on_install:
  - hopewell hooks install --full --quiet
```

Two install models, both supported, manifest-declared per plugin:

- **Tool plugins** (`kind: tool`) — `pip install <package>`, then read
  the `flotilla.yaml` from the installed package and compose. Used by
  Hopewell, Pedia, Mercator. Versioning is whatever pip understands.
- **Agent-pack plugins** (`kind: agent-pack`) — `git clone` into the
  project's `.flotilla/cache/`, check out the requested ref, then
  compose. Used by `slim-agents` and any pure-markdown plugin.

See [`docs/authoring-plugins.md`](docs/authoring-plugins.md) for the
full schema and a worked example.

## CLI

```
flotilla init                    scaffold .flotilla/ in the current project
flotilla install <name> [...]    install one or more plugins
flotilla list                    show installed plugins
flotilla upgrade [<name>]        re-resolve + recompose (defaults to all)
flotilla remove <name>           uninstall (un-compose, optionally pip-uninstall)
flotilla sync                    make on-disk state match .flotilla/manifest.yaml
flotilla validate <repo-path>    check a plugin's flotilla.yaml is valid
flotilla doctor                  diagnose missing files / broken state

flotilla search                  (Phase 2 — deferred)
flotilla info                    (Phase 2 — deferred)
```

## Installing on Windows

Flotilla defaults to **copying** files (not symlinking) on Windows
because reliable symlinks need admin or developer mode. POSIX systems
default to symlinks. You can override either default in
`.flotilla/config.yaml`:

```yaml
link_mode: symlink   # or "copy" or "auto" (the default — picks per-OS)
```

The cost of copy-mode is that `flotilla upgrade` has to re-walk every
contributed file. The benefit is no permission elevation, no surprises.

## Phase 1 trust model

`flotilla install <name>` only resolves names against a **curated
registry** in this release: `hopewell`, `pedia`, `mercator`,
`slim-agents`. Any other name fails with a friendly error pointing at
`--source <url-or-path>` for explicit third-party installs.

Phase 2 will add a published index (`flotilla search`), a richer info
surface (`flotilla info`), and a signed-manifest story for plugins
distributed by parties other than the curator. Phase 1 is deliberately
narrow so the install surface stays auditable.

**Be cautious with `--source`.** A plugin's `on_install` steps run
arbitrary shell commands as you. Until signed plugins ship in Phase 3,
treat third-party plugin manifests like a `curl | bash` — read them
first, especially the `on_install` block.

## Layout in a consuming project

```
my-project/
├── .flotilla/
│   ├── manifest.yaml        # which plugins this project wants
│   ├── config.yaml          # how to compose them (link mode, cache dir)
│   ├── installed.json       # what's currently installed (machine-managed)
│   └── cache/               # agent-pack plugins cloned here
├── .claude/
│   ├── agents/              # contributed by various plugins
│   ├── commands/
│   ├── skills/
│   └── settings.json        # hooks + MCP merged from plugins (fenced under flotilla:managed)
└── ...
```

Anything you put in `.claude/` that Flotilla didn't place is preserved.
The `flotilla:managed` sentinel inside `settings.json` fences off the
plugin contributions so a manual edit to a hook outside the fence
survives upgrades.

## Examples

The `examples/` directory contains a fully wired sample project:

- [`examples/notes-cli/`](examples/notes-cli/) — the original Flotilla
  starter kit (a tiny notes CLI + Hopewell + Pedia + Mercator + the
  slim-agent bundle). Useful as a reference layout when authoring your
  own plugin or wiring up a new project.

## Design background

The full design rationale (manifest schema, composition strategy,
Windows trade-offs, security posture, deferred items) lives in
[`patterns/drafts/flotilla-plugin-design.md` in AgentFactory](https://github.com/ocgully/AgentFactory/blob/main/patterns/drafts/flotilla-plugin-design.md).
That draft is the long-form version of this README.

## Links

- [Hopewell](https://github.com/ocgully/Hopewell) — work ledger
- [Pedia](https://github.com/ocgully/pedia) — knowledge base
- [Mercator](https://github.com/ocgully/mercator) — codemap
- [flotilla-slim-agents](https://github.com/ocgully/flotilla-slim-agents) — bare-bones AIDLC roster
