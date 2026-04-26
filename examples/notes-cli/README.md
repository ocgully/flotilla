# notes-cli — a Flotilla-on-a-tiny-domain example

This is the original Flotilla starter kit content, preserved as an
example of how a real project consumes Flotilla plugins. It's a trivial
plain-text notes CLI (~230 LOC) wired up with TaskFlow + Pedia + CodeAtlas
+ a slim 6-agent bundle so the *tooling* is the thing you study, not the
business logic.

## What's pre-wired

- `.hopewell/` — TaskFlow work ledger with five historical nodes + two open + one release
- `.pedia/` — Pedia knowledge base with one north-star, one constitution chapter, one spec, one decision, one PRD
- `.mercator/` — CodeAtlas code map of the notes CLI
- `tests/`, `notes/` — the toy domain itself
- `tutorial/` — the original walkthrough

> The on-disk data directories are still named `.hopewell/` and
> `.mercator/` because that's the format the seeded data was written
> in; TaskFlow and CodeAtlas read these legacy paths transparently.

## Use as a Flotilla example

To re-create this from scratch using the new plugin-marketplace model,
in a fresh project:

```bash
flotilla init
flotilla install taskflow pedia codeatlas slim-agents
# then re-run the per-tool init scripts from each tool's docs:
taskflow hooks install --full
taskflow network init
pedia init
codeatlas refresh
```

This directory is preserved so the original tutorial (`tutorial/`) stays
runnable; future Flotilla versions may regenerate it from a recipe.

## See also

- `../../README.md` — top-level Flotilla CLI
- `../../docs/authoring-plugins.md` — author your own plugin
