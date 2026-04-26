# CLAUDE.md — Flotilla

## Project posture

Flotilla is the **plugin marketplace CLI** for AI-native projects. Its
job is to install plugins (each one a git repo or pip package) and
compose their contributions — agents, skills, commands, hooks, MCP
servers — into a consumer project's `.claude/`.

The CLI itself lives under `flotilla/`. The original notes-CLI starter
kit content has been moved to `examples/notes-cli/` and is preserved as
a worked example. Fresh projects bootstrap with
`flotilla init && flotilla install taskflow pedia codeatlas diffsextant slim-agents`.

## Layout

```
flotilla/
├── flotilla/              # the CLI package itself
│   ├── cli.py             # argparse entry — dispatches to commands/
│   ├── commands/          # one module per sub-command
│   ├── manifest.py        # flotilla.yaml parser/validator (both shapes)
│   ├── compose.py         # copy/symlink + settings.json merge
│   ├── resolve.py         # pip + git-clone plugin resolution
│   ├── installed.py       # .flotilla/installed.json read/write
│   ├── registry.py        # Phase 1 curated plugin registry
│   ├── config.py          # .flotilla/config.yaml (link mode etc.)
│   └── paths.py           # ProjectPaths + project-root discovery
├── tests/                 # pytest unit + e2e tests
├── docs/
│   └── authoring-plugins.md
├── examples/
│   └── notes-cli/         # the original starter kit, preserved
└── README.md
```

## Working on the CLI

- All sub-commands take an `argparse.Namespace` and return an int exit
  code. Tests drive them by constructing the Namespace directly — no
  argv re-parsing in tests.
- Manifest parsing falls back to a tiny built-in YAML loader when
  PyYAML is absent; both code paths are tested in `tests/test_manifest.py`.
- Composition is idempotent. Re-running `install` for the same
  plugin/version produces identical on-disk state.
- The `flotilla:managed` sentinel inside `.claude/settings.json` fences
  off plugin contributions. User-authored entries outside the fence are
  preserved across upgrade/uninstall cycles.

## Trust model (Phase 1)

Bare-name installs (`flotilla install taskflow`) only succeed for the
curated registry in `flotilla/registry.py`. Third-party plugins must be
installed with an explicit `--source <url-or-path>`. Legacy names
(`hopewell`, `mercator`, `sextant`) still resolve via the registry's
`aliases:` mechanism. There is no signing yet — `on_install` runs
arbitrary shell. Document any trust-elevating steps clearly in plugin
READMEs.

## Test posture

- Unit tests per sub-command — `tests/test_cmd_<name>.py`.
- Manifest validation tests — `tests/test_manifest.py`.
- End-to-end test installing TaskFlow (via its legacy `hopewell` alias)
  as a real pip plugin — `tests/test_e2e_hopewell.py` (slow, marked
  accordingly; filename retained because it tests alias resolution).

Run the full suite with `python -m pytest`.

## Phase 2 hooks

Already wired but not implemented:

- `flotilla search` — surface a registry index
- `flotilla info` — richer plugin info (README + reviews)
- `requires:` SAT-solving across plugin dependencies
- `.flotilla/resolved.lock` for reproducibility

When picking these up, keep the same architectural posture: small
sub-command modules, tests via Namespace-driven dispatch, no argv
parsing inside the handlers.
