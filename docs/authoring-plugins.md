# Authoring a Flotilla plugin

A Flotilla plugin is any directory (in a git repo or inside a pip
package) that contains a `flotilla.yaml` manifest at its root. This
guide is the schema reference + a worked example.

## Manifest schema

```yaml
# Required.
name: my-plugin                    # [a-z][a-z0-9_-]* — the install name
version: "0.1.0"                   # any string; pip-style for tool plugins

# Optional metadata (shown in `flotilla info`, `flotilla list`).
description: "What this plugin does in one line"
homepage: "https://github.com/you/my-plugin"
license: "Apache-2.0"
tags:
  - example

# Required.
kind: tool                         # "tool" (pip-installed) or "agent-pack" (git-clone)

# Required for kind: tool — the pip package name and any extras.
python_package:
  name: my-plugin                  # what `pip install` will resolve
  extras:
    - cli
    - web

# What this plugin contributes to the consumer's .claude/.
# Each path is relative to the manifest root (the directory containing
# this flotilla.yaml). Omit any field your plugin doesn't contribute.
contributes:
  agents:    plugin/agents/        # *.md files copied to .claude/agents/
  skills:    plugin/skills/        # *.md files copied to .claude/skills/
  commands:  plugin/commands/      # *.md files copied to .claude/commands/
  hooks:     plugin/hooks.yaml     # YAML merged into .claude/settings.json
  mcp:       plugin/mcp.yaml       # YAML merged into .claude/settings.json

# Shell commands run once on install. Best-effort — failure does not
# abort the install. Used for hooks-install, store init, etc.
on_install:
  - my-plugin init --quiet
  - my-plugin hooks install --quiet

# Shell commands run when `flotilla remove` is invoked. Symmetric to
# on_install. Best-effort.
on_uninstall:
  - my-plugin hooks uninstall --quiet

# Cross-plugin requirements. Soft hints today; SAT-solving deferred to
# Phase 2.
requires:
  - taskflow >= 0.17.0
```

## Where the plugin lives on disk

Two layouts, depending on `kind`:

### `kind: tool` (pip-installed)

Your repo:

```
my-plugin/                         # the repo
├── flotilla.yaml                  # the manifest (REQUIRED at the root)
├── pyproject.toml                 # standard Python packaging
├── my_plugin/                     # the Python package
│   ├── __init__.py
│   └── cli.py
└── plugin/
    ├── agents/
    │   └── my-agent.md
    ├── commands/
    │   └── my-cmd.md
    └── hooks.yaml
```

When a consumer runs `flotilla install my-plugin`, the resolver:

1. `pip install my-plugin` (or via the manifest's `python_package.name`)
2. Imports the package and locates the `flotilla.yaml` either *inside*
   the package directory, or *one level up* (the repo root, for
   editable installs). Either layout works.
3. Composes the contributions referenced in `contributes:`.

If you want to ship `flotilla.yaml` inside the wheel for non-editable
installs, place a copy at `my_plugin/flotilla.yaml` and adjust the
`contributes:` paths to be relative to that copy (e.g. `agents/` inside
`my_plugin/plugin/agents/`). The convention used by the curated
plugins is to keep one copy at the repo root.

### `kind: agent-pack` (git-clone)

Your repo:

```
my-pack/                           # the repo
├── flotilla.yaml                  # the manifest
└── plugin/
    └── agents/
        └── one-agent.md
```

No Python, no packaging. When a consumer runs
`flotilla install my-pack --source github.com/you/my-pack`, the
resolver clones the repo into `.flotilla/cache/my-pack/` and composes.

## Worked example: a minimal pure-agents plugin

```
my-pack/
├── flotilla.yaml
└── plugin/
    └── agents/
        └── reviewer.md
```

```yaml
# my-pack/flotilla.yaml
name: my-pack
version: "0.1.0"
description: "A single-agent code reviewer pack"
kind: agent-pack
contributes:
  agents: plugin/agents/
```

```markdown
<!-- my-pack/plugin/agents/reviewer.md -->
# Reviewer

You are the Reviewer for this project. Read the diff, surface concerns
about correctness, security, and clarity, then route to the appropriate
specialist.
```

A consumer wires it in:

```bash
flotilla install my-pack --source github.com/you/my-pack
# or, for local development:
flotilla install my-pack --source /path/to/my-pack
```

After install, `.claude/agents/reviewer.md` is in place and Claude Code
will pick it up.

## Validating a plugin

Run `flotilla validate <path-to-repo>` to check that:

- `flotilla.yaml` parses
- `name`, `version`, `kind` are present and valid
- Each path under `contributes:` resolves to an existing file/directory
- The `plugin/` directory exists

The validator is the same code path Flotilla uses internally on install,
so a passing `validate` is a strong signal the install will work.

## Versioning + upgrades

For tool plugins, version selection rides on top of pip:

- `version: "0.16.0"` — exact pin
- `version: "^0.16"` — at least 0.16, less than 0.17 (caret semantics)
- `version: "*"` — latest available

For agent-pack plugins, the version is interpreted as a git ref (tag,
branch, or SHA). The default `*` clones the default branch.

`flotilla upgrade` re-resolves the plugin (re-pip, re-fetch + re-checkout)
and recomposes. The on-disk record at `.flotilla/installed.json` tracks
exactly which files were placed, so the upgrade can swap them cleanly.

## Hooks + MCP merging

`hooks.yaml` and `mcp.yaml` are merged into the consumer's
`.claude/settings.json` under a `flotilla:managed` sentinel block keyed
by plugin name. Live keys (the ones Claude Code reads) get the union of
all managed contributions plus user-authored content. On uninstall, the
managed block for that plugin is stripped and the live keys are
recomputed — user content is preserved across the cycle.

```json
{
  "theme": "dark",                          // user-authored — preserved
  "hooks": {
    "PreToolUse": [
      { "matcher": "user-rule" },           // user-authored — preserved
      { "matcher": "taskflow-rule" }        // contributed by taskflow plugin
    ]
  },
  "flotilla:managed": {
    "taskflow": {
      "hooks": {
        "PreToolUse": [{ "matcher": "taskflow-rule" }]
      }
    }
  }
}
```

If two plugins contribute different matchers for the same key, both
land in the live array — Claude Code reads matchers as a list, so this
is the intended behaviour. There's no automatic conflict resolution in
Phase 1; if your plugin needs an exclusive matcher, document that in
your README.

## Things to know

- **`on_install` / `on_uninstall` run arbitrary shell.** They run as
  the user. Keep them small + idempotent + best-effort. Anything load-
  bearing should also be runnable as a manual command and documented in
  your plugin README.
- **No private state.** Don't write outside the consumer's
  `.flotilla/cache/` (for agent-packs) or your pip package's data dirs
  (for tool plugins). Composition writes only inside the consumer's
  `.claude/` and `.flotilla/`.
- **Be a good citizen with names.** Agents are looked up by filename in
  `.claude/agents/`; if your plugin contributes `architect.md`, it will
  collide with another plugin's `architect.md`. Prefix with your plugin
  name (`taskflow-scribe.md`, `pedia-keeper.md`) unless you intend to
  override.

## Phase 2 hints (heads-up only)

- Signed manifests for third-party plugins
- A `flotilla search` index over a curated registry
- A lock file (`.flotilla/resolved.lock`) for reproducibility
- SAT-style `requires:` resolution

If your plugin already declares `requires:` today, the manifest is
forward-compatible — Flotilla just doesn't yet do anything with it.
